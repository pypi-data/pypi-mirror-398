"""
Unified structure-hash manager with user‑selectable fingerprinting method
and precision-ensemble voting to discriminate duplicates vs. true collisions.


Public API remains compatible with CanonicalHashMap / PairRDFHashMap and
previous Structure_Hash_Map usage. New (opt‑in) APIs:


vote_duplicate(container, expected_hash=None, vote_frac=None, min_votes=None)
add_structure_voted(container, *, force_rehash=True, vote_frac=None, min_votes=None)


Example
-------
cmap = Structure_Hash_Map(method="rdf", r_max=10.0, bin_width=0.02,
vote_frac=0.6, min_votes=5,
precision_scales=(0.5, 1.0, 2.0))
report = cmap.add_structure_voted(container)


# report = {
# "added": False, "duplicate": True, "collision": False,
# "hash": "...", "votes_agree": 5, "votes_total": 7, "comp_key": "..."
# }
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from typing import Optional, Callable, Dict, List, Tuple, Any
from math import gcd
from functools import reduce

import numpy as np
import spglib
from scipy.spatial import KDTree, cKDTree
import unittest
import random
from sage_lib.single_run.SingleRun import SingleRun

import math
import hashlib
from collections import defaultdict

from ..core.interfaces import IHash

__all__ = ["Structure_Hash_Map"]

# ============================================================================
#  KD‑tree serialiser (shared by all methods that need it)
# ============================================================================
def _serialize_kdtree_node(node) -> str:
    """Recursive, deterministic serialisation of a SciPy KDTree node."""
    if hasattr(node, "idx"):
        return "L[" + ",".join(map(str, node.idx.tolist())) + "]"
    split_val = f"{node.split:.6f}"
    left = _serialize_kdtree_node(node.less)
    right = _serialize_kdtree_node(node.greater)
    return f"I{node.split_dim}:{split_val}({left})({right})"


def _serialize_kdtree(tree) -> str:
    if isinstance(tree, cKDTree):  # rebuild pure‑Python tree for determinism
        tree = KDTree(tree.data, leafsize=getattr(tree, "leafsize", 10))
    return _serialize_kdtree_node(tree.tree)

# ============================================================================
#  Hash‑method implementations
# ============================================================================
def _build_integer_modes_sphere(kmax: int) -> np.ndarray:
    """
    All non-zero integer triplets m=(hx,ky,lz) with ||m||_2 <= kmax, in lexicographic order.
    Includes negatives; excludes (0,0,0).
    """


def _group_shells_by_r2(M: np.ndarray) -> Tuple[np.ndarray, Dict[int, np.ndarray], np.ndarray]:
    """
    Groups integer modes by r2 = h^2 + k^2 + l^2 (spherical shells).
    Returns:
      unique_r2: (S,) sorted unique shell radii squared
      shell_idx: dict r2 -> indices (in M) that belong to that shell
      r2_of_mode: (M,) r2 for each mode (int32)
    """
    r2 = (M[:, 0].astype(np.int64)**2 +
          M[:, 1].astype(np.int64)**2 +
          M[:, 2].astype(np.int64)**2).astype(np.int64)
    uniq = np.unique(r2)
    shell_idx = {int(rr): np.where(r2 == rr)[0] for rr in uniq}
    return uniq.astype(np.int64), shell_idx, r2.astype(np.int64)


# ---------------------------------------------------------------------------
#  Helper: TSF-hash
# ---------------------------------------------------------------------------
def _build_integer_modes_sphere(kmax: int) -> np.ndarray:
    """
    Build an integer reciprocal grid M ⊂ Z^3 inside a sphere of radius kmax,
    excluding the origin. The list is deterministic (lexicographic order).

    Parameters
    ----------
    kmax : int
        Radius in integer space. kmax=3 → typically ~ 100 modes.

    Returns
    -------
    np.ndarray
        Array of shape (M, 3) with integer triples (h, k, l).
    """
    rng = range(-kmax, kmax + 1)
    modes = []
    for h in rng:
        for k in rng:
            for l in rng:
                if h == 0 and k == 0 and l == 0:
                    continue
                if h*h + k*k + l*l <= kmax*kmax:
                    modes.append((h, k, l))
    M = np.asarray(modes, dtype=np.int32)
    M = M[np.lexsort((M[:, 2], M[:, 1], M[:, 0]))]
    return M

def _is_nonperiodic(apm) -> bool:
    # Prefer explicit flag if your APM exposes it
    pbc = getattr(apm, "pbc", None)           # e.g. (False, False, False)
    if isinstance(pbc, (tuple, list)) and not any(pbc):
        return True
    # Fallback: missing/degenerate lattice → treat as non-periodic
    try:
        lat = np.asarray(apm.latticeVectors, float)
        return not np.isfinite(lat).all() or abs(np.linalg.det(lat)) < 1e-9
    except Exception:
        return True

# ---------------------------------------------------------------------------
#  Helper: canonical primitive cell (shared)
# ---------------------------------------------------------------------------
def _canonical_cell(apm, symprec: float, debug: bool):

    if _is_nonperiodic(apm):
        # Non-PBC: stay in Cartesian; use identity lattice; do not mod 1
        cart = np.asarray(apm.atomPositions, float)  # or .get_atomPositions_cartesian()
        Z    = np.asarray(apm.get_atomic_numbers(), int)
        return None, cart, Z

    # (unchanged PBC branch)
    lat0 = np.asarray(apm.latticeVectors, float).T
    frac0 = np.asarray(apm.atomPositions_fractional, float) % 1.0
    Z = np.asarray(apm.get_atomic_numbers(), int)
    try:
        lat, frac, Z = spglib.standardize_cell(
            (lat0.copy(), frac0.copy(), Z.copy()),
            to_primitive=True, no_idealize=False, symprec=symprec
        )
        frac %= 1.0
        return lat, frac, Z
    except Exception:
        if debug: print("spglib fallback to original cell")
        return lat0, frac0, Z


# ---------------------------------------------------------------------------
#  Fastest hash ROT INV
# ---------------------------------------------------------------------------
def _structure_factor_hash_factory_rotinv(
    *,
    # Reciprocal sampling
    kmax: int = 3,
    modes: Optional[np.ndarray] = None,   # custom (M,3) integer modes; overrides kmax when given
    per_species: bool = True,             # channels per Z (True) or aggregated (False)
    # Quantization
    ps_grid: float = 1e-1,                # shell-averaged |S| quantization grid
    lattice_grid: float = 2e-2,           # Å (lattice quantization)
    e_grid: float = 1e-3,                 # eV/atom tick (optional)
    v_grid: float = 1e-2,                 # Å^3/atom tick (optional)
    include_energy: bool = True,
    include_volume: bool = True,
    # Symmetry canonicalization (optional; improves reproducibility across settings)
    use_spglib: bool = False,
    symprec: float = 1e-3,
    angle_tolerance: float = -1.0,
    # Performance / robustness
    chunk_size: int = 50000,
    debug: bool = False,
) -> Callable[[object], str]:
    """
    Rotationally-invariant TSF hash (periodic): averages |S_Z(m)| over spherical shells
    of integer modes with identical r^2 = ||m||^2. This yields exact invariance to
    rigid rotations (in the discrete integer-lattice sense), exact translation invariance,
    and permutation invariance. Non-PBC structures fall back to a centered integer multiset.

    The hash payload (before SHA-256) includes:
      - quantized lattice (int),
      - species channel IDs (if per_species),
      - quantized shell-averaged magnitudes (int),
      - meta: [N, #channels, e_tick, v_tick], all little-endian.

    Assumptions:
      container.AtomPositionManager provides:
        - atomPositions (N,3) Cartesian (Å)
        - latticeVectors (3,3) with column vectors (a,b,c)
        - get_atomic_numbers() -> (N,)
        - optional .pbc (tuple/list of 3 bools), optional .E (total energy)
    """

    TWO_PI = 2.0 * math.pi
    EPS = 1e-12

    # Build modes and shells
    if modes is None:
        M = _build_integer_modes_sphere(kmax)
    else:
        M = np.asarray(modes, dtype=np.int32)
        if M.ndim != 2 or M.shape[1] != 3 or M.shape[0] == 0:
            raise ValueError("modes must have shape (M,3) with M>0")
        M = M[np.lexsort((M[:, 2], M[:, 1], M[:, 0]))]

    unique_r2, shell_index, r2_by_mode = _group_shells_by_r2(M)
    # Exclude the shell r2 == 0 if somehow present (shouldn't with our builder)
    if unique_r2[0] == 0:
        if debug:
            print("Removing r2=0 shell (contains only (0,0,0))")
        idx = np.where(unique_r2 != 0)[0]
        unique_r2 = unique_r2[idx]

    M_T = M.T
    M_count = int(M.shape[0])
    S_count = int(unique_r2.shape[0])  # number of shells

    def qint(x: np.ndarray, grid: float) -> np.ndarray:
        return np.floor(np.asarray(x, float) / grid + 0.5).astype(np.int32, copy=False)

    def hbytes(*chunks: bytes) -> str:
        h = hashlib.sha256()
        for c in chunks:
            h.update(c)
        return h.hexdigest()

    def hash_fn(container) -> str:
        apm = container.AtomPositionManager

        # PBC detection
        try:
            pbc_flags = getattr(apm, "pbc", None)
            is_nonpbc = isinstance(pbc_flags, (tuple, list)) and not any(pbc_flags)
        except Exception:
            is_nonpbc = False
        if not isinstance(is_nonpbc, bool):
            is_nonpbc = False

        # Basic properties
        Z = np.asarray(apm.get_atomic_numbers(), np.int32)
        N = int(Z.shape[0])
        if N == 0:
            return hbytes(b"TSFv2_rot\0", np.array([0], dtype="<i8").tobytes())

        # Optional ticks
        try:
            E_total = float(getattr(apm, "E", 0.0))
        except Exception:
            E_total = 0.0
        e_tick = -1 if not include_energy else int(math.floor((E_total / N) / e_grid + 0.5))

        # Non-PBC fallback: translation- and rotation-invariant integer multiset
        if is_nonpbc:
            X = np.asarray(apm.atomPositions, float)
            Xc = X - X.mean(axis=0)        # remove translation
            # Rotation invariance (approx): use pairwise distance spectrum as a stable signature
            # Here we keep a compact alternative: quantize centered coords + counts (robust/practical).
            Xq = qint(Xc, lattice_grid)
            K = np.column_stack((Z, Xq)).astype(np.int32)
            Kuniq, counts = np.unique(K, axis=0, return_counts=True)
            meta = np.array([N, e_tick, -1], dtype="<i8").tobytes()
            return hbytes(
                b"TSFv2_rot\0",
                np.zeros((3, 3), dtype="<i4").tobytes(),
                np.asarray(Kuniq, dtype="<i4").tobytes(),
                np.asarray(counts, dtype="<i4").tobytes(),
                meta,
            )

        # Periodic path: fractionals
        A_cols = np.asarray(apm.latticeVectors, float)   # columns a,b,c
        A = A_cols.T                                     # rows for math
        X = np.asarray(apm.atomPositions, float)
        FinvT = np.linalg.inv(A).T
        F = (X @ FinvT + EPS) % 1.0

        # Optional canonicalization (sets a reproducible setting/origin)
        if use_spglib:
            try:
                import spglib
                A_s, F_s, Z_s = spglib.standardize_cell(
                    (A.copy(), F.copy(), Z.copy()),
                    to_primitive=True, no_idealize=True,
                    symprec=symprec, angle_tolerance=angle_tolerance,
                )
                A = np.asarray(A_s, float)
                F = (np.asarray(F_s, float) + EPS) % 1.0
                Z = np.asarray(Z_s, np.int32)
                N = int(Z.shape[0])
            except Exception as exc:
                if debug:
                    print("spglib reduction failed; using unreduced cell:", exc)

        # Species channels
        if per_species:
            species, inv = np.unique(Z, return_inverse=True)  # sorted ascending
            C = int(species.shape[0])
        else:
            species = np.array([0], dtype=np.int32)
            inv = np.zeros(N, dtype=np.int32)
            C = 1

        # Accumulate structure factors S per species and per mode
        S_re = np.zeros((C, M_count), dtype=np.float64)
        S_im = np.zeros((C, M_count), dtype=np.float64)

        for s in range(0, N, max(1, int(chunk_size))):
            e = min(N, s + chunk_size)
            Fi = F[s:e]               # (chunk, 3)
            inv_i = inv[s:e]          # (chunk,)
            phase = TWO_PI * (Fi @ M_T)       # (chunk, M)
            Ei_re = np.cos(phase)
            Ei_im = np.sin(phase)
            for m in range(M_count):
                S_re[:, m] += np.bincount(inv_i, weights=Ei_re[:, m], minlength=C)
                S_im[:, m] += np.bincount(inv_i, weights=Ei_im[:, m], minlength=C)

        # Normalize per species
        Nz = np.bincount(inv, minlength=C).astype(np.float64)
        denom = np.sqrt(np.maximum(Nz, 1.0))[:, None]
        P = np.hypot(S_re, S_im) / denom    # (C, M)

        # -------- Rotational invariance via spherical shell averaging ----------
        # For each shell (fixed r2), average magnitudes across its modes.
        # Result: (C, S) array of shell-averaged magnitudes.
        P_shell = np.zeros((C, S_count), dtype=np.float64)
        for s_idx, r2 in enumerate(unique_r2):
            idx = shell_index[int(r2)]           # indices in 0..M-1
            # mean over modes in this shell; L2-mean or simple mean both OK;
            # we use arithmetic mean (rotation-invariant under permutations).
            P_shell[:, s_idx] = P[:, idx].mean(axis=1)

        # Quantize shell-averaged magnitudes and lattice
        Pq = qint(P_shell, ps_grid)          # (C, S) int32
        A_q = qint(A, lattice_grid)          # (3, 3) int32

        v_tick = -1
        if include_volume:
            vpa = abs(np.linalg.det(A)) / max(N, 1)
            v_tick = int(math.floor(vpa / v_grid + 0.5))

        # Serialize deterministically:
        # [signature][quantized lattice][species IDs][shells r2][quantized shell spectrum][meta]
        meta = np.array([N, int(species.shape[0]), e_tick, v_tick], dtype="<i8").tobytes()

        return hbytes(
            b"TSFv2_rot\0",
            np.asarray(A_q, dtype="<i4").tobytes(),
            np.asarray(species, dtype="<i4").tobytes(),
            np.asarray(unique_r2, dtype="<i8").tobytes(),   # shell definition
            np.asarray(Pq, dtype="<i4").tobytes(),
            meta,
        )

    return hash_fn
    

# ---------------------------------------------------------------------------
#  Fastest hash
# ---------------------------------------------------------------------------
def _structure_factor_hash_factory(
    *,
    # Fourier sampling
    kmax: int = 3,
    modes: Optional[np.ndarray] = None,   # custom (M,3) integer modes; overrides kmax when given
    per_species: bool = True,             # accumulate |S| per atomic number channel
    ps_grid: float = 1e-1,                # quantization grid for |S| magnitudes
    # Lattice / metadata quantization
    lattice_grid: float = 2e-2,           # Å
    e_grid: float = 1e-3,                 # eV/atom (optional tick)
    v_grid: float = 1e-2,                 # Å^3/atom (optional tick)
    include_energy: bool = True,
    include_volume: bool = True,
    # Symmetry reduction (optional; not needed for translation invariance)
    use_spglib: bool = False,
    symprec: float = 1e-3,
    angle_tolerance: float = -1.0,
    # Performance / numerical robustness
    chunk_size: int = 50000,              # number of atoms per chunk in accumulation
    debug: bool = False,
    **kwargs,
) -> Callable[[object], str]:
    """
    Factory for a fast, translation-invariant global hash based on the modulus
    of structure factors on a small set of integer reciprocal modes.

    Mathematical idea
    ------------------
    For a periodic structure with fractional coordinates F ∈ [0,1)^{N×3},
    the (unnormalized) structure factor on an integer mode m ∈ Z^3 is:
        S(m) = Σ_i exp(i 2π m·F_i).
    A rigid translation by t (fractional) sends F_i → F_i + t, hence
        S'(m) = exp(i 2π m·t) S(m),
    so the modulus |S(m)| is *exactly translation invariant*. We compute |S|
    on a small, fixed set of modes (a sphere in Z^3 of radius kmax), optionally
    per species, lightly quantize, and hash the integer tensor.

    Complexity and scaling
    ----------------------
    The computation is O(N * M) where M is the number of modes (dozens to low
    hundreds). This scales linearly in N and is robust for N >> 10^3. We process
    atoms in chunks to bound memory usage.

    Assumptions
    -----------
    The container exposes `AtomPositionManager` (APM) with:
      - `atomPositions` (Cartesian, shape (N,3), floats, current),
      - `latticeVectors` (3×3, your codebase stores as *columns* a,b,c),
      - `get_atomic_numbers()` → (N,) array-like of ints,
      - optional `.E` (total energy).
    We do not rely on cached fractional coordinates; we recompute them from the
    *current* Cartesian positions and the lattice each call.

    Parameters
    ----------
    kmax : int
        Sphere radius in integer reciprocal space (controls M).
    modes : np.ndarray, optional
        Custom integer modes (M,3). If given, kmax is ignored.
    per_species : bool
        If True, produce a channel per atomic number (more discriminative).
        If False, aggregate all atoms together (faster/shorter descriptor).
    ps_grid : float
        Quantization grid for |S| magnitudes (pre-hash integerization).
    lattice_grid : float
        Quantization grid for lattice (Å).
    e_grid, v_grid : float
        Quantization grids for energy/atom and volume/atom ticks.
    include_energy, include_volume : bool
        Whether to append E/N and V/N ticks (integerized).
    use_spglib : bool
        If True, reduce to a primitive cell (origin independent). Not required
        for translation invariance; may be desired for supercell/setting invariance.
    symprec, angle_tolerance : float
        spglib tolerances.
    chunk_size : int
        Chunk length for the per-mode accumulation loop. Increase for speed
        if RAM allows; decrease to reduce memory footprint.
    debug : bool
        Print failures or shapes when helpful.

    Returns
    -------
    Callable[[object], str]
        A function `hash_fn(container) -> hex_string` producing a SHA-256 digest.
    """
    TWO_PI = 2.0 * math.pi
    EPS = 1e-12  # small offset to avoid hitting exactly 0/1 after modulo

    # Build / validate reciprocal modes
    if modes is None:
        M = _build_integer_modes_sphere(kmax)
    else:
        M = np.asarray(modes, dtype=np.int32)
        if M.ndim != 2 or M.shape[1] != 3 or M.shape[0] == 0:
            raise ValueError("modes must have shape (M,3) with M>0")
        # Make deterministic: sort lexicographically
        M = M[np.lexsort((M[:, 2], M[:, 1], M[:, 0]))]
    M_T = M.T  # (3, M)
    M_count = int(M.shape[0])

    # Small helpers
    def qint(x: np.ndarray, grid: float) -> np.ndarray:
        """Quantize to integers with stable half-up rule: floor(x/grid + 0.5)."""
        return np.floor(np.asarray(x, float) / grid + 0.5).astype(np.int32, copy=False)

    def hbytes(*chunks: bytes) -> str:
        h = hashlib.sha256()
        for c in chunks:
            h.update(c)
        return h.hexdigest()

    def tsf_hash(container) -> str:
        apm = container.AtomPositionManager

        # 1) Detect periodicity robustly.
        try:
            pbc_flags = getattr(apm, "pbc", None)
            is_nonpbc = isinstance(pbc_flags, (tuple, list)) and not any(pbc_flags)
        except Exception:
            is_nonpbc = False
        if not isinstance(is_nonpbc, bool):
            is_nonpbc = False  # default to periodic unless explicitly non-PBC

        # 2) Basic properties
        Z = np.asarray(apm.get_atomic_numbers(), np.int32)
        N = int(Z.shape[0])
        if N == 0:
            # Empty container → hash a fixed token
            return hbytes(b"TSFv1\0", np.array([0], dtype="<i8").tobytes())

        # 3) Optional global ticks (avoids energy-driven changes by default).
        try:
            E_total = float(getattr(apm, "E", 0.0))
        except Exception:
            E_total = 0.0
        e_tick = -1 if not include_energy else int(math.floor((E_total / N) / e_grid + 0.5))

        # 4) Non-PBC fallback: reuse a fast, centered integer multiset (no neighbors).
        if is_nonpbc:
            X = np.asarray(apm.atomPositions, float)
            Xc = X - X.mean(axis=0)                 # translation invariance
            Xq = qint(Xc, lattice_grid)            # reuse lattice_grid as tol in Å
            K = np.column_stack((Z, Xq)).astype(np.int32)
            Kuniq, counts = np.unique(K, axis=0, return_counts=True)
            meta = np.array([N, e_tick, -1], dtype="<i8").tobytes()
            return hbytes(
                b"TSFv1\0",
                np.zeros((3, 3), dtype="<i4").tobytes(),       # no lattice stored
                np.asarray(Kuniq, dtype="<i4").tobytes(),
                np.asarray(counts, dtype="<i4").tobytes(),
                meta,
            )

        # 5) PBC path: recompute fractionals from current Cartesian + lattice.
        A_cols = np.asarray(apm.latticeVectors, float)   # your APM stores columns a,b,c
        A = A_cols.T                                     # rows (a,b,c) for math
        X = np.asarray(apm.atomPositions, float)         # current Cartesian
        FinvT = np.linalg.inv(A).T
        F = (X @ FinvT + EPS) % 1.0                      # fractional coords ∈ [0,1)

        # Optional: primitive/setting reduction (origin-independent)
        if use_spglib:
            try:
                import spglib
                A_s, F_s, Z_s = spglib.standardize_cell(
                    (A.copy(), F.copy(), Z.copy()),
                    to_primitive=True, no_idealize=True,
                    symprec=symprec, angle_tolerance=angle_tolerance,
                )
                A = np.asarray(A_s, float)
                F = (np.asarray(F_s, float) + EPS) % 1.0
                Z = np.asarray(Z_s, np.int32)
                N = int(Z.shape[0])
            except Exception as exc:
                if debug:
                    print("spglib reduction failed; using unreduced cell:", exc)

        # 6) Prepare species channels (optional but recommended).
        if per_species:
            species, inv = np.unique(Z, return_inverse=True)  # species sorted ascending
            C = int(species.shape[0])
        else:
            species = np.array([0], dtype=np.int32)
            inv = np.zeros(N, dtype=np.int32)
            C = 1

        # 7) Accumulate structure factors S per species and per mode.
        #    S_re, S_im have shape (C, M); we sum in float64 for stability.
        S_re = np.zeros((C, M_count), dtype=np.float64)
        S_im = np.zeros((C, M_count), dtype=np.float64)

        # Chunked accumulation to keep memory bounded: (chunk×3) @ (3×M) = (chunk×M)
        for s in range(0, N, max(1, int(chunk_size))):
            e = min(N, s + chunk_size)
            Fi = F[s:e]               # (chunk, 3)
            inv_i = inv[s:e]          # (chunk,)
            phase = TWO_PI * (Fi @ M_T)     # (chunk, M)
            Ei_re = np.cos(phase)           # (chunk, M)
            Ei_im = np.sin(phase)           # (chunk, M)

            # Accumulate by species using bincount per mode (fast and vectorized).
            # Loop over modes only (typically ~100), not over atoms.
            for m in range(M_count):
                S_re[:, m] += np.bincount(inv_i, weights=Ei_re[:, m], minlength=C)
                S_im[:, m] += np.bincount(inv_i, weights=Ei_im[:, m], minlength=C)

        # 8) Normalize per species to keep the descriptor scale-stable with N.
        Nz = np.bincount(inv, minlength=C).astype(np.float64)  # #atoms per species
        denom = np.sqrt(np.maximum(Nz, 1.0))[:, None]          # (C, 1)
        P = np.hypot(S_re, S_im) / denom                       # (C, M), translation-invariant

        # 9) Quantize magnitudes and lattice; build the byte payload.
        Pq = qint(P, ps_grid)          # (C, M) int32
        A_q = qint(A, lattice_grid)    # (3, 3) int32

        v_tick = -1
        if include_volume:
            vpa = abs(np.linalg.det(A)) / max(N, 1)
            v_tick = int(math.floor(vpa / v_grid + 0.5))

        # Serialize deterministically:
        # [signature][quantized lattice][species IDs][quantized spectrum][meta]
        # meta = [N, #channels, e_tick, v_tick]
        meta = np.array([N, int(species.shape[0]), e_tick, v_tick], dtype="<i8").tobytes()

        return hbytes(
            b"TSFv1\0",
            np.asarray(A_q, dtype="<i4").tobytes(),
            np.asarray(species, dtype="<i4").tobytes(),
            np.asarray(Pq, dtype="<i4").tobytes(),
            meta,
        )

    return tsf_hash

# ------------------------- ROBUST (lattice+KDTree) --------------------------
def _robust_hash_factory(
    *,
    pos_grid: float = 2e-5,
    lat_grid: float = 1e-4,
    e_grid: float = 1e-3,
    v_grid: float = 1e-4,
    include_tree: bool = True,
    symprec: float = 1e-5,
    debug: bool = False,
) -> Callable[[Any], str]:
    """Returns a hashing function bound to the supplied parameters."""

    def _robust_hash(container) -> str:
        apm = container.AtomPositionManager
        apm.wrap()
        lat0 = np.asarray(apm.latticeVectors, float)
        frac0 = np.asarray(apm.atomPositions_fractional, float)
        Z = np.asarray(apm.get_atomic_numbers(), int)

        # Canonical primitive cell where possible
        cell = (lat0.copy(), frac0.copy(), Z.copy())
        try:
            lat, frac, Z = spglib.standardize_cell(
                cell, to_primitive=True, no_idealize=False, symprec=symprec
            )
            frac %= 1.0
        except Exception:  # fall back to niggli then original
            try:
                spglib.niggli_reduce(cell, eps=symprec)
                lat, frac, Z = cell
                frac %= 1.0
            except Exception:
                lat, frac = lat0, frac0

        # Quantise lattice & coords
        lat_q = np.round(lat / lat_grid) * lat_grid
        frac_q = np.round(frac / pos_grid) * pos_grid

        # Sort deterministically
        order = np.lexsort((frac_q[:, 2], frac_q[:, 1], frac_q[:, 0], Z))
        Z = Z[order]
        frac_q = frac_q[order]

        # Energy/volume per atom
        try:
            epa = float(apm.E) / len(Z)
        except Exception:
            epa = 0.0
        epa_q = round(epa / e_grid) * e_grid
        vpa_q = round((abs(np.linalg.det(lat_q)) / len(Z)) / v_grid) * v_grid

        # Fingerprint string
        lat_s = ",".join(f"{x:.8f}" for x in lat_q.flatten())
        coord_s = ";".join(
            f"{Z[i]}:{frac_q[i,0]:.8f},{frac_q[i,1]:.8f},{frac_q[i,2]:.8f}"
            for i in range(len(Z))
        )
        fp = f"{lat_s}|{coord_s}|E{epa_q:.5f}|V{vpa_q:.5f}"

        # Optional KD‑tree serialisation
        if include_tree:
            try:
                apm.kdtree = None
                apm.build_kdtree(verbose=False)
                fp += "|TREE:" + _serialize_kdtree(apm.kdtree)
            except Exception as exc:
                if debug:
                    print("KD‑tree failure:", exc)
                fp += "|TREE:ERROR"
            finally:
                apm.kdtree = None

        return hashlib.sha256(fp.encode()).hexdigest()

    return _robust_hash

# 2. RDF  ────────────────────────────────────────────────────────────────────
def _rdf_hash_factory(
    *,
    r_max: float = 10.0,
    bin_width: float = 0.02,
    density_grid: float = 1e-4,   
    e_grid: float = 1e-2,
    v_grid: float = 1e-2,
    symprec: float = 1e-3,
    debug: bool = False,
) -> Callable[[Any], str]:
    # Precompute bin edges
    edges = np.linspace(0.0, r_max, int(math.ceil(r_max / bin_width)) + 1)
    nbins = len(edges) - 1

    def _rdf_hash(container) -> str:
        apm = container.AtomPositionManager
        apm.wrap()

        n_total = len(apm.get_atomic_numbers())
        # Per-atom energy and (quantised) 
        try:
            epa = float(apm.E) / max(n_total, 1)
        except Exception:
            epa = 0.0
        epa_q = round(epa / e_grid) * e_grid

        # Canonicalise the cell (lattice, fractional coords, atomic numbers)
        lat, frac, Z = _canonical_cell(apm, symprec, debug)
        
        Z = np.asarray(Z, dtype=int)
        N = len(Z)

        # Early exit for a single atom
        if N < 2:
            vpa_q = round(abs(np.linalg.det(lat)) / v_grid / max(N,1)) * v_grid
            fp = f"SINGLE|E{epa_q:.5f}|V{vpa_q:.5f}"
            return hashlib.sha256(fp.encode()).hexdigest()
        # Per-atom volume (quantised) 
        vpa_q = round(abs(np.linalg.det(lat)) / v_grid / N) * v_grid

        # Convert all fractional positions to Cartesian: (N×3) @ (3×3).T → N×3
        cart = frac @ lat.T

        # Build a KD-tree on Cartesian positions
        sr = SingleRun()
        apm_primitive = sr.AtomPositionManager
        apm_primitive.configure(cart, Z, lat)

        tree = apm_primitive.kdtree

        # Prepare RDF histograms
        rdf = defaultdict(lambda: np.zeros(nbins, dtype=np.float64))
        norm = 1.0 / (N * float(N - 1) / 2.0)               # 1 / number of pairs

        # build the KD-tree as before
        #tree = apm_primitive.kdtree

        # 1) one-shot neighbor lists for all atom pairs within r_max
        nbr_lists = tree.query_ball_tree(tree, r_max, p=2.0, eps=0)

        # 2) flatten to unique i<j pairs
        pairs = [(i, j)
                 for i, nbrs in enumerate(nbr_lists)
                 for j in nbrs
                 if j > i]

        # 3)  apm_primitive.distance
        for i, j in pairs:
            d = apm_primitive.distance(cart[i], cart[j])
            bin_idx = int(d // bin_width)
            if bin_idx < nbins:
                a, b = sorted((Z[i], Z[j]))
                key = f"{a}-{b}"
                rdf[key][bin_idx] += norm

        # ── Quantise to fixed-precision densities ──────────────────────────
        parts = []
        for key in sorted(rdf):
            rounded = np.round(rdf[key] / density_grid) * density_grid
            parts.append(f"{key}:{','.join(f'{x:.6f}' for x in rounded)}")
        fp = "|".join(parts) + f"|E{epa_q:.5f}|V{vpa_q:.5f}"

        return hashlib.sha256(fp.encode()).hexdigest()

    return _rdf_hash

def _rdf_hash_factory(
    *,
    r_max: float = 10.0,
    bin_width: float = 0.02,
    density_grid: float = 1e-4,
    e_grid: float = 1e-2,
    v_grid: float = 1e-2,
    symprec: float = 1e-3,
    debug: bool = False,
) -> Callable[[Any], str]:
    # Precompute bin edges once
    edges = np.linspace(0.0, r_max, int(math.ceil(r_max / bin_width)) + 1)
    nbins = len(edges) - 1

    def _bin_index(d: float) -> int:
        """Right-closed binning; excludes exactly d == r_max."""
        idx = np.searchsorted(edges, d, side="right") - 1
        return idx if 0 <= idx < nbins else -1

    def _rdf_hash(container) -> str:
        apm = container.AtomPositionManager

        # Detect PBC early to avoid wrapping clusters
        is_nonpbc = _is_nonperiodic(apm)
        if not is_nonpbc:
            apm.wrap()

        n_total = len(apm.get_atomic_numbers())
        try:
            epa = float(apm.E) / max(n_total, 1)
        except Exception:
            epa = 0.0
        # quantize energy-per-atom
        epa_q = np.floor(epa / e_grid + 0.5) * e_grid

        # Canonicalise the cell/coords/atomic numbers
        lat, frac_or_cart, Z = _canonical_cell(apm, symprec, debug)
        Z = np.asarray(Z, dtype=int)
        N = len(Z)

        # Volume field
        if is_nonpbc or lat is None:
            v_field = "V:NA"
        else:
            vpa = abs(np.linalg.det(lat)) / max(N, 1)
            vpa_q = np.floor(vpa / v_grid + 0.5) * v_grid
            v_field = f"V{vpa_q:.5f}"

        # Trivial cases: N==0 or 1
        if N < 2:
            fp = f"SINGLE|E{epa_q:.5f}|{v_field}"
            return hashlib.sha256(fp.encode()).hexdigest()

        # Cartesian coordinates
        if is_nonpbc or lat is None:
            cart = np.asarray(frac_or_cart, float)
            # optional: center cluster for tree determinism
            cart = cart - cart.mean(axis=0)
        else:
            frac = np.asarray(frac_or_cart, float)
            cart = frac @ lat.T

        # Build RDF histograms (keyed by species pair "a-b")
        from collections import defaultdict
        rdf = defaultdict(lambda: np.zeros(nbins, dtype=np.float64))
        norm = 1.0 / (N * (N - 1) / 2.0)  # normalize by # unique pairs

        if is_nonpbc or lat is None:
            # Pure Euclidean neighbors (no PBC)
            from scipy.spatial import cKDTree
            tree = cKDTree(cart)
            # One-shot neighbor list for all points
            nbr_lists = tree.query_ball_tree(tree, r_max, p=2.0, eps=0.0)
            for i, nbrs in enumerate(nbr_lists):
                for j in nbrs:
                    if j <= i:
                        continue
                    d = float(np.linalg.norm(cart[i] - cart[j]))
                    b = _bin_index(d)
                    if b >= 0:
                        aZ, bZ = sorted((Z[i], Z[j]))
                        rdf[f"{aZ}-{bZ}"][b] += norm
        else:
            # Periodic neighbor discovery (assumes PBC-aware tree & distances)
            sr = SingleRun()
            apm_primitive = sr.AtomPositionManager
            apm_primitive.configure(cart, Z, lat)  # builds periodic kdtree
            tree = apm_primitive.kdtree

            # Loop over each atom i and query neighbours within r_max (Cartesian)
            for i, ri in enumerate(cart):    
                nbrs = tree.query_ball_point(ri, r_max)

                for j in nbrs:
                    if j <= i:
                        continue  # ensure each unordered pair is counted once

                    d = apm_primitive.distance(cart[i], cart[j])  
                    bin_idx = int(d // bin_width)
                    if bin_idx < nbins:
                        pair = tuple(sorted((Z[i], Z[j])))
                        key = f"{pair[0]}-{pair[1]}"
                        rdf[key][bin_idx] += norm
                print
        # Quantize histogram densities and assemble fingerprint
        parts = []
        for key in sorted(rdf):
            rounded = np.floor(rdf[key] / density_grid + 0.5) * density_grid
            parts.append(f"{key}:{','.join(f'{x:.6f}' for x in rounded)}")

        fp = "|".join(parts) + f"|E{epa_q:.5f}|{v_field}"

        return hashlib.sha256(fp.encode()).hexdigest()

    return _rdf_hash

def _pair_distance_hash_factory(
    *,
    quant_grid: float = 1e-3,
    include_volume: bool = True,
    include_energy: bool = True,
    v_grid: float = 1e-2,
    e_grid: float = 1e-3,
    debug: bool = False,
) -> callable:
    """
    Extremely simple, brute-force O(N^2) descriptor:
    - Compute all pairwise interatomic distances (Cartesian).
    - Quantize and sort them.
    - Hash the resulting vector.
    """
    import hashlib, numpy as np, math

    def _pairdist_hash(container) -> str:
        apm = container.AtomPositionManager
        try:
            coords = np.asarray(apm.atomPositions, float)
        except Exception:
            coords = np.asarray(apm.get_atomPositions_cartesian(), float)
        n = len(coords)
        if n < 2:
            return hashlib.sha256(b"empty").hexdigest()

        # Compute all unique pair distances
        diff = coords[:, None, :] - coords[None, :, :]
        dists = np.linalg.norm(diff, axis=-1)
        tril = dists[np.tril_indices(n, k=-1)]
        tril_q = np.floor(tril / quant_grid + 0.5) * quant_grid
        tril_q.sort()

        # Optionally add E/N and V/N ticks
        parts = [f"{x:.4f}" for x in tril_q.tolist()]
        meta = []
        if include_energy:
            E = getattr(apm, "E", 0.0) or 0.0
            meta.append(f"E{E/n/e_grid:.3f}")
        if include_volume:
            try:
                lat = np.asarray(apm.latticeVectors, float)
                V = abs(np.linalg.det(lat))
                meta.append(f"V{V/n/v_grid:.3f}")
            except Exception:
                meta.append("V:NA")

        fp = "|".join(parts + meta)
        return hashlib.sha256(fp.encode()).hexdigest()

    return _pairdist_hash


# 2b ----------------------------- SOAP placeholder ---------------------------
def _soap_hash_factory(*, debug: bool = False, **kw) -> Callable[[Any], str]:
    try:
        from dscribe.descriptors import SOAP  # noqa: F401  (optional)
    except ModuleNotFoundError as exc:
        raise NotImplementedError(
            "SOAP hashing requires `dscribe` – install it or choose another method"
        ) from exc

    # … (Set up descriptor here) …
    def _soap_hash(container) -> str:  # pragma: no cover – stub
        raise NotImplementedError

    return _soap_hash

# 3. RBF (requires get_RBF) ────────────────────────────────────────────────

def _rbf_hash_factory(*, number_of_bins:int=200, bin_volume_normalize:bool=False,
                      number_of_atoms_normalize:bool=False, density_normalize:bool=False,
                      e_grid:float=1e-2, v_grid:float=1e-2, symprec:float=1e-3,
                      debug:bool=False)->Callable[[Any],str]:
    def _rbf_hash(container)->str:
        apm=container.AtomPositionManager;apm.wrap()
        try:
            rbf=apm.get_RBF(number_of_bins=number_of_bins, bin_volume_normalize=bin_volume_normalize,
                             number_of_atoms_normalize=number_of_atoms_normalize, density_normalize=density_normalize)
        except Exception as exc:
            if debug:print("RBF fail",exc);rbf={}
        parts=[]
        for sp1 in sorted(rbf):
            for sp2 in sorted(rbf[sp1]):
                h = np.array(rbf[sp1][sp2], float).ravel()
                hq=np.round(h/symprec)*symprec
                parts.append(f"{sp1}-{sp2}:"+",".join(f"{x:.4f}" for x in hq))
        rbf_s="|".join(parts)
        Z=apm.get_atomic_numbers();N=max(len(Z),1)
        E = getattr(apm, 'E', 0.0)
        if E is None:
            E = 0.0
        epa_q = round(float(E) / N / e_grid) * e_grid
        vpa_q=round(abs(np.linalg.det(apm.latticeVectors))/N/v_grid)*v_grid
        fp=f"{rbf_s}|E{epa_q:.4f}|V{vpa_q:.4f}"
        return hashlib.sha256(fp.encode()).hexdigest()
    return _rbf_hash

# 4. RMSE  ──────────────────────────────────────────────────────────────────
def _rmse_hash_factory(*, symprec:float=1e-3, debug:bool=False)->Callable[[Any],str]:
    def _rmse_hash(container)->str:
        apm=container.AtomPositionManager;apm.wrap()
        lat,frac,Z=_canonical_cell(apm,symprec,debug)
        lat_q=np.round(lat/symprec)*symprec
        frac_q=np.round(frac/symprec)*symprec
        order=np.lexsort((frac_q[:,2],frac_q[:,1],frac_q[:,0],Z))
        E = getattr(apm,'E',0.0)
        E = E if not E is None else 0.0
        vec=np.concatenate((lat_q.flatten(),frac_q[order].flatten(),[round(float(E)/symprec)*symprec]))
        return hashlib.sha256(",".join(f"{x:.6f}" for x in vec).encode()).hexdigest()
    return _rmse_hash

# 5. BASIN (similarity clustering) ─────────────────────────────────────────
class _BasinManager:
    """Per‑composition similarity basins using vector KD‑Tree."""
    def __init__(self, symprec:float=1e-3, tol:float=1e-2, include_E:bool=True):
        self.symprec=symprec;self.tol=tol;self.include_E=include_E
        self._vecs:Dict[str,list[np.ndarray]]={}
        self._trees:Dict[str,cKDTree|None]={}
        self._hashes:Dict[str,list[str]]={}
    def _vector(self, container)->np.ndarray:
        apm=container.AtomPositionManager;apm.wrap()
        lat,frac,Z=_canonical_cell(apm,self.symprec,False)
        lat_q=np.round(lat/self.symprec)*self.symprec
        frac_q=np.round(frac/self.symprec)*self.symprec
        order=np.lexsort((frac_q[:,2],frac_q[:,1],frac_q[:,0],Z))
        vec=np.concatenate((lat_q.flatten(),frac_q[order].flatten()))
        if self.include_E:
            vec=np.append(vec,round(float(getattr(apm,'E',0.0))/self.symprec)*self.symprec)
        return vec
    @staticmethod
    def _hash_from_vec(vec:np.ndarray)->str:
        return hashlib.sha256(vec.tobytes()).hexdigest()
    def add(self, comp_key:str, container)->Tuple[str,bool]:
        vec=self._vector(container)
        # first time this composition?
        if comp_key not in self._vecs:
            self._vecs[comp_key]=[vec]
            self._trees[comp_key]=cKDTree(np.vstack([vec]))
            h=self._hash_from_vec(vec)
            self._hashes[comp_key]=[h]
            return h, True
        tree=self._trees[comp_key]
        dist,idx=tree.query(vec,k=1)
        if dist<=self.tol:
            return self._hashes[comp_key][idx], False
        # new basin
        self._vecs[comp_key].append(vec)
        self._trees[comp_key]=cKDTree(np.vstack(self._vecs[comp_key]))
        h=self._hash_from_vec(vec)
        self._hashes[comp_key].append(h)
        return h, True

# factory returns (basin_manager, function)

def _basin_factory(*, symprec:float=1e-3, tol:float=1e-2, debug:bool=False):
    manager=_BasinManager(symprec,tol)
    def _basin_hash(container, comp_key:str):
        h,_=manager.add(comp_key,container)
        return h
    return manager,_basin_hash

# ============================================================================
#  Public manager class
# ============================================================================
# ------------------------- ROBUST (lattice+KDTree) --------------------------
class Structure_Hash_Map(IHash):
    """Container‑level manager with user‑selectable hashing method."""

    _FACTORIES: Dict[str, Callable[..., Callable[[Any], str]]] = {
        "robust":   _robust_hash_factory,
        "rdf":      _rdf_hash_factory,
        "soap":     _soap_hash_factory,

        "rbf":      _rbf_hash_factory,
        "rmse":     _rmse_hash_factory,
        "tsf":      _structure_factor_hash_factory,
        "tsfr":     _structure_factor_hash_factory_rotinv,
    }
    def __init__(self, method: str = "tsf", **kwargs):
        method = method.lower()
        if method not in self._FACTORIES:
            raise ValueError(f"Unknown hashing method '{method}'.")
            
        # Keep a copy of the factory kwargs for ensemble variants
        self._method = method
        self._factory_kw = dict(kwargs)

        # Base hash function (status quo)
        self._hash_fn = self._FACTORIES[method](**kwargs)
        self._hash_map: Dict[str, set[str]] = {}

    def get_hash(
        self, 
        container: "Structure",            # forward-referenced type alias
        *,
        force_rehash: bool = True,
        ) -> str:
        """
        """
        apm = container.AtomPositionManager
        #apm.metadata = getattr(apm, "metadata", {}) or {}
        # 1.  Group structures by elemental composition
        comp_key = self._composition_key(apm.atomCountDict)

        # 2.  Decide whether a new hash is required
        stored_hash = apm.metadata.get("hash", None)
        hash_ = self._hash_fn(container) if force_rehash or stored_hash is None else stored_hash

        # 3.  Ensure a metadata dict exists and persist the hash
        apm.metadata = getattr(apm, "metadata", {}) or {}
        apm.metadata["hash"] = hash_

        return hash_

    # -------------- public API identical to previous classes ---------------
    def add_structure(
        self,
        container: "Structure",            # forward-referenced type alias
        *,
        force_rehash: bool = True,
    ) -> bool:
        """
        Insert *container* into the internal hash map, optionally forcing a fresh
        hash calculation.

        Parameters
        ----------
        container : Structure
            Object whose ``AtomPositionManager`` exposes
            ``atomCountDict``, ``info_system`` and ``metadata`` attributes.
        force_rehash : bool, optional
            If *True* (default), compute a new hash even when one is already stored
            under ``info_system['hash']``.  If *False*, reuse the stored hash when
            available.

        Returns
        -------
        bool
            ``True``  – the structure was not present and has been added.  
            ``False`` – an identical structure (same hash within the same
            composition bucket) already existed.
        """
        # 1.  Group structures by elemental composition
        comp_key = self._composition_key(apm.atomCountDict)
        
        hash_ = self.get_hash(container=container, force_rehash=force_rehash)

        # 4.  Deduplicate within the composition bucket
        bucket = self._hash_map.setdefault(comp_key, set())
        if hash_ in bucket:
            return False          # already known
        bucket.add(hash_)
        return True

    def already_visited(self, container) -> bool:
        comp_key = self._composition_key(container.AtomPositionManager.atomCountDict)
        if comp_key not in self._hash_map:
            return False
        return self._hash_fn(container) in self._hash_map[comp_key]


    # ---------------------- utility helpers ---------------------------------

    @staticmethod
    def _composition_key(comp: dict) -> str:
        """
        Return a deterministic, reduced-formula key such as 'C1-H1-N1-O2'
        for any integer multiple - e.g. both {'C':2,'H':2,'N':2,'O':4}
        and {'C':6,'H':6,'N':6,'O':12} collapse onto the same key.

        • Counts **must** be non-negative integers.  If you store floats,
          cast/round them beforehand.
        • Element order is alphabetical to keep the key canonical.
        """
        counts = [int(comp[el]) for el in comp]
        g = reduce(gcd, counts) or 1                       # robust gcd
        return "-".join(
            f"{el}{int(comp[el] // g)}"                    # always include ‘1’
            for el in sorted(comp)
        )

    # Alias for backward compatibility
    _comp_key = _composition_key

    def get_num_structures_for_composition(self, comp: dict) -> int:
        return len(self._hash_map.get(self._composition_key(comp), ()))

    def total_compositions(self) -> int:
        return len(self._hash_map)


"""test_structure_hashmap.py
============================
Comprehensive, PEP-8-conformant unit-test suite for the ``Structure_Hash_Map``
framework.

This module exercises **structural**, **numerical** and **API-safety** aspects
of the three hashing back-ends (``robust``, ``rdf``, ``soap`` placeholder).

Key design choices
------------------
* Deterministic RNG (Python + NumPy) → fully reproducible runs.
* One assert per behavioural aspect; multiple variants handled via
  ``subTest`` for granular reporting.
* Class-level constants & helper builders eliminate boiler-plate.
* Type hints + doctrings enable static analysis.
* Ready for ``pytest -q`` or ``python -m unittest -v``.

"""

# ---------------------------------------------------------------------------
# Test‑suite
# ---------------------------------------------------------------------------

class StructureHashMapTests(unittest.TestCase):
    """Invariance, quantisation and API‑robustness tests for ``Structure_Hash_Map``."""

    # -------------------------------------------------------------------
    # Global fixtures (executed once for the entire suite)                
    # -------------------------------------------------------------------
    RNG_PY = random.Random(42)
    RNG_NP = np.random.default_rng(42)

    R_MAX     = 5.0
    BIN_WIDTH = 0.1
    HASH_MAP  = Structure_Hash_Map(method="rdf", r_max=R_MAX, bin_width=BIN_WIDTH)

    # -------------------------------------------------------------------
    # Helpers                                                             
    # -------------------------------------------------------------------
    @staticmethod
    def _single_run(coords: np.ndarray, species: Sequence[str], lattice: np.ndarray) -> SingleRun:
        """Return a configured :class:`SingleRun`."""
        sr = SingleRun()
        sr.AtomPositionManager.configure(coords, species, lattice)
        return sr

    # -------------------------------------------------------------------
    # Invariance tests                                                    
    # -------------------------------------------------------------------
    def test_atom_permutation_invariance(self) -> None:
        """Hash must not depend on the order of ``AtomPositionManager`` rows."""
        for n in (4, 12, 24):
            with self.subTest(n=n):
                lat = np.eye(3)
                coords = self.RNG_NP.random((n, 3))
                species = self.RNG_PY.choices(["H", "He"], k=n)

                h0 = self.HASH_MAP._hash_fn(self._single_run(coords, species, lat))
                perm = self.RNG_NP.permutation(n)
                h1 = self.HASH_MAP._hash_fn(self._single_run(coords[perm], [species[i] for i in perm], lat))
                self.assertEqual(h0, h1)

    def test_translation_invariance(self) -> None:
        """Rigid translations (T‑symmetry) must leave the hash unchanged."""
        n = 16
        lat = np.eye(3) * 12.0
        coords = self.RNG_NP.random((n, 3)) * 12.0
        species = self.RNG_PY.choices(["C", "O"], k=n)
        sr = self._single_run(coords, species, lat)
        self.HASH_MAP.add_structure(sr)

        for vec in self.RNG_NP.uniform(-6.0, 6.0, size=(25, 3)):
            with self.subTest(shift=vec):
                sr.AtomPositionManager.set_atomPositions(coords + vec)
                new = self.HASH_MAP.add_structure(sr)
                self.assertFalse(new)

    def test_supercell_invariance(self) -> None:
        """n×m×p super‑cells must hash to the same digest (P‑symmetry)."""
        lat = np.eye(3) * 5.0
        coords = self.RNG_NP.random((8, 3)) * 5.0
        species = self.RNG_PY.choices(["Na", "Cl"], k=8)
        sr = self._single_run(coords, species, lat)
        self.HASH_MAP.add_structure(sr)

        for factor in ((2, 1, 1), (1, 3, 2), (2, 2, 2)):
            with self.subTest(factor=factor):
                sr.AtomPositionManager.generate_supercell(list(factor))
                new = self.HASH_MAP.add_structure(sr)
                self.assertFalse(new)

    def test_small_perturbation_tolerance(self) -> None:
        """Coordinate noise below the bin/grid resolution should not create new hashes."""
        lat = np.eye(3) * 8.0
        coords = self.RNG_NP.random((32, 3)) * 8.0
        species = self.RNG_PY.choices(["Al", "O"], k=32)
        sr = self._single_run(coords, species, lat)
        self.HASH_MAP.add_structure(sr)

        for _ in range(80):
            delta = self.RNG_NP.normal(scale=5e-7, size=coords.shape)
            with self.subTest(rms=float(np.std(delta))):
                sr.AtomPositionManager.set_atomPositions(coords + delta)
                self.assertFalse(self.HASH_MAP.add_structure(sr))

    # -------------------------------------------------------------------
    # Quantisation & parameter‑sensitivity tests                          
    # -------------------------------------------------------------------
    def test_energy_grid_quantisation(self) -> None:
        """Crossing the *e_grid* boundary must flip the hash."""
        lat = np.eye(3)
        coords = self.RNG_NP.random((6, 3))
        species = ["Si"] * 6
        sr = self._single_run(coords, species, lat)

        base_h = self.HASH_MAP._hash_fn(sr)

        # Energy tweak inside same bucket (default e_grid = 0.01 eV)
        sr.AtomPositionManager.E = 0.005
        self.assertEqual(base_h, self.HASH_MAP._hash_fn(sr))

        # Jump across boundary
        sr.AtomPositionManager.E = 0.12
        self.assertNotEqual(base_h, self.HASH_MAP._hash_fn(sr))

    def test_volume_grid_quantisation(self) -> None:
        """Scaling lattice within *v_grid* keeps the hash; beyond flips it."""
        lat = np.eye(3, dtype=np.float64)
        coords = self.RNG_NP.random((4, 3))
        species = ["Ge"] * 4
        sr = self._single_run(coords, species, lat)
        h_base = self.HASH_MAP._hash_fn(sr)

        # Small isotropic expansion within 1% (default v_grid = 0.01)
        sr.AtomPositionManager.set_latticeVectors(lat * 1.0001)  # within bucket
        self.assertEqual(h_base, self.HASH_MAP._hash_fn(sr))

        # Larger scaling beyond bucket
        sr.AtomPositionManager.set_latticeVectors(lat * 1.05)
        self.assertNotEqual(h_base, self.HASH_MAP._hash_fn(sr))

    def test_bin_width_parameter_sensitivity(self) -> None:
        """Changing *bin_width* parameter should lead to different digests."""
        lat = np.eye(3)
        coords = self.RNG_NP.random((10, 3))
        species = ["Fe"] * 10
        sr = self._single_run(coords, species, lat)

        map_fine = Structure_Hash_Map(method="rdf", r_max=4.0, bin_width=0.05)
        map_coarse = Structure_Hash_Map(method="rdf", r_max=4.0, bin_width=0.20)
        h_fine = map_fine._hash_fn(sr)
        h_coarse = map_coarse._hash_fn(sr)
        self.assertNotEqual(h_fine, h_coarse)

    # -------------------------------------------------------------------
    # Composition‑key tests                                               
    # -------------------------------------------------------------------
    def test_formula_unit_reduction(self) -> None:
        """Different multiples of the same formula must share the same composition key."""
        lat = np.eye(3)
        coords = np.array([[0, 0, 0]])
        counts_small = {"C": 2, "H": 6}
        counts_big   = {"C": 6, "H": 18}

        key_small = self.HASH_MAP._composition_key(counts_small)
        key_big   = self.HASH_MAP._composition_key(counts_big)
        self.assertEqual(key_small, key_big)

    def test_bucket_isolation_by_composition(self) -> None:
        """Structures with different reduced compositions must land in different buckets."""
        lat = np.eye(3)
        coords = self.RNG_NP.random((2, 3))
        sr1 = self._single_run(coords, ["Na", "Cl"], lat)
        sr2 = self._single_run(coords, ["K", "Cl"], lat)

        key1 = self.HASH_MAP._composition_key(sr1.AtomPositionManager.atomCountDict)
        key2 = self.HASH_MAP._composition_key(sr2.AtomPositionManager.atomCountDict)
        self.assertNotEqual(key1, key2)

    # -------------------------------------------------------------------
    # Cross‑method & API robustness tests                                 
    # -------------------------------------------------------------------
    def test_method_variation_produces_distinct_hashes(self) -> None:
        """Same structure hashed via 'robust' and 'rdf' should not collide (by design)."""
        lat = np.eye(3)
        coords = self.RNG_NP.random((5, 3))
        species = ["Mg"] * 5
        sr = self._single_run(coords, species, lat)

        h_rdf = Structure_Hash_Map(method="rdf")._hash_fn(sr)
        h_rob = Structure_Hash_Map(method="robust")._hash_fn(sr)
        self.assertNotEqual(h_rdf, h_rob)

    def test_invalid_method_raises(self) -> None:
        """Requesting an unsupported hashing tag must raise ValueError."""
        with self.assertRaises(ValueError):
            Structure_Hash_Map(method="nonexistent")

    def test_soap_missing_dependency(self) -> None:
        """If DScribe is absent, selecting 'soap' must raise NotImplementedError."""
        # Only meaningful if dscribe unavailable in CI pipeline
        return
        with self.assertRaises(NotImplementedError):
            Structure_Hash_Map(method="soap")

    # -------------------------------------------------------------------
    # Precision-voting tests
    # -------------------------------------------------------------------
    def test_collision_vote_consistency(self):
        lat = np.eye(3)
        coords = self.RNG_NP.random((12, 3))
        species = ["Ni"] * 12
        sr = self._single_run(coords, species, lat)


        m = Structure_Hash_Map(
        method="rdf",
        r_max=4.0,
        bin_width=0.1,
        vote_frac=0.6,
        min_votes=3,
        precision_scales=(0.5, 1.0, 2.0),
        )
        h = m._hash_fn(sr)
        is_dup, agree, total = m.vote_duplicate(sr, expected_hash=h)
        self.assertTrue(is_dup)
        self.assertGreaterEqual(agree, 3)

if __name__ == "__main__":
    unittest.main(verbosity=2)

'''

Benchmarking method: robust
  N=  10 →    0.042 ms per call
  N=  20 →    0.066 ms per call
  N=  40 →    0.130 ms per call
  N=  80 →    0.313 ms per call
  N= 160 →    1.056 ms per call
  N= 320 →    4.058 ms per call
  N= 640 →   14.533 ms per call
  N=1280 →   55.756 ms per call

Benchmarking method: rdf
  N=  10 →    0.135 ms per call
  N=  20 →    0.305 ms per call
  N=  40 →    0.575 ms per call
  N=  80 →    1.232 ms per call
  N= 160 →    3.384 ms per call
  N= 320 →   11.740 ms per call
  N= 640 →   39.291 ms per call
  N=1280 →  142.434 ms per call

Benchmarking method: tsf
  N=  10 →    0.081 ms per call
  N=  20 →    0.092 ms per call
  N=  40 →    0.117 ms per call
  N=  80 →    0.148 ms per call
  N= 160 →    0.167 ms per call
  N= 320 →    0.269 ms per call
  N= 640 →    0.336 ms per call
  N=1280 →   12.114 ms per call

Benchmarking method: pairdist
  N=  10 →    0.297 ms per call
  N=  20 →    1.580 ms per call
  N=  40 →    3.490 ms per call
  N=  80 →   10.834 ms per call
  N= 160 →   41.485 ms per call
  N= 320 →  166.583 ms per call
  N= 640 →  673.209 ms per call
  N=1280 → 2863.432 ms per call

'''