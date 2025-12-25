# vib_spectrum.py
import os
import json
import time
import hashlib
import numpy as np
from scipy.fft import rfft, rfftfreq
from ase import units

# ============================================================
# Utility functions
# ============================================================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def thz_to_cm1(freq_thz):
    return freq_thz * 33.35641

def remove_COM(vels):
    """
    Input: (T, N, 3)
    Remove instantaneous per-step COM velocity (mass-unweighted).
    """
    return vels - vels.mean(axis=1, keepdims=True)

def structure_hash(symbols, positions, cell):
    h = hashlib.sha256()
    h.update(np.asarray(symbols, dtype=object).tobytes())
    h.update(np.asarray(positions, float).tobytes())
    if cell is not None:
        h.update(np.asarray(cell, float).tobytes())
    return h.hexdigest()[:16]

def cut_spectrum(freqs, spec, fmax):
    idx = freqs <= fmax
    return freqs[idx], spec[idx]

# ============================================================
# Core VAF computation
# ============================================================

def compute_vaf_total(vels, max_lag):
    T, N, _ = vels.shape
    vaf = np.zeros(max_lag)
    maxlag = min(max_lag, T - 1)

    for lag in range(maxlag):
        dot = (vels[:T - lag] * vels[lag:]).sum(axis=2)
        vaf[lag] = dot.mean()

    return vaf

def compute_vaf_per_atom(vels, max_lag):
    T, N, _ = vels.shape
    vaf_atom = np.zeros((max_lag, N))
    maxlag = min(max_lag, T - 1)

    for lag in range(maxlag):
        dot = (vels[:T - lag] * vels[lag:]).sum(axis=2)
        vaf_atom[lag] = dot.mean(axis=0)

    return vaf_atom

def vaf_fft(vaf, timestep_fs):
    dt_seconds = timestep_fs * 1e-15
    freqs_hz = rfftfreq(len(vaf), dt_seconds)
    freqs_cm1 = thz_to_cm1(freqs_hz * 1e-12)

    spec = np.abs(rfft(vaf))
    if spec.max() > 0:
        spec /= spec.max()

    return freqs_cm1, spec

def vaf_fft_per_atom(vaf_atoms, timestep_fs):
    T, N = vaf_atoms.shape
    dt_seconds = timestep_fs * 1e-15
    freqs_hz = rfftfreq(T, dt_seconds)
    freqs_cm1 = thz_to_cm1(freqs_hz * 1e-12)

    spec = np.abs(rfft(vaf_atoms, axis=0))
    for i in range(N):
        if spec[:, i].max() > 0:
            spec[:, i] /= spec[:, i].max()

    return freqs_cm1, spec

def vaf_fft_per_element(symbols, spec_atom):
    unique = sorted(set(symbols))
    out = {}

    for el in unique:
        idx = [i for i, s in enumerate(symbols) if s == el]
        out[el] = spec_atom[:, idx].mean(axis=1)

    return out

# ============================================================
# Main interface used by GA
# ============================================================

def compute_vib_spectrum(
    velocities,
    masses,
    symbols,
    positions,
    cell,
    dt_fs,
    output_path,
    max_lag:int=None,
    freq_cutoff_cm1=3200.0,
    mode="total",       # total | atom | element | all
    remove_com=True,
    mass_weighting=True 
):
    """
    Compute vibrational spectrum exactly like the standalone script.
    Saves everything under:

        <output_path>/struct_<hash>/

    Returns:
        {
            "data": ...,
            "hash": <hash>,
            "folder": <folder>
        }
    """

    # ------------------------------------------------------------------
    # Prepare unique folder per structure
    # ------------------------------------------------------------------
    h = structure_hash(symbols, positions, cell)

    base_dir = output_path or "."

    folder_name = f"vib_struct_{h}"
    folder = os.path.join(base_dir, folder_name)
    ensure_dir(folder)

    # ------------------------------------------------------------------
    # Prepare velocities
    # ------------------------------------------------------------------
    vels = np.asarray(velocities, dtype=float)  # shape (T,N,3)

    # 1. Remove Drift (Center of Mass motion)
    # Important: Do this on raw velocities before weighting
    if remove_com:
        vels = remove_COM(vels)

    # ------------------------------------------------------------------
    # 2. Mass Weighting (Apply sqrt(mass) scaling)
    # ------------------------------------------------------------------
    if mass_weighting:
        m_arr = np.asarray(masses, dtype=float)
        # Check shapes
        if m_arr.shape[0] != vels.shape[1]:
             raise ValueError(f"Masses shape {m_arr.shape} mismatch with atoms N={vels.shape[1]}")

        # Scale velocities: v' = v * sqrt(m)
        # Broadcasting: (T, N, 3) * (1, N, 1)
        sqrt_m = np.sqrt(m_arr)
        vels = vels * sqrt_m[None, :, None]

    T, N, _ = vels.shape

    # If max_lag is None, use full trajectory range
    if max_lag is None:
        max_lag = T - 1

    # ------------------------------------------------------------------
    # TOTAL VAF
    # ------------------------------------------------------------------
    vaf_total = compute_vaf_total(vels, max_lag)
    freq_total, spec_total = vaf_fft(vaf_total, dt_fs)
    freq_total, spec_total = cut_spectrum(freq_total, spec_total, freq_cutoff_cm1)

    np.savetxt(os.path.join(folder, "vaf_total.txt"), vaf_total)
    np.savetxt(os.path.join(folder, "spectrum_total.txt"),
               np.column_stack([freq_total, spec_total]))

    # ------------------------------------------------------------------
    # PER-ATOM VAF
    # ------------------------------------------------------------------
    vaf_atom = compute_vaf_per_atom(vels, max_lag)
    freq_atom, spec_atom = vaf_fft_per_atom(vaf_atom, dt_fs)
    idx = freq_atom <= freq_cutoff_cm1
    freq_atom = freq_atom[idx]
    spec_atom = spec_atom[idx]

    np.save(os.path.join(folder, "vaf_atom.npy"), vaf_atom)
    np.save(os.path.join(folder, "freq_atom.npy"), freq_atom)
    np.save(os.path.join(folder, "spec_atom.npy"), spec_atom)

    # ------------------------------------------------------------------
    # PER-ELEMENT VAF
    # ------------------------------------------------------------------
    spec_element = vaf_fft_per_element(symbols, spec_atom)
    spec_element_cut = {}

    for el, spec in spec_element.items():
        fcut, scut = cut_spectrum(freq_atom, spec, freq_cutoff_cm1)
        spec_element_cut[el] = scut.tolist()
        np.savetxt(
            os.path.join(folder, f"element_{el}.txt"),
            np.column_stack([fcut, scut])
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    meta = dict(
        hash=h,
        n_atoms=N,
        max_lag=max_lag,
        freq_cutoff_cm1=freq_cutoff_cm1,
        mode=mode,
        dt_fs=dt_fs,
    )
    with open(os.path.join(folder, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=4)

    # ------------------------------------------------------------------
    # Return dictionary for GA
    # ------------------------------------------------------------------
    data = {
        "freq_total": freq_total.tolist(),
        "spec_total": spec_total.tolist(),
        "freq_atom": freq_atom.tolist(),
        "spec_atom": spec_atom.tolist(),
        "spec_element": spec_element_cut,
    }

    return dict(data=data, hash=h, folder=folder)
