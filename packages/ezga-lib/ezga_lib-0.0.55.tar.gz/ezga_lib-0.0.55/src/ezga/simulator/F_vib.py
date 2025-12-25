import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import matplotlib.pyplot as plt
import os, json, uuid
from datetime import datetime

# ============================================================
# sanitize and SAVE vib
# ============================================================
def _sanitize_tag(tag: str) -> str:
    """Make a safe tag for filenames (letters, digits, -, _, .)."""
    safe = []
    for ch in str(tag):
        if ch.isalnum() or ch in "-_.":
            safe.append(ch)
        else:
            safe.append("_")
    return "".join(safe).strip("._") or "run"

def _gen_run_tag(user_tag: Optional[str] = None) -> str:
    """User tag if provided, else UTC timestamp + short uuid."""
    if user_tag:
        return _sanitize_tag(user_tag)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    rid = uuid.uuid4().hex[:6]
    return f"{ts}-{rid}"

def _bump_path(path: str) -> str:
    """If path exists, append -1, -2, ... before extension until free."""
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    k = 1
    cand = f"{root}-{k}{ext}"
    while os.path.exists(cand):
        k += 1
        cand = f"{root}-{k}{ext}"
    return cand

def _extract_scalar_vib_fields(corrections: Dict[str, Any]) -> Dict[str, float]:
    preferred = [
        "F_vib_eV", "U_vib_eV", "E_ZP_eV", "S_vib_eV_perK",
        "F_vib_eV_classical", "U_vib_eV_classical", "E_ZP_eV_classical", "S_vib_eV_perK_classical",
        "T_K", "dof_count", "F"
    ]
    out = {}
    for k in preferred:
        v = corrections.get(k, None)
        if np.isscalar(v) and np.isfinite(v):
            out[k] = float(v)
    return out

def _save_vib_outputs_to_folder(
    corrections: Dict[str, Any],
    output_path: str,
    run_tag: Optional[str] = None
) -> Dict[str, str]:
    """
    Save vib results next to output_path with a unique run tag.
    Creates:
      BASE.{run_tag}.vib.json
      BASE.{run_tag}.vdos.npz
      BASE.{run_tag}.vdos.csv
    Returns dict with written paths.
    """
    saved: Dict[str, str] = {}
    out_dir = output_path or "."
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(output_path))[0] or "MD_out"

    tag = _gen_run_tag(run_tag)
    stem = f"{base}.{tag}"

    # JSON scalars
    scalars = _extract_scalar_vib_fields(corrections)
    if scalars:
        scalars["created_utc"] = datetime.utcnow().isoformat() + "Z"
        scalars["run_tag"] = tag
        jpath = _bump_path(os.path.join(out_dir, f"{stem}.vib.json"))
        try:
            with open(jpath, "w", encoding="utf-8") as f:
                json.dump(scalars, f, indent=2)
            saved["json"] = jpath
        except Exception:
            pass

    # Arrays (VDOS)
    if "freqs_THz" in corrections and "dos_mode" in corrections:
        npz_path = _bump_path(os.path.join(out_dir, f"{stem}.vdos.npz"))
        csv_path = _bump_path(os.path.join(out_dir, f"{stem}.vdos.csv"))
        try:
            np.savez_compressed(
                npz_path,
                freqs_THz=np.asarray(corrections["freqs_THz"]),
                dos_mode=np.asarray(corrections["dos_mode"]),
                dos_std=np.asarray(corrections.get("dos_std", np.zeros_like(corrections["dos_mode"]))),
            )
            saved["npz"] = npz_path
        except Exception:
            pass
        try:
            freqs = np.asarray(corrections["freqs_THz"]).reshape(-1)
            dos = np.asarray(corrections["dos_mode"]).reshape(-1)
            std = np.asarray(corrections.get("dos_std", np.zeros_like(dos))).reshape(-1)
            arr = np.column_stack([freqs, dos, std])
            np.savetxt(
                csv_path,
                arr,
                delimiter=",",
                header="freqs_THz,dos_mode,dos_std",
                comments="",
                fmt="%.12g",  
            )
            saved["csv"] = csv_path
        except Exception:
            pass

    return saved

# ============================================================
# Velocity sampler (downsample) with optional COM removal
# ============================================================
class _VibSampler:
    """
    Downsampled velocity recorder with optional per-step center-of-mass removal.

    This sampler stores float32 to save memory and returns an array of shape
    (n_samples, 3N) after `finalize()`.

    Parameters
    ----------
    atoms : ase.Atoms-like
        Object providing `get_velocities()` and `get_masses()`.
    n_samples_pred : int
        Expected number of stored samples (preallocates the buffer).
    store_interval : int
        MD steps between stored samples; >= 1.
    remove_com : bool, optional
        If True, remove the instantaneous COM velocity at each sampling step.
    mass_weighted : bool, optional
        If True, COM is computed mass-weighted. If False, it's a simple mean.

    Notes
    -----
    - Call `attach(dyn)` on your ASE dynamics to record periodically.
    - Call `finalize()` at the end to retrieve the (m, 3N) array.
    """

    def __init__(self, atoms, n_samples_pred: int, store_interval: int,
                 remove_com: bool = True, mass_weighted: bool = True):
        self.atoms = atoms
        self.n_samples = int(n_samples_pred)
        self.store_interval = int(max(store_interval, 1))
        self.remove_com = bool(remove_com)
        self.mass_weighted = bool(mass_weighted)
        self.buf = np.empty((self.n_samples, 3*len(atoms)), dtype=np.float32)
        self.i = 0
        if self.remove_com:
            self.masses = atoms.get_masses()
            self.M = float(self.masses.sum()) if self.mass_weighted else float(len(self.masses))

    def __call__(self):
        """Sampling hook: stores one frame when triggered by the dynamics."""
        if self.i >= self.n_samples:
            return
        v = self.atoms.get_velocities()   # (N, 3)
        if self.remove_com:
            if self.mass_weighted:
                vcm = (self.masses[:, None] * v).sum(axis=0, dtype=np.float64) / self.M
            else:
                vcm = v.mean(axis=0)
            v = v - vcm
        self.buf[self.i, :] = v.reshape(-1).astype(np.float32, copy=False)
        self.i += 1

    def attach(self, dyn):
        """Attach this sampler to an ASE dynamics object."""
        dyn.attach(self, interval=self.store_interval)

    def finalize(self) -> np.ndarray:
        """Return the recorded velocities as an array of shape (m, 3N)."""
        return self.buf[:self.i, :]

    def get_velocity_series(self) -> np.ndarray:
        """
        Return velocities in (m, N, 3) format for VAF/spectrum processing.
        The internal buffer is stored as (m, 3N), so we reshape it here.
        """
        data = self.buf[:self.i, :]  # (m, 3N)
        m, flat = data.shape
        if flat % 3 != 0:
            raise ValueError(
                f"Cannot reshape velocity array of shape {data.shape} into (m, N, 3)."
            )
        N = flat // 3
        return data.reshape(m, N, 3)


# ============================================================
# Plotting helpers (optional; for analysis/diagnostics)
# ============================================================
def plot_vdos(freqs_THz: np.ndarray,
              dos_mode: np.ndarray,
              dos_std: Optional[np.ndarray] = None,
              title: str = "VDOS (per mode)") -> None:
    """
    Plot the per-mode VDOS with optional ±1σ band.

    Parameters
    ----------
    freqs_THz : (nf,) ndarray
        Frequency grid in THz.
    dos_mode : (nf,) ndarray
        Area-normalized per-mode DOS.
    dos_std : (nf,) ndarray, optional
        Standard deviation across Welch segments.
    title : str
        Figure title.
    """
    plt.figure()
    plt.plot(freqs_THz, dos_mode, label="DOS")
    if dos_std is not None:
        hi = dos_mode + dos_std
        lo = np.maximum(dos_mode - dos_std, 0.0)
        plt.fill_between(freqs_THz, lo, hi, alpha=0.25, label="±1σ")
    plt.xlabel("Frequency (THz)")
    plt.ylabel("Per-mode DOS (area = 1)")
    plt.title(title)
    plt.legend()
    plt.tight_layout()


def plot_vdos_with_debye(freqs_THz: np.ndarray,
                         dos_mode: np.ndarray,
                         fmax_fit: float = 1.5,
                         title: str = "VDOS + Debye f^2") -> None:
    """
    Plot the VDOS and overlay a crude Debye ~ c f^2 fit at low frequency.

    Parameters
    ----------
    freqs_THz : (nf,) ndarray
        Frequency grid in THz.
    dos_mode : (nf,) ndarray
        Area-normalized per-mode DOS.
    fmax_fit : float
        Upper frequency (THz) used for the c f^2 least-squares fit.
    title : str
        Figure title.
    """
    plt.figure()
    plt.plot(freqs_THz, dos_mode, label="DOS")
    mask = (freqs_THz > 0) & (freqs_THz <= fmax_fit)
    if mask.sum() >= 3:
        f = freqs_THz[mask]
        g = dos_mode[mask]
        c = (f*f @ g) / max((f*f @ f*f), 1e-30)
        f_line = np.linspace(0, fmax_fit, 200)
        plt.plot(f_line, c*f_line**2, "--", label="Debye ~ c f²")
    plt.xlabel("Frequency (THz)")
    plt.ylabel("Per-mode DOS")
    plt.title(title)
    plt.legend()
    plt.tight_layout()


def plot_thermo_bars(res: Dict[str, float],
                     n_atoms: Optional[int] = None,
                     classical: bool = True,
                     title: str = "Vibrational thermodynamics") -> None:
    """
    Bar plot comparing quantum vs classical vibrational quantities.

    Parameters
    ----------
    res : dict
        Dictionary containing keys like "E_ZP_eV", "U_vib_eV", "S_vib_eV_perK", "F_vib_eV",
        and their classical counterparts.
    n_atoms : int, optional
        If given, energies are shown per atom (entropy stays per system).
    classical : bool
        If True, plot classical bars next to quantum.
    title : str
        Figure title.
    """
    keys_q = ["E_ZP_eV", "U_vib_eV", "S_vib_eV_perK", "F_vib_eV"]
    vals_q = [res.get(k, np.nan) for k in keys_q]
    labels = ["ZPE", "U", "S (eV/K)", "F"]

    if n_atoms:
        vals_q = [vals_q[0]/n_atoms, vals_q[1]/n_atoms, vals_q[2], vals_q[3]/n_atoms]
        labels = ["ZPE/atom", "U/atom", "S (eV/K)", "F/atom"]

    x = np.arange(len(labels))
    plt.figure()
    plt.bar(x - 0.15, vals_q, width=0.3, label="Quantum")

    if classical:
        keys_c = ["E_ZP_eV_classical", "U_vib_eV_classical",
                  "S_vib_eV_perK_classical", "F_vib_eV_classical"]
        vals_c = [res.get(k, np.nan) for k in keys_c]
        if n_atoms:
            vals_c = [0.0, vals_c[1]/n_atoms, vals_c[2], vals_c[3]/n_atoms]
        plt.bar(x + 0.15, vals_c, width=0.3, label="Classical")

    plt.xticks(x, labels)
    plt.ylabel("eV  (S shown in eV/K)")
    plt.title(title)
    plt.legend()
    plt.tight_layout()


def plot_cumulative(res: Dict[str, np.ndarray],
                    which: str = "ZPE",
                    title: Optional[str] = None) -> None:
    """
    Plot cumulative integral of ZPE or U over the VDOS.

    Parameters
    ----------
    res : dict
        Must contain "freqs_THz" and "dos_mode".
    which : {"ZPE", "U"}
        Select cumulative quantity to plot.
    title : str, optional
        Figure title. Defaults to a descriptive title.
    """
    f = res["freqs_THz"]
    g = res["dos_mode"]
    hbar_eV = 6.582119569e-16
    omega = 2 * np.pi * f * 1e12

    if which.lower() == "zpe":
        integrand = 0.5 * hbar_eV * omega
        ylabel = "ZPE cumulative (eV per mode)"
    elif which.lower() == "u":
        T = res.get("T_K", None)
        if T is None:
            raise ValueError("T_K missing in results; cannot plot U cumulative.")
        kB_eV = 8.617333262e-5
        beta = 1.0 / (kB_eV * T)
        x = 0.5 * beta * hbar_eV * omega
        # U_mode = 1/2 ħω coth(βħω/2)
        integrand = 0.5 * hbar_eV * omega * (np.cosh(x) / (np.sinh(x) + 1e-300))
        ylabel = f"U cumulative @ {T:.1f} K (eV per mode)"
    else:
        raise ValueError("which must be 'ZPE' or 'U'")

    # cumulative trapezoidal integral
    cum = np.cumsum(0.5 * (g[:-1] * integrand[:-1] + g[1:] * integrand[1:]) * (f[1:] - f[:-1]))
    plt.figure()
    plt.plot(f[1:], cum)
    plt.xlabel("Frequency (THz)")
    plt.ylabel(ylabel)
    plt.title(title or ylabel)
    plt.tight_layout()

# ============================================================
# Utilities
# ============================================================
def _next_pow2(n: int) -> int:
    """Return the next power-of-two >= n."""
    #return 1 << (int(2*n - 1).bit_length())
    return 1 << (max(0, n-1).bit_length())


def _trapz_area(x: np.ndarray, y: np.ndarray) -> float:
    """Trapezoidal area under y(x)."""
    return float(np.trapz(y, x)) if x.size > 1 else 0.0


def _area_normalize(x: np.ndarray, y: np.ndarray, eps: float = 1e-30) -> np.ndarray:
    """
    Normalize y so that ∫ y dx = 1.

    If the area is <= eps, y is returned unchanged.
    """
    area = _trapz_area(x, y)
    return y if area <= eps else (y / area)


def _as_structured(vel_flat: np.ndarray) -> np.ndarray:
    """
    Reshape a (m, 3N) array to (m, N, 3).
    """
    m, d = vel_flat.shape
    if d % 3 != 0:
        raise ValueError("vel_flat must have 3N columns.")
    return vel_flat.reshape(m, d // 3, 3)


def _as_flat(vel_struct: np.ndarray) -> np.ndarray:
    """
    Reshape a (m, N, 3) array to (m, 3N).
    """
    m, N, c = vel_struct.shape
    if c != 3:
        raise ValueError("last dim must be 3.")
    return vel_struct.reshape(m, 3*N)


def remove_com_drift(vel_flat: np.ndarray, masses: np.ndarray) -> np.ndarray:
    """
    Remove instantaneous center-of-mass (COM) velocity frame by frame.

    Parameters
    ----------
    vel_flat : (m, 3N) ndarray
        Velocity time series.
    masses : (N,) ndarray
        Atomic masses.

    Returns
    -------
    (m, 3N) ndarray
        Velocities with COM drift removed.
    """
    v = _as_structured(vel_flat)                # (m, N, 3)
    m = masses.reshape(1, -1, 1)                # (1, N, 1)
    M = float(masses.sum())
    if M <= 0:
        raise ValueError("Masses must be positive.")
    v_com = (v * m).sum(axis=1, keepdims=True) / M
    return _as_flat(v - v_com)


def _apply_notch_suppression(freqs_THz: np.ndarray,
                             y: np.ndarray,
                             bands_THz: Optional[List[Tuple[float, float]]]) -> np.ndarray:
    """
    Suppress narrow frequency bands (e.g., thermostat lines) by linear interpolation.

    Parameters
    ----------
    freqs_THz : (nf,) ndarray
        Frequency grid (THz).
    y : (nf,) ndarray
        Signal to correct (e.g., mean VDOS).
    bands_THz : list of (f0, width) or None
        For each band, suppress [f0 - width/2, f0 + width/2].

    Returns
    -------
    (nf,) ndarray
        Corrected signal.
    """
    if not bands_THz:
        return y
    y = y.copy()
    for f0, w in bands_THz:
        fL, fR = f0 - 0.5*w, f0 + 0.5*w
        mask = (freqs_THz >= fL) & (freqs_THz <= fR)
        if not np.any(mask):
            continue
        iL = np.searchsorted(freqs_THz, fL, side="left")
        iR = np.searchsorted(freqs_THz, fR, side="right") - 1
        iL = max(0, min(iL, len(freqs_THz)-1))
        iR = max(0, min(iR, len(freqs_THz)-1))
        if iR <= iL:
            continue
        y_band = np.interp(freqs_THz[mask],
                           [freqs_THz[iL], freqs_THz[iR]],
                           [y[iL], y[iR]])
        y[mask] = y_band
    return y


def _debye_blend(freqs_THz: np.ndarray,
                 dos: np.ndarray,
                 fit_fmax_THz: float,
                 blend_fmax_THz: float) -> np.ndarray:
    """
    Fit g(f) = c f^2 on [0, fit_fmax] and smoothly blend into the measured VDOS up to
    `blend_fmax`. The area is renormalized afterwards.

    Notes
    -----
    Use only for crystalline solids. Disable for liquids or glasses.
    """
    if freqs_THz.size < 3 or blend_fmax_THz <= 0:
        return dos
    mask_fit = (freqs_THz > 0) & (freqs_THz <= fit_fmax_THz)
    if np.count_nonzero(mask_fit) < 3:
        return dos
    f = freqs_THz[mask_fit]
    g = dos[mask_fit]
    c = float((f*f @ g) / max((f*f @ f*f), 1e-30))
    y = dos.copy()
    mask_blend = (freqs_THz >= 0) & (freqs_THz <= blend_fmax_THz)
    if np.any(mask_blend):
        fb = freqs_THz[mask_blend]
        w = np.clip(fb / max(blend_fmax_THz, 1e-30), 0.0, 1.0)
        y[mask_blend] = (1.0 - w) * (c * fb**2) + w * y[mask_blend]
    return _area_normalize(freqs_THz, y)

# -----------------------------
# FAST Welch classical kernels
# -----------------------------


# ============================================================
# VDOS by Welch (fast, memory-lean) with optional parallelism
# ============================================================
def vdos_psd_welch_fast(
    vel_flat: np.ndarray,
    dt_fs: float,
    *,
    window: str = "hann",
    n_segments: Optional[int] = None,
    overlap: float = 0.5,
    prefer_pow2_seglen: bool = True,
    dof_chunk: Optional[int] = None,
    fft_time_last: bool = True,
    fft_dtype: str = "float32",
    notch_bands_THz: Optional[List[Tuple[float, float]]] = None,
    debye_blend: bool = False,
    debye_fit_fmax_THz: float = 1.5,
    debye_blend_fmax_THz: float = 1.5,
    fmax_THz:float = 130, 
    n_jobs: int = 1,
) -> Dict[str, np.ndarray]:
    """
    Build a non-negative, area-normalized per-mode VDOS from velocity time series
    using Welch PSD averaging.

    Parameters
    ----------
    vel_flat : (m, d) ndarray
        Velocities with shape (time, 3N). Apply COM removal before calling if needed.
    dt_fs : float
        Sampling interval in femtoseconds (effective, if you downsampled).
    window : {"hann", None}
        Segment windowing. "hann" recommended.
    n_segments : int or None
        Number of Welch segments. None or <=1 uses a single segment.
    overlap : float in [0, 1)
        Fractional overlap between segments (0.5 recommended for Hann).
    prefer_pow2_seglen : bool
        If True, round segment length down to a power-of-two for faster FFTs.
    dof_chunk : int or None
        Process this many DOFs per pass to limit peak memory (e.g., 1024–4096).
    fft_time_last : bool
        Use time-last layout for better cache locality (recommended).
    fft_dtype : {"float32", "float64"}
        Internal FFT precision (float32 is typically sufficient and faster).
    notch_bands_THz : list of (f0, width)
        Optional suppression of narrow spurious lines.
    debye_blend : bool
        If True, blend a Debye f^2 tail at low frequency (solids only).
    debye_fit_fmax_THz : float
        Upper THz bound for Debye prefactor fit.
    debye_blend_fmax_THz : float
        Upper THz bound for blending.
    n_jobs : int
        If >1, tries to parallelize PSD across DOF chunks using joblib (threads).

    Returns
    -------
    dict
        {"freqs_THz", "dos_mode", "dos_std"}
    """
    m, d = vel_flat.shape
    if m < 8 or d < 1:
        raise ValueError(f"Not enough data: m={m}, d={d}. Need m≥8 and d≥1.")

    # --- segmentation
    if n_segments is None or n_segments <= 1:
        L = m
        step = L
    else:
        L0 = max(8, m // n_segments)
        L = (1 << (L0.bit_length()-1)) if prefer_pow2_seglen else L0
        L = min(L, m)
        step = max(1, int(L * (1.0 - overlap)))
    starts = np.arange(0, m - L + 1, step, dtype=int)
    K = len(starts)
    if K == 0:
        starts = np.array([0], dtype=int)
        L = m
        K = 1

    # --- window and frequency grid
    if isinstance(window, str) and window.lower() == "hann":
        w = np.hanning(L).astype(fft_dtype, copy=False)
    else:
        w = None
    dt_ps = dt_fs * 1e-3
    nfft = L
    nf = nfft // 2 + 1
    freqs = np.fft.rfftfreq(nfft, d=dt_ps)  # THz (1/ps)

    # --- Welford online mean/std
    mean = np.zeros(nf, dtype=np.float64)
    m2 = np.zeros(nf, dtype=np.float64)
    count = 0

    # --- DOF chunking
    csize = d if (dof_chunk is None or dof_chunk <= 0) else int(dof_chunk)

    def _psd_block(block: np.ndarray) -> np.ndarray:
        if fft_time_last:
            X = np.ascontiguousarray(block.T, dtype=fft_dtype)  # (chunk, L)
            F = np.fft.rfft(X, n=nfft, axis=1)                  # (chunk, nf)
            psd = (F.real.astype(np.float64)**2 + F.imag.astype(np.float64)**2).sum(axis=0)
        else:
            X = np.ascontiguousarray(block, dtype=fft_dtype)    # (L, chunk)
            F = np.fft.rfft(X, n=nfft, axis=0)                  # (nf, chunk)
            psd = (F.real.astype(np.float64)**2 + F.imag.astype(np.float64)**2).sum(axis=1)
        return psd

    use_parallel = (isinstance(n_jobs, int) and n_jobs > 1)

    for s in starts:
        seg = vel_flat[s:s+L, :]
        # detrend per-DOF mean
        seg = seg - seg.mean(axis=0, keepdims=True)
        if w is not None:
            seg = seg * w[:, None]

        if use_parallel:
            try:
                from joblib import Parallel, delayed
                blocks = [seg[:, i0:min(i0 + csize, d)] for i0 in range(0, d, csize)]
                psd_list = Parallel(n_jobs=n_jobs, prefer="threads")(
                    delayed(_psd_block)(blk) for blk in blocks
                )
                psd_sum = np.sum(psd_list, axis=0, dtype=np.float64)
            except Exception:
                # Fallback to serial if joblib is unavailable or fails
                psd_sum = np.zeros(nf, dtype=np.float64)
                for i0 in range(0, d, csize):
                    i1 = min(i0 + csize, d)
                    psd_sum += _psd_block(seg[:, i0:i1])
        else:
            psd_sum = np.zeros(nf, dtype=np.float64)
            for i0 in range(0, d, csize):
                i1 = min(i0 + csize, d)
                psd_sum += _psd_block(seg[:, i0:i1])

        # area-normalize to per-mode DOS
        dos_seg = _area_normalize(freqs, psd_sum)

        # Welford update
        count += 1
        delta = dos_seg - mean
        mean += delta / count
        m2 += delta * (dos_seg - mean)

    dos_mean = mean
    dos_std = np.sqrt(m2 / (count - 1)) if count > 1 else np.zeros_like(dos_mean)

    # optional post-processing
    if notch_bands_THz:
        dos_mean = _apply_notch_suppression(freqs, dos_mean, notch_bands_THz)
        dos_mean = _area_normalize(freqs, dos_mean)
    if debye_blend:
        dos_mean = _debye_blend(freqs, dos_mean, debye_fit_fmax_THz, debye_blend_fmax_THz)

    dos_mean = _apply_highf_cutoff(freqs, dos_mean, fmax_THz)

    return {"freqs_THz": freqs, "dos_mode": dos_mean, "dos_std": dos_std}

def _apply_highf_cutoff(freqs_THz: np.ndarray,
                        dos: np.ndarray,
                        fmax_THz: float) -> np.ndarray:
    """
    Zero the DOS above fmax_THz and renormalize to preserve area = 1.
    """
    y = dos.copy()
    mask = freqs_THz > fmax_THz
    if np.any(mask):
        y[mask] = 0.0
        y = _area_normalize(freqs_THz, y)
    return y

# ============================================================
# Thermodynamic kernels (quantum & classical)
# ============================================================
def _log2sinh_stable(x: np.ndarray) -> np.ndarray:
    """
    Numerically stable log(2*sinh(x)) for x >= 0.
    Exact for all x; uses two branches purely for numerical safety.
    Uses asymptotics for large x and log-expm1 identities otherwise.
    """
    x = np.asarray(x, dtype=np.float64)
    out = np.empty_like(x)

    big = x > 35.0
    # For moderate x: log(2*sinh x) = log(expm1(2x)) - x   (no overflow, accurate)
    xm = x[~big]
    out[~big] = np.log(np.expm1(2.0 * xm)) - xm
    # For very large x: log(2*sinh x) = x + log1p(-exp(-2x))  (avoids overflow)
    xb = x[big]
    out[big] = xb + np.log1p(-np.exp(-2.0 * xb))
    '''
    out = np.empty_like(x)
    big = x > 20.0
    out[big] = x[big]
    xm = x[~big]
    out[~big] = np.log(np.expm1(2.0 * xm)) - np.log(2.0)
    return out

    The old small-x branch uses np.log(np.expm1(2*x)) - np.log(2), which is 
    mathematically wrong (it behaves like log x instead of log(2x) for small 
    x and, worse, overestimates by ~x for moderate 𝑥, inflating F). The corrected
     version is exact and stable across regimes.
    '''
    return out


def precompute_vib_kernel(freqs_THz: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Precompute angular frequencies for thermodynamic kernels.

    Parameters
    ----------
    freqs_THz : (nf,) ndarray
        Frequency grid in THz.

    Returns
    -------
    dict
        {"freqs_THz": freqs_THz, "omega": 2π f (rad/s)}
    """
    omega = 2.0 * np.pi * freqs_THz * 1e12   # rad/s
    return {"freqs_THz": freqs_THz, "omega": omega}


def vib_thermo_from_vdos_fast(
    kernel: Dict[str, np.ndarray],
    dos_mode: np.ndarray,
    T_K: float,
    dof_count: int,
    drop_zero_bin: bool = True
) -> Dict[str, float]:
    """
    Quantum harmonic oscillator thermodynamics over a per-mode VDOS.

    F = kT log[2 sinh(β ħ ω / 2)]
    U = 1/2 ħ ω coth(β ħ ω / 2)
    S = (U - F) / T

    Parameters
    ----------
    kernel : dict
        Output of `precompute_vib_kernel` with "freqs_THz" and "omega".
    dos_mode : (nf,) ndarray
        Area-normalized per-mode DOS.
    T_K : float
        Temperature in kelvin.
    dof_count : int
        Active DOF count used as a multiplicative factor.
    drop_zero_bin : bool
        If True and the first bin is exactly 0 THz, drop it to avoid ω=0 issues.

    Returns
    -------
    dict
        {"F_vib_eV", "U_vib_eV", "E_ZP_eV", "S_vib_eV_perK"}
    """
    freqs_THz = kernel["freqs_THz"]
    omega = kernel["omega"]

    if drop_zero_bin and freqs_THz.size > 1 and freqs_THz[0] == 0.0:
        f = freqs_THz[1:]
        g = dos_mode[1:]
        om = omega[1:]
    else:
        f = freqs_THz
        g = dos_mode
        om = omega

    kB_eV   = 8.617333262e-5
    hbar_eV = 6.582119569e-16
    T = max(T_K, 1e-12)
    beta = 1.0 / (kB_eV * T)
    x = 0.5 * beta * hbar_eV * om

    F_mode = kB_eV * T * _log2sinh_stable(x)

    cothx = 1.0 / np.tanh(x)
    U_mode = 0.5 * hbar_eV * om * cothx
    # less robust option : U_mode = 0.5 * hbar_eV * om * (np.cosh(x) / (np.sinh(x) + 1e-300))

    S_mode = (U_mode - F_mode) / T

    F_per = np.trapz(g * F_mode, f)
    U_per = np.trapz(g * U_mode, f)
    S_per = np.trapz(g * S_mode, f)
    ZP_per = np.trapz(g * (0.5 * hbar_eV * om), f)

    return {
        "F_vib_eV": float(F_per * dof_count),
        "U_vib_eV": float(U_per * dof_count),
        "E_ZP_eV":  float(ZP_per * dof_count),
        "S_vib_eV_perK": float(S_per * dof_count),
    }


def vib_thermo_from_vdos_classical(
    kernel: Dict[str, np.ndarray],
    dos_mode: np.ndarray,
    T_K: float,
    dof_count: int,
    drop_zero_bin: bool = True,
) -> Dict[str, float]:
    """
    Classical harmonic oscillator limit over a per-mode VDOS.

    Per mode:
      F_cl(ω,T) = k_B T ln(β ħ ω)   (up to an additive constant that cancels in comparisons)
      U_cl(ω,T) = k_B T
      S_cl(ω,T) = k_B [1 - ln(β ħ ω)]

    Notes
    -----
    - E_ZP_classical = 0 by definition.
    - This is mainly useful for reference or high-T comparisons.
    """
    freqs_THz = kernel["freqs_THz"]
    omega = kernel["omega"]

    kB_eV = 8.617333262e-5
    T = max(T_K, 1e-12)
    beta = 1.0 / (kB_eV * T)
    hbar_eV = 6.582119569e-16

    if drop_zero_bin and freqs_THz.size > 1 and freqs_THz[0] == 0.0:
        f = freqs_THz[1:]
        g = dos_mode[1:]
        om = omega[1:]
    else:
        f = freqs_THz
        g = dos_mode
        om = omega

    F_mode = kB_eV * T * np.log(beta * hbar_eV * om)
    U_mode = np.full_like(om, kB_eV * T)
    S_mode = (U_mode - F_mode) / T

    F_per = np.trapz(g * F_mode, f)
    U_per = np.trapz(g * U_mode, f)
    S_per = np.trapz(g * S_mode, f)

    return {
        "F_vib_eV_classical": float(F_per * dof_count),
        "U_vib_eV_classical": float(U_per * dof_count),
        "S_vib_eV_perK_classical": float(S_per * dof_count),
        "E_ZP_eV_classical": 0.0,
    }


def vib_thermo_from_vdos_both(
    kernel: Dict[str, np.ndarray],
    dos_mode: np.ndarray,
    T_K: float,
    dof_count: int,
    drop_zero_bin: bool = True,
) -> Dict[str, float]:
    """
    Convenience wrapper that returns both quantum and classical results.
    """
    out_q = vib_thermo_from_vdos_fast(kernel, dos_mode, T_K, dof_count, drop_zero_bin)
    out_c = vib_thermo_from_vdos_classical(kernel, dos_mode, T_K, dof_count, drop_zero_bin)
    return {**out_q, **out_c}

# -----------------------------
# One-call fast pipeline
# -----------------------------
def corrected_vdos_and_F_from_velocities(
    vel_flat: np.ndarray,
    dt_fs: float,
    T_K: float,
    dof_count: int,
    *,
    masses: Optional[np.ndarray] = None,
    remove_COM: bool = False,
    mass_weighting: bool = True,
    window: str = "hann",
    n_segments: Optional[int] = 8,
    overlap: float = 0.5,
    prefer_pow2_seglen: bool = True,
    dof_chunk: Optional[int] = None,
    fft_time_last: bool = True,
    fft_dtype: str = "float32",
    notch_bands_THz: Optional[List[Tuple[float, float]]] = None,
    debye_lowf_blend: bool = False,
    debye_fit_fmax_THz: float = 1.5,
    debye_blend_fmax_THz: float = 1.5,
    stats: str = "quantum",  #  {"quantum","classical","both"}
    fmax_THz: float = 130,
    n_jobs: int = 1,
) -> Dict[str, object]:
    """
    Compute vibrational thermodynamics from a velocity trajectory in one call.

    Pipeline (all in-core, no new MD):
        1) Optional per-frame COM drift removal (mass-weighted).
        2) Non-negative VDOS via Welch-averaged PSD of velocities.
        3) Optional notch suppression of narrow artifacts (e.g., thermostat lines).
        4) Optional Debye low-frequency blending for crystalline solids.
        5) Quantum-harmonic thermodynamics integrated over the per-mode VDOS.

    Parameters
    ----------
    vel_flat : (m, d) ndarray of float
        Velocity time series with `m` frames and `d = 3N` Cartesian DOFs
        (row-major: time along axis 0, flattened DOFs along axis 1).
        Units can be arbitrary but must be self-consistent across the run.

    dt_fs : float
        MD sampling interval **in femtoseconds** corresponding to adjacent rows
        in `vel_flat`. If you downsampled during collection (e.g., storing every
        k-th MD step), this must be the *effective* interval (k × MD timestep).

    T_K : float
        Temperature **in kelvin** used for the quantum-harmonic kernels
        (F, U, S). This does not rescale your trajectory; it only parametrizes
        the thermodynamic integrals.

    dof_count : int
        Number of *active* dynamical DOFs represented by your spectrum,
        used as a multiplicative factor after integrating per-mode quantities.
        Typical choices:
            - periodic solids: `3*N - 3` (remove rigid translations)
            - with constraints: `3*N - (# frozen DOFs)`
        Make sure this is consistent with any ASE constraints you applied.

    masses : (N,) ndarray of float, optional (keyword-only)
        Atomic masses, required if `remove_COM=True` to perform mass-weighted
        COM removal at each frame. If `remove_COM=False`, this is ignored.

    remove_COM : bool, default True (keyword-only)
        If True, subtract the instantaneous center-of-mass velocity from every
        frame (mass-weighted using `masses`). Strongly recommended to clean the
        f→0 region for solids.

    window : {"hann", None}, default "hann" (keyword-only)
        Time-domain window applied per Welch segment before the FFT. "hann"
        reduces leakage and is standard for PSD estimation.

    n_segments : int or None, default 8 (keyword-only)
        Number of Welch segments. `None` or `<=1` means “use the whole trace as
        a single segment” (higher variance). 6–12 is a good range for typical
        lengths.

    overlap : float in [0, 1), default 0.5 (keyword-only)
        Fractional overlap between adjacent Welch segments. With "hann", 50%
        overlap satisfies COLA and gives good variance reduction.

    prefer_pow2_seglen : bool, default True (keyword-only)
        If True, each segment length is rounded to the nearest power-of-two
        (floor) for faster RFFT without extra zero-padding.

    dof_chunk : int or None, default None (keyword-only)
        Process DOFs in chunks of this size to limit peak memory and improve
        cache locality. `None` processes all DOFs at once. Values like 1024–4096
        are often effective for large systems.

    fft_time_last : bool, default True (keyword-only)
        If True, reshapes each segment to (DOF, L) and FFTs along the **time**
        axis (axis=1) for better memory access patterns. Keep True unless you
        have a specific reason.

    fft_dtype : {"float32", "float64"}, default "float32" (keyword-only)
        Internal FFT precision. "float32" is typically ~2× faster and sufficient
        for PSD estimation; all integrals/accumulators run in float64.

    notch_bands_THz : list of (f0, width) tuples in THz, optional (keyword-only)
        List of narrow frequency bands to suppress (by linear interpolation)
        after Welch averaging, e.g., to remove thermostat lines. Example:
        `[(1.0, 0.1)]` notches [0.95, 1.05] THz.

    debye_lowf_blend : bool, default False (keyword-only)
        If True, fit `g(f) ≈ c f^2` on [0, `debye_fit_fmax_THz`] and smoothly
        blend this Debye form into the VDOS up to `debye_blend_fmax_THz`.
        Recommended **only** for crystalline solids; disable for liquids or
        amorphous phases.

    debye_fit_fmax_THz : float, default 1.5 (keyword-only)
        Upper frequency (THz) used to least-squares fit the Debye prefactor `c`
        on the low-f window.

    debye_blend_fmax_THz : float, default 1.5 (keyword-only)
        Upper frequency (THz) up to which the Debye fit is blended into the
        measured VDOS. The result is area-renormalized to 1 afterwards.

    stats : {"quantum","classical","both"}, default "quantum"
        Which thermodynamic treatment to return:
        - "quantum"   : QHOs with F = kT ln[2 sinh(β ħ ω / 2)]
        - "classical" : classical HO limit with F = kT ln(β ħ ω) (constant cancels in comparisons)
        - "both"      : include both sets of outputs (keys suffixed with _classical for the latter)
    
    fmax_THz : float, Trim unphysical high-f noise

    Returns
    -------
    out : dict
        Dictionary with the following fields:
            - "freqs_THz" : (nf,) ndarray
                Frequency axis in **THz** (1/ps), one-sided (rFFT grid).
            - "dos_mode"  : (nf,) ndarray
                Per-mode VDOS (area-normalized so ∫ dos df = 1 over THz).
            - "dos_std"   : (nf,) ndarray
                Standard deviation across Welch segments (zeros if single segment).
            - "F_vib_eV" : float
                Vibrational free energy in **eV**.
            - "U_vib_eV" : float
                Vibrational internal energy in **eV**.
            - "E_ZP_eV"  : float
                Zero-point energy in **eV**.
            - "S_vib_eV_perK" : float
                Vibrational entropy in **eV/K**.

    Raises
    ------
    ValueError
        If inputs are inconsistent (e.g., `remove_COM=True` but `masses is None`,
        insufficient samples/DOFs, or shape mismatches).

    Notes
    -----
    * The VDOS is built from a **non-negative PSD** of the detrended velocities
      (Wiener–Khinchin) with Welch averaging, then area-normalized per mode.
    * The thermodynamics kernel corresponds to **independent quantum harmonic
      oscillators** whose frequencies are sampled from the (temperature-renormalized)
      VDOS extracted from classical MD (quasi-harmonic picture).
    * Ensure `dof_count` reflects any ASE constraints (FixAtoms/FixCartesian).
    * For accurate low-frequency behavior in solids, enable COM removal and,
      optionally, the Debye blending (tune the `1–2 THz` window to your material).
    * Units: input `dt_fs` in fs, output `freqs_THz` in THz, energies in eV.

    Examples
    --------
    >>> # vel_flat.shape == (m, 3*N)
    >>> out = corrected_vdos_and_F_from_velocities(
    ...     vel_flat, dt_fs=2.0, T_K=300.0, dof_count=3*N-3,
    ...     masses=masses, remove_COM=True, n_segments=8, overlap=0.5,
    ...     debye_lowf_blend=True, debye_fit_fmax_THz=1.2, debye_blend_fmax_THz=1.2)
    >>> F = out["F_vib_eV"]; freqs = out["freqs_THz"]; dos = out["dos_mode"]

    See Also
    --------
    remove_com_drift : per-frame COM removal
    vdos_psd_welch_fast : fast, memory-lean Welch PSD → VDOS
    precompute_vib_kernel, vib_thermo_from_vdos_fast : cached thermodynamics
    """
    # --- validations
    v = np.asarray(vel_flat)

    if v.ndim != 2 or v.shape[0] < 8 or v.shape[1] < 3:
        raise ValueError(f"vel_flat invalid: shape={v.shape}, need (m≥8, d multiple of 3).")
    if v.shape[1] % 3 != 0:
        raise ValueError("vel_flat must have 3N columns (N atoms).")
    if not np.isfinite(dt_fs) or dt_fs <= 0:
        raise ValueError(f"Invalid dt_fs: {dt_fs}.")
    if not np.isfinite(T_K) or T_K < 0:
        raise ValueError(f"Invalid T_K: {T_K}.")
    if not isinstance(dof_count, int) or dof_count <= 0:
        raise ValueError(f"Invalid dof_count: {dof_count}.")

    # --- COM removal if requested
    if remove_COM:
        if masses is None:
            raise ValueError("masses required when remove_COM=True.")
        v = remove_com_drift(v.astype(np.float64, copy=False), masses=np.asarray(masses, dtype=np.float64))
    else:
        v = v.astype(np.float64, copy=False)

    # =========================================================================
    # ### MASS WEIGHTING ###
    # =========================================================================
    if mass_weighting:
        if masses is None:
            raise ValueError("masses required when mass_weighting=True.")
        
        # 1. Ensure masses array is numpy float64
        m_arr = np.asarray(masses, dtype=np.float64)
        
        # 2. Verify shape matches velocities
        # v has shape (n_steps, 3*N_atoms)
        N_atoms = v.shape[1] // 3
        if m_arr.shape[0] != N_atoms:
             raise ValueError(f"Masses shape {m_arr.shape} does not match N_atoms={N_atoms}.")

        # 3. Create weighting factors [sqrt(m1), sqrt(m1), sqrt(m1), sqrt(m2)...]
        # We repeat each mass 3 times (for x, y, z components)
        sqrt_masses = np.sqrt(np.repeat(m_arr, 3))
        
        # 4. Apply weighting: v_weighted = v * sqrt(m)
        # Broadcasting: (n_steps, 3N) * (1, 3N)
        v = v * sqrt_masses[None, :]
        
        # Note: Now 'v' represents sqrt(2*KineticEnergy), not velocity.
        # The VDOS calculated from this will be the "Generalized Density of States"
        # required for accurate thermodynamics in multi-species systems.
    # =========================================================================

    # --- VDOS
    vdos = vdos_psd_welch_fast(
        v, dt_fs,
        window=window,
        n_segments=n_segments,
        overlap=overlap,
        prefer_pow2_seglen=prefer_pow2_seglen,
        dof_chunk=dof_chunk,
        fft_time_last=fft_time_last,
        fft_dtype=fft_dtype,
        notch_bands_THz=notch_bands_THz,
        debye_blend=debye_lowf_blend,
        debye_fit_fmax_THz=debye_fit_fmax_THz,
        debye_blend_fmax_THz=debye_blend_fmax_THz,
        fmax_THz=fmax_THz,
        n_jobs=n_jobs,
    )

    kernel = precompute_vib_kernel(vdos["freqs_THz"])

    st = (stats or "quantum").lower()
    if st == "quantum":
        thermo = vib_thermo_from_vdos_fast(kernel, vdos["dos_mode"], T_K, dof_count)
        default_add_key = "F_vib_eV"
    elif st == "classical":
        thermo = vib_thermo_from_vdos_classical(kernel, vdos["dos_mode"], T_K, dof_count)
        default_add_key = "F_vib_eV_classical"
    elif st == "both":
        thermo = vib_thermo_from_vdos_both(kernel, vdos["dos_mode"], T_K, dof_count)
        default_add_key = "F_vib_eV"  # prefer quantum by default
    else:
        raise ValueError("stats must be 'quantum', 'classical', or 'both'.")

    out = dict(vdos)
    out.update(thermo)
    out["T_K"] = float(T_K)
    out["dof_count"] = int(dof_count)

    return out

# --------------------------------------------------------------------------
# Vibrational thermodynamics outputs (all system-wide, not per atom):
# --------------------------------------------------------------------------
# 'freqs_THz' : Frequency grid (in THz) from FFT/Welch analysis.
#               Should cover ~0–100 THz with fine resolution (spacing < 1 THz).
#
# 'dos_mode'  : Per-mode vibrational density of states (normalized so ∫DOS df = 1).
#               Represents the probability distribution of vibrational frequencies.
#
# 'dos_std'   : Standard deviation of DOS from Welch segment averaging;
#               small values indicate good statistical convergence.
#
# --- Quantum (harmonic oscillator) thermodynamics ---
# 'E_ZP_eV'   : Zero-point energy, sum of ½ ħω over all modes.
#               Typical ~0.03 eV/atom for heavy atoms, up to 0.3 eV per H.
#
# 'U_vib_eV'  : Vibrational internal energy = E_ZP + thermal phonon energy.
#               At 300 K, ~0.05–0.15 eV/atom is common.
#
# 'S_vib_eV_perK' : Vibrational entropy (should be positive).
#                   Negative values indicate poor spectral resolution or
#                   missing Debye tail correction.
#
# 'F_vib_eV'  : Vibrational Helmholtz free energy = U_vib – T*S_vib.
#               Add this to the static electronic energy to get finite-T free energy.
#               Typically reduces stability by ~0.05–0.15 eV/atom at 300 K.
#
# --- Classical limit (high-T approximation, no zero-point) ---
# 'E_ZP_eV_classical' = 0.0 by definition.
# 'U_vib_eV_classical' : Equipartition result (~kB T per mode).
# 'S_vib_eV_perK_classical' : Classical vibrational entropy, positive.
# 'F_vib_eV_classical' : Classical vibrational free energy. Absolute values are
#                        arbitrary; only differences between structures are meaningful.
# --------------------------------------------------------------------------


# ============================================================
# Metadata helpers (save scalars only)
# ============================================================
_SCALAR_KEYS_PRIORITY = [
    "F_vib_eV", "U_vib_eV", "E_ZP_eV", "S_vib_eV_perK",
    "F_vib_eV_classical", "U_vib_eV_classical", "E_ZP_eV_classical", "S_vib_eV_perK_classical",
    "F_add_eV", "T_K", "dof_count",
]


def scalars_only(results: Dict[str, object],
                 extra_scalars: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Extract only scalar (finite) quantities from `results`, in a stable order.

    Parameters
    ----------
    results : dict
        Output from `corrected_vdos_and_F_from_velocities`.
    extra_scalars : list of str, optional
        Additional keys to try to extract.

    Returns
    -------
    dict
        Scalar-only subset suitable for lightweight metadata storage.
    """
    keys = list(_SCALAR_KEYS_PRIORITY)
    if extra_scalars:
        keys.extend(extra_scalars)
    out = {}
    for k in keys:
        if k in results and np.isscalar(results[k]) and np.isfinite(results[k]):
            out[k] = float(results[k])
    return out


def update_individual_metadata(individual, corrections: Dict[str, object]) -> None:
    """
    Store scalar vibrational corrections into an object's metadata field.

    The function writes human-friendly keys and keeps arrays (VDOS, etc.)
    out of metadata to avoid bloat.

    Parameters
    ----------
    individual : object
        Must have `AtomPositionManager.metadata` (a dict-like).
    corrections : dict
        Typically the output of `corrected_vdos_and_F_from_velocities` or
        `scalars_only(...)`.
    """
    meta = individual.AtomPositionManager.metadata
    pairs = [
        ("Fvib_quantum", "F_vib_eV"),
        ("Fvib_classical", "F_vib_eV_classical"),
        ("U_vib_quantum", "U_vib_eV"),
        ("U_vib_classical", "U_vib_eV_classical"),
        ("S_vib_quantum", "S_vib_eV_perK"),
        ("S_vib_classical", "S_vib_eV_perK_classical"),
        ("E_ZP_quantum", "E_ZP_eV"),
        ("E_ZP_classical", "E_ZP_eV_classical"),
        ("F_add_eV", "F_add_eV"),
        ("T", "T_K"),
        ("dof_count", "dof_count"),
    ]
    for meta_key, corr_key in pairs:
        if corr_key in corrections and np.isscalar(corrections[corr_key]) and np.isfinite(corrections[corr_key]):
            meta[meta_key] = float(corrections[corr_key])