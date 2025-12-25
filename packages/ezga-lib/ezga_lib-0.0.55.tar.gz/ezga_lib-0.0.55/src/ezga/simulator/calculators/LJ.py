"""
LJMixer: A Numba-accelerated Lennard-Jones Calculator for ASE.

This module provides a calculator that supports multi-species Lennard-Jones
interactions with Periodic Boundary Conditions (PBC). It supports automatic
parameter inference from VdW radii, custom mixing rules, and Numba JIT
compilation for performance.
"""
from __future__ import annotations

import json
import warnings
from typing import Dict, Tuple, Optional, Any, List

import numpy as np
from ase.calculators.calculator import Calculator, all_changes
from ase.geometry import cell_to_cellpar

# Attempt to import ASE data for fallback inference
try:
    from ase.data import atomic_numbers, vdw_radii
    _ASE_DATA_OK = True
except ImportError:
    _ASE_DATA_OK = False
    atomic_numbers = {}
    vdw_radii = {}

# Attempt to import Numba
try:
    from numba import njit, prange
    _NUMBA_OK = True
except ImportError:
    _NUMBA_OK = False
    # Fallback dummy decorator if Numba is missing
    def njit(*args, **kwargs):
        def deco(func):
            return func
        return deco
    # Dummy prange
    prange = range

# -----------------------------------------------------------------------------
# Constants & Defaults
# -----------------------------------------------------------------------------

_SIXTH_ROOT_OF_2 = 1.122462048309373

# Universal Lennard-Jones Parameters (Sigma in Å, Epsilon in eV)
# Sources:
# - Noble Gases: Standard experimental fits.
# - H-Lr: Adapted from Rappe et al., Universal Force Field (UFF), JACS 1992.
#         Converted: sigma = x_i / 2^(1/6); epsilon = D_i * 0.04336 (kcal/mol -> eV).
# - Rf-Og: Extrapolated based on periodic trends (theoretical placeholders).

_DEFAULT_LJ_TABLE: Dict[str, Tuple[float, float]] = {
    # --- Period 1 ---
    "H":  (2.571, 0.0019),  # UFF
    "He": (2.640, 0.0009),  # Exp

    # --- Period 2 ---
    "Li": (2.183, 0.0011), "Be": (2.446, 0.0037),
    "B":  (3.638, 0.0078), "C":  (3.431, 0.0045),
    "N":  (3.261, 0.0030), "O":  (3.118, 0.0026),
    "F":  (2.996, 0.0022), "Ne": (2.800, 0.0031), # Ne Exp

    # --- Period 3 ---
    "Na": (2.658, 0.0013), "Mg": (2.691, 0.0048),
    "Al": (4.009, 0.0219), "Si": (3.826, 0.0174),
    "P":  (3.695, 0.0132), "S":  (3.595, 0.0119),
    "Cl": (3.516, 0.0098), "Ar": (3.405, 0.0103), # Ar Exp

    # --- Period 4 ---
    "K":  (3.396, 0.0015), "Ca": (3.028, 0.0100),
    "Sc": (2.936, 0.0008), "Ti": (2.829, 0.0007), "V":  (2.803, 0.0007),
    "Cr": (2.686, 0.0006), "Mn": (2.637, 0.0006), "Fe": (2.592, 0.0006),
    "Co": (2.557, 0.0006), "Ni": (2.521, 0.0006), "Cu": (3.114, 0.0002),
    "Zn": (2.461, 0.0054),
    "Ga": (3.903, 0.0180), "Ge": (3.813, 0.0165), "As": (3.768, 0.0134),
    "Se": (3.746, 0.0126), "Br": (3.732, 0.0109), "Kr": (3.650, 0.0141), # Kr Exp

    # --- Period 5 ---
    "Rb": (3.665, 0.0017), "Sr": (3.244, 0.0102),
    "Y":  (2.977, 0.0031), "Zr": (2.783, 0.0015), "Nb": (2.821, 0.0026),
    "Mo": (2.716, 0.0024), "Tc": (2.671, 0.0021), "Ru": (2.637, 0.0024),
    "Rh": (2.606, 0.0023), "Pd": (2.580, 0.0021), "Ag": (2.553, 0.0016),
    "Cd": (2.536, 0.0099),
    "In": (3.975, 0.0260), "Sn": (3.913, 0.0246), "Sb": (3.935, 0.0194),
    "Te": (3.980, 0.0173), "I":  (4.009, 0.0152), "Xe": (4.100, 0.0190), # Xe Exp

    # --- Period 6 ---
    "Cs": (4.018, 0.0019), "Ba": (3.296, 0.0158),
    # Lanthanides (La-Lu) - UFF Adapted
    "La": (3.136, 0.0007), "Ce": (3.167, 0.0006), "Pr": (3.208, 0.0004),
    "Nd": (3.235, 0.0004), "Pm": (3.257, 0.0004), "Sm": (3.275, 0.0004),
    "Eu": (3.288, 0.0004), "Gd": (2.986, 0.0004), "Tb": (3.048, 0.0004),
    "Dy": (3.085, 0.0004), "Ho": (3.111, 0.0004), "Er": (3.134, 0.0004),
    "Tm": (3.151, 0.0004), "Yb": (3.165, 0.0004), "Lu": (3.245, 0.0018),
    
    "Hf": (2.798, 0.0031), "Ta": (2.821, 0.0035), "W":  (2.730, 0.0029),
    "Re": (2.630, 0.0031), "Os": (2.775, 0.0016), "Ir": (2.526, 0.0031),
    "Pt": (2.449, 0.0035), "Au": (2.934, 0.0017), "Hg": (2.406, 0.0167),
    "Tl": (3.871, 0.0295), "Pb": (3.829, 0.0285), "Bi": (3.893, 0.0225),
    "Po": (4.195, 0.0142), "At": (4.230, 0.0125), "Rn": (4.300, 0.0210),

    # --- Period 7 ---
    "Fr": (4.350, 0.0020), "Ra": (3.600, 0.0160),
    # Actinides (Ac-Lr) - UFF Adapted
    "Ac": (3.090, 0.0014), "Th": (3.029, 0.0011), "Pa": (3.056, 0.0010),
    "U":  (3.018, 0.0009), "Np": (2.986, 0.0009), "Pu": (2.964, 0.0007),
    "Am": (2.942, 0.0006), "Cm": (2.906, 0.0006), "Bk": (2.933, 0.0006),
    "Cf": (2.951, 0.0006), "Es": (2.964, 0.0006), "Fm": (2.973, 0.0006),
    "Md": (2.977, 0.0006), "No": (2.982, 0.0006), "Lr": (2.986, 0.0006),

    # --- Transactinides (Rf-Og) ---
    # Theoretical extrapolation (Trend: size increases, eps roughly constant/decreases for metals)
    "Rf": (3.000, 0.0030), "Db": (3.020, 0.0034), "Sg": (2.950, 0.0030),
    "Bh": (2.850, 0.0030), "Hs": (2.950, 0.0020), "Mt": (2.700, 0.0030),
    "Ds": (2.600, 0.0035), "Rg": (3.100, 0.0020), "Cn": (2.600, 0.0170),
    "Nh": (4.000, 0.0300), "Fl": (3.950, 0.0290), "Mc": (4.000, 0.0230),
    "Lv": (4.300, 0.0150), "Ts": (4.400, 0.0130), "Og": (4.500, 0.0220),
}

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _infer_sigma_from_vdw(r_vdw: float) -> float:
    """Calculates LJ sigma from VdW radius assuming r_min = 2 * r_vdw."""
    return (2.0 * r_vdw) / _SIXTH_ROOT_OF_2

def _infer_eps_from_size(r_vdw: float, eps0: float) -> float:
    """Scales epsilon based on atom size (heuristic)."""
    scale = (r_vdw / 1.5) ** 2
    return max(1e-6, eps0 * scale)

def _get_vdw_radius(symbol: str) -> float:
    """Retrieves VdW radius from ASE data or returns default."""
    if not _ASE_DATA_OK:
        return 1.7
    z = atomic_numbers.get(symbol, 0)
    return float(vdw_radii.get(z, 1.7))

def _mix_lorentz_berthelot(p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
    """Arithmetic mean for Sigma, Geometric mean for Epsilon."""
    sigma = 0.5 * (p1[0] + p2[0])
    eps = np.sqrt(p1[1] * p2[1])
    return sigma, float(eps)

def _mix_geometric(p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
    """Geometric mean for both Sigma and Epsilon."""
    sigma = np.sqrt(p1[0] * p2[0])
    eps = np.sqrt(p1[1] * p2[1])
    return sigma, float(eps)

# -----------------------------------------------------------------------------
# Numba Kernels
# -----------------------------------------------------------------------------

@njit(fastmath=True, cache=True)
def _lj_kernel_orthogonal(positions, types, sigma_mat, eps_mat,
                          rc2, shift_e_mat, cell_diag):
    """
    Optimized Numba kernel for Orthogonal Cells (Rectangular boxes).
    
    Avoids matrix multiplication for Minimum Image Convention.
    """
    n = positions.shape[0]
    forces = np.zeros((n, 3), dtype=np.float64)
    virial = np.zeros((3, 3), dtype=np.float64)
    energy = 0.0
    r2_min = 0.01  # Guard against division by zero

    # Unpack cell dimensions
    Lx, Ly, Lz = cell_diag[0], cell_diag[1], cell_diag[2]
    inv_Lx, inv_Ly, inv_Lz = 1.0/Lx, 1.0/Ly, 1.0/Lz

    for i in range(n - 1):
        ri0, ri1, ri2 = positions[i, 0], positions[i, 1], positions[i, 2]
        ti = types[i]
        
        for j in range(i + 1, n):
            dx = ri0 - positions[j, 0]
            dy = ri1 - positions[j, 1]
            dz = ri2 - positions[j, 2]

            # Fast Minimum Image Convention for Orthogonal Box
            dx -= Lx * round(dx * inv_Lx)
            dy -= Ly * round(dy * inv_Ly)
            dz -= Lz * round(dz * inv_Lz)

            r2 = dx*dx + dy*dy + dz*dz

            if r2 < r2_min: 
                continue # Skip overlaps
            if rc2 > 0.0 and r2 > rc2:
                continue # Cutoff

            tj = types[j]
            sigma = sigma_mat[ti, tj]
            eps = eps_mat[ti, tj]

            sr2  = (sigma * sigma) / r2
            sr6  = sr2 * sr2 * sr2
            sr12 = sr6 * sr6

            # Energy
            e_ij = 4.0 * eps * (sr12 - sr6) - shift_e_mat[ti, tj]
            energy += e_ij

            # Forces (F = -dV/dr)
            # coef = -(1/r) * dV/dr
            coef = 24.0 * eps * (2.0 * sr12 - sr6) / r2
            
            fx = coef * dx
            fy = coef * dy
            fz = coef * dz

            forces[i, 0] += fx; forces[i, 1] += fy; forces[i, 2] += fz
            forces[j, 0] -= fx; forces[j, 1] -= fy; forces[j, 2] -= fz

            # Virial (Standard definition: Sum r_ij * f_ij)
            virial[0, 0] += dx * fx
            virial[1, 1] += dy * fy
            virial[2, 2] += dz * fz
            # Off-diagonals (usually 0 in pure avg, but calculated for instantaneous)
            virial[0, 1] += dx * fy
            virial[0, 2] += dx * fz
            virial[1, 2] += dy * fz

    # Symmetrize virial for off-diagonals
    virial[1, 0] = virial[0, 1]
    virial[2, 0] = virial[0, 2]
    virial[2, 1] = virial[1, 2]

    return energy, forces, virial


@njit(fastmath=True, cache=True)
def _lj_kernel_triclinic(positions, types, sigma_mat, eps_mat,
                         rc2, shift_e_mat, cell, inv_cell):
    """
    General Numba kernel for Triclinic (Non-Orthogonal) Cells.
    
    Uses fractional coordinates for Minimum Image Convention.
    """
    n = positions.shape[0]
    forces = np.zeros((n, 3), dtype=np.float64)
    virial = np.zeros((3, 3), dtype=np.float64)
    energy = 0.0
    r2_min = 0.01

    for i in range(n - 1):
        ti = types[i]
        for j in range(i + 1, n):
            # 1. Calculate distance vector
            rij_vec = positions[i] - positions[j]

            # 2. Minimum Image Convention (General)
            # Convert to fractional, round to nearest integer, convert back
            s = inv_cell @ rij_vec
            s_rounded = np.empty(3, dtype=np.float64)
            s_rounded[0] = round(s[0])
            s_rounded[1] = round(s[1])
            s_rounded[2] = round(s[2])
            
            rij_vec -= cell @ s_rounded

            r2 = np.dot(rij_vec, rij_vec)

            if r2 < r2_min: continue
            if rc2 > 0.0 and r2 > rc2: continue

            tj = types[j]
            sigma = sigma_mat[ti, tj]
            eps = eps_mat[ti, tj]

            sr2  = (sigma * sigma) / r2
            sr6  = sr2 * sr2 * sr2
            sr12 = sr6 * sr6

            e_ij = 4.0 * eps * (sr12 - sr6) - shift_e_mat[ti, tj]
            energy += e_ij

            coef = 24.0 * eps * (2.0 * sr12 - sr6) / r2
            f_vec = coef * rij_vec

            # Update Forces
            forces[i] += f_vec
            forces[j] -= f_vec

            # Update Virial (Outer product)
            # Manual unroll for speed
            virial[0,0] += rij_vec[0]*f_vec[0]; virial[0,1] += rij_vec[0]*f_vec[1]; virial[0,2] += rij_vec[0]*f_vec[2]
            virial[1,0] += rij_vec[1]*f_vec[0]; virial[1,1] += rij_vec[1]*f_vec[1]; virial[1,2] += rij_vec[1]*f_vec[2]
            virial[2,0] += rij_vec[2]*f_vec[0]; virial[2,1] += rij_vec[2]*f_vec[1]; virial[2,2] += rij_vec[2]*f_vec[2]

    return energy, forces, virial

# -----------------------------------------------------------------------------
# Main Class
# -----------------------------------------------------------------------------

class LJMixer(Calculator):
    """
    A Numba-accelerated Lennard-Jones calculator for ASE with automatic mixing.

    This calculator computes Energy, Forces, and Stress using the standard
    12-6 Lennard-Jones potential. It supports arbitrary combinations of elements
    via a lookup table or VdW radii inference.

    Potential Form:
        V(r) = 4 * epsilon * [ (sigma/r)^12 - (sigma/r)^6 ]

    Attributes:
        results (dict): Dictionary storing calculated 'energy', 'forces', 'stress'.
        implemented_properties (list): ['energy', 'forces', 'stress']

    Args:
        species_params (dict, optional): Manual parameters per element.
            Format: `{'Na': {'sigma': 3.0, 'epsilon': 0.01}}`.
        pair_params (dict, optional): Manual parameters for specific pairs.
            Format: `{'Na-Cl': {'sigma': 3.5, 'epsilon': 0.1}}`.
        rc (float, optional): Cutoff radius in Angstroms. If None, infinite cutoff (all pairs).
        shift (bool): If True, shifts the potential energy to 0 at the cutoff radius.
            Default is True.
        eps0 (float): Default epsilon (eV) used when inferring parameters from size.
            Default is 0.010 eV.
        inference_mode (str): Strategy to determine unknown parameters.
            - "auto": Check table first, then fallback to VdW inference.
            - "table": Only use the built-in dictionary.
            - "vdw": Ignore table, calculate everything from ASE VdW radii.
        combination_rule (str): Rule to mix parameters for unlike atoms.
            - "LB": Lorentz-Berthelot (Arithmetic sigma, Geometric epsilon).
            - "geometric": Geometric mean for both sigma and epsilon.
        dump_params_to (str, optional): Filename to dump the final resolved parameters
            to a JSON file for inspection.
    """

    implemented_properties = ["energy", "forces", "stress"]

    def __init__(self,
                 species_params: Optional[Dict[str, Dict[str, float]]] = None,
                 pair_params: Optional[Dict[str, Dict[str, float]]] = None,
                 rc: Optional[float] = None,
                 shift: bool = True,
                 eps0: float = 0.010,
                 inference_mode: str = "auto",
                 combination_rule: str = "LB",
                 dump_params_to: Optional[str] = None,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.species_params = species_params or {}
        self.pair_params = pair_params or {}
        self.rc = rc
        self.shift = shift
        self.eps0 = eps0
        self.inference_mode = inference_mode
        self.combination_rule = combination_rule
        self.dump_params_to = dump_params_to

        if not _NUMBA_OK:
            warnings.warn("Numba not found. Falling back to slow Python loops. "
                          "Install numba (`pip install numba`) for performance.")

    def _resolve_per_element(self, symbols: List[str]) -> Dict[str, Tuple[float, float]]:
        """Resolves Sigma and Epsilon for every unique element in the system."""
        uniq = sorted(set(symbols))
        resolved: Dict[str, Tuple[float, float]] = {}

        for s in uniq:
            # 1. Check user-provided overrides
            if s in self.species_params:
                sp = self.species_params[s]
                resolved[s] = (float(sp["sigma"]), float(sp["epsilon"]))
                continue

            # 2. Strategy Logic
            in_table = s in _DEFAULT_LJ_TABLE
            
            use_table = False
            if self.inference_mode == "table":
                use_table = True
            elif self.inference_mode == "auto" and in_table:
                use_table = True
            
            if use_table and in_table:
                resolved[s] = _DEFAULT_LJ_TABLE[s]
            else:
                # Fallback to VdW inference
                r = _get_vdw_radius(s)
                sig = _infer_sigma_from_vdw(r)
                eps = _infer_eps_from_size(r, self.eps0)
                resolved[s] = (sig, eps)
        
        return resolved

    def calculate(self, atoms=None, properties=('energy',), system_changes=all_changes):
        """
        Main calculation method called by ASE.
        """
        super().calculate(atoms, properties, system_changes)
        
        # 1. Prepare Data
        positions = self.atoms.get_positions().astype(np.float64, copy=False)
        symbols = self.atoms.get_chemical_symbols()
        cell = self.atoms.get_cell().array.astype(np.float64)
        
        # Check volume to prevent errors in non-periodic systems or vacuum
        volume = abs(np.linalg.det(cell))
        if volume < 1e-10:
            # Handle non-periodic case roughly or warn
            # For simplicity, we assume PBC is always intended if using this calc
            pass 

        # 2. Resolve Parameters
        per_elem = self._resolve_per_element(symbols)
        
        # Optional: Dump parameters
        if self.dump_params_to:
            self._dump_parameters(per_elem)

        # 3. Build Interaction Matrices
        uniq = sorted(set(symbols))
        idx_map = {s: i for i, s in enumerate(uniq)}
        types = np.array([idx_map[s] for s in symbols], dtype=np.int64)
        m = len(uniq)

        sigma_mat = np.zeros((m, m), dtype=np.float64)
        eps_mat = np.zeros((m, m), dtype=np.float64)

        # Select mixing function
        mixer = _mix_geometric if self.combination_rule == "geometric" else _mix_lorentz_berthelot

        for i, si in enumerate(uniq):
            for j, sj in enumerate(uniq):
                # Check specific pair overrides first
                key1, key2 = f"{si}-{sj}", f"{sj}-{si}"
                if key1 in self.pair_params:
                    p = self.pair_params[key1]
                    sij, eij = float(p["sigma"]), float(p["epsilon"])
                elif key2 in self.pair_params:
                    p = self.pair_params[key2]
                    sij, eij = float(p["sigma"]), float(p["epsilon"])
                else:
                    sij, eij = mixer(per_elem[si], per_elem[sj])
                
                sigma_mat[i, j] = sij
                eps_mat[i, j] = eij
        
        # 4. Handle Cutoff
        if self.rc is None:
            rc2 = -1.0
            shift_e_mat = np.zeros_like(eps_mat)
        else:
            rc2 = float(self.rc) ** 2
            if self.shift:
                sr2c = (sigma_mat**2) / rc2
                sr6c = sr2c**3
                sr12c = sr6c**2
                shift_e_mat = 4.0 * eps_mat * (sr12c - sr6c)
            else:
                shift_e_mat = np.zeros_like(eps_mat)

        # 5. Run Numba Kernel
        # Check if cell is orthogonal (angles == 90) to use fast path
        # ASE cellpar returns [a, b, c, alpha, beta, gamma]
        cellpar = cell_to_cellpar(cell)
        is_orthogonal = np.allclose(cellpar[3:], 90.0)

        if is_orthogonal:
            cell_diag = np.array([cellpar[0], cellpar[1], cellpar[2]], dtype=np.float64)
            energy, forces, virial = _lj_kernel_orthogonal(
                positions, types, sigma_mat, eps_mat, rc2, shift_e_mat, cell_diag
            )
        else:
            inv_cell = np.linalg.inv(cell)
            energy, forces, virial = _lj_kernel_triclinic(
                positions, types, sigma_mat, eps_mat, rc2, shift_e_mat, cell, inv_cell
            )

        # 6. Store Results
        self.results["energy"] = float(energy)
        self.results["forces"] = forces

        # Convert Virial to Stress
        # ASE definition: Stress = - (Virial + Kinetic) / Volume (Voigt order)
        # We only compute configuration virial here.
        if volume > 1e-12:
            stress_tensor = -virial / volume
            # Convert 3x3 tensor to Voigt [xx, yy, zz, yz, xz, xy]
            self.results["stress"] = np.array([
                stress_tensor[0, 0],
                stress_tensor[1, 1],
                stress_tensor[2, 2],
                stress_tensor[1, 2],
                stress_tensor[0, 2],
                stress_tensor[0, 1]
            ])
        else:
            self.results["stress"] = np.zeros(6)

    def _dump_parameters(self, per_elem: Dict):
        """Writes resolved parameters to JSON."""
        try:
            with open(self.dump_params_to, 'w', encoding='utf-8') as f:
                data = {k: {"sigma": v[0], "epsilon": v[1]} for k, v in per_elem.items()}
                json.dump(data, f, indent=2)
        except IOError as e:
            warnings.warn(f"Could not dump parameters: {e}")

# Factory for configuration systems
def lj_mixer(**kwargs) -> LJMixer:
    """Factory function to instantiate LJMixer."""
    return LJMixer(**kwargs)