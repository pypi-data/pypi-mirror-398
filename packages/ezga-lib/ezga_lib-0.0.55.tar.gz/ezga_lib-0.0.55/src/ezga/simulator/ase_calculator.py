"""
Constraint-aware MD+Relaxation runner for GA simulations (ASE backend).

This refactored module keeps the original API but organizes the code into
small, testable functions and adds performance-friendly controls.

Pipeline
--------
Stage 0 (optional) : Pre-MD geometry relaxation
Stage 1 (optional) : NVT MD + velocity capture
Stage 1.5 (optional): Vibrational analysis (VDOS/F_vib)
Stage 2 (optional) : Post-MD relaxation

Each stage has its own function and is driven by schedules (built once).
The constraint system (same predicates you use for mutations) is reused
across stages via a consistent adapter.

Additions & Fixes
-----------------
- Fixed predicate logic (selected indices = atoms that *satisfy* predicates).
- Optional pre-MD relaxation with independent controls.
- **Performance knobs**: `log_interval` (disable or reduce printing) and
  `write_interval` (control trajectory I/O frequency).
- Correct DOF accounting for `constraint_action` in vibrational scaling.

Python compatibility
--------------------
- Uses `typing.Union[...]` instead of `|` to support Python < 3.10.
- No dependency on `from __future__ import annotations`.
"""
from __future__ import annotations

import os
import copy
import logging
import time

import numpy as np
from typing import Union, Sequence, Optional, Callable, Tuple, Dict, Any, List

# ASE imports (module-level, imported once)
import ase.io
from ase.units import fs
from ase import Atoms, units
from ase.md.langevin import Langevin
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.optimize import BFGS, FIRE
from ase.filters import FrechetCellFilter
from ase.constraints import FixAtoms, FixCartesian

# Vibrational pipeline (your local module)
from .F_vib import corrected_vdos_and_F_from_velocities as _vib_pipeline
from .F_vib import _VibSampler, _save_vib_outputs_to_folder
from .vib_spectrum import compute_vib_spectrum

# Sella Imports (Reactivity)
try:
    from sella import Sella, IRC
    SELLA_AVAILABLE = True
except ImportError:
    SELLA_AVAILABLE = False

# =============================================================================
# Type Definitions
# =============================================================================
# Format: (Positions, Symbols, Cell, Energy, Metadata)
CalculationResult = Tuple[np.ndarray, List[str], Optional[np.ndarray], float, Dict[str, Any]]

# =============================================================================
# Shared constants
# =============================================================================
INTERPOLATION_PREC = 256

# =============================================================================
# Basic utilities
# =============================================================================

def linear_interpolation(data, N):
    """Generate N linearly interpolated samples from control points.

    If `data` is a scalar or length-1 sequence, returns a constant array of
    length N. If `data` has length M>1, N must be >= M.
    """
    if not isinstance(N, int) or N <= 0:
        raise ValueError("N must be a positive integer.")
    if isinstance(data, (int, float)):
        return np.full(N, float(data))
    try:
        arr = np.asarray(data, dtype=float).flatten()
    except Exception as exc:
        raise ValueError("Data must be numeric.") from exc
    M = arr.size
    if M == 0:
        raise ValueError("Input sequence must contain at least one element.")
    if M == 1:
        return np.full(N, arr[0])
    if N < M:
        raise ValueError(f"N ({N}) must be >= number of points M ({M}).")
    xp = np.arange(M)
    xi = np.linspace(0, M - 1, N)
    return np.interp(xi, xp, arr)


def _to_pred_list(preds: Optional[Sequence[Callable]]) -> list:
    """Normalize predicates to a plain Python list; robust to numpy arrays/single callables."""
    if preds is None:
        return []
    if callable(preds):
        return [preds]
    try:
        return list(preds)
    except TypeError:
        return [preds]

# =============================================================================
# Constraint bridge
# =============================================================================
class _APMAdapter:
    """Minimal adapter exposing the attributes your predicates expect."""

    def __init__(self, symbols, positions, cell, atomic_constraints=None):
        self.atomPositions  = np.asarray(positions, float)
        self.atomLabelsList = np.asarray(symbols, dtype=object)
        _cell = np.asarray(cell, float) if cell is not None else None
        if _cell is None or _cell.shape != (3, 3) or not np.isfinite(_cell).all() or abs(np.linalg.det(_cell)) < 1e-9:
            _cell = np.eye(3, dtype=float)
        self.latticeVectors = _cell
        self.atomicConstraints = (
            np.asarray(atomic_constraints, bool) if atomic_constraints is not None else None
        )
        self.atomCount = len(self.atomPositions)


class _StructAdapter:
    def __init__(self, symbols, positions, cell, atomic_constraints=None):
        self.AtomPositionManager = _APMAdapter(symbols, positions, cell, atomic_constraints)


def _evaluate(idx: int, structure: _StructAdapter, constraints: Sequence[Callable], logic: str = "all") -> bool:
    """Return True if atom `idx` should be **selected** by the constraint predicates.

    - logic='all': intersection — all predicates must return True for selection.
    - logic='any': union — any predicate returning True selects the atom.
    """
    if not constraints:
        return False
    if logic == "all":
        return all(c(idx, structure) for c in constraints)
    if logic == "any":
        return any(c(idx, structure) for c in constraints)
    raise ValueError("logic must be 'all' or 'any'")


def _select_indices_by_constraints(
    symbols,
    positions,
    cell,
    fixed: Optional[Sequence[bool]],
    constraints: Sequence[Callable],
    logic: str = "all",
) -> np.ndarray:
    N = len(symbols)
    adapter = _StructAdapter(symbols=symbols, positions=positions, cell=cell, atomic_constraints=fixed)
    sel = [i for i in range(N) if _evaluate(i, adapter, constraints, logic=logic)]
    return np.asarray(sel, dtype=int)


def _normalize_components(components: Optional[Sequence[Union[int, str]]]) -> Optional[Sequence[int]]:
    if components is None:
        return None
    comp_map = {"x": 0, "y": 1, "z": 2}
    out = []
    for c in components:
        out.append(comp_map[c.lower()] if isinstance(c, str) else int(c))
    if any(c not in (0, 1, 2) for c in out):
        raise ValueError("freeze_components must be a subset of {0,1,2,'x','y','z'}")
    return out


def _build_ase_constraints(atoms, selected: np.ndarray, action: str, freeze_components: Optional[Sequence[int]]):
    """Create ASE constraints (FixAtoms or FixCartesian) from selection & components.

    - action == 'freeze'     : freeze the *selected* DOFs
    - action == 'move_only'  : freeze the complement (non-selected) DOFs
    If `freeze_components` is None -> FixAtoms; else -> FixCartesian(mask).
    """

    N = len(atoms)
    selected = np.unique(selected)
    if action not in ("freeze", "move_only"):
        raise ValueError("constraint_action must be 'freeze' or 'move_only'")

    if freeze_components is None:
        if action == "freeze":
            idx = selected
        else:
            mask = np.ones(N, dtype=bool); mask[selected] = False
            idx = np.where(mask)[0]
        return FixAtoms(indices=list(idx))
    else:
        comps = list(freeze_components)
        mask = np.zeros((N, 3), dtype=bool)
        if action == "freeze":
            mask[np.ix_(selected, comps)] = True
        else:
            comp = np.ones(N, dtype=bool); comp[selected] = False
            idx = np.where(comp)[0]
            mask[np.ix_(idx, comps)] = True
        return FixCartesian(mask=mask)

# =============================================================================
# Structural helpers
# =============================================================================
def _build_atoms(
    symbols: Sequence[str], 
    positions: np.ndarray, 
    cell: Optional[np.ndarray], 
    calculator: object
) -> Tuple[Atoms, bool]:
    """
    Constructs an ASE Atoms object from raw arrays.
    """
    # Validation of Cell / PBC
    if cell is not None:
        pbc = True
        # Sanity check for singular cells
        if abs(np.linalg.det(cell)) < 1e-6:
            pbc = False
            cell = None
    else:
        pbc = False

    atoms = Atoms(symbols=symbols, positions=positions, cell=cell, pbc=pbc)
    
    # Attach calculator if provided
    if calculator is not None:
        atoms.calc = calculator
        
    return atoms, pbc


def _apply_constraints(atoms, selected: np.ndarray, action: str, freeze_components_norm: Optional[Sequence[int]]):
    if selected.size > 0:
        atoms.set_constraint(
            _build_ase_constraints(atoms, selected, action=action, freeze_components=freeze_components_norm)
        )

# =============================================================================
# Scheduling
# =============================================================================

def _build_schedules(nvt_steps, T, fmax, pre_relax_fmax) -> Dict[str, Optional[np.ndarray]]:
    sched = {
        'nvt_steps': linear_interpolation(nvt_steps, INTERPOLATION_PREC) if nvt_steps is not None else None,
        'T':         linear_interpolation(T, INTERPOLATION_PREC) if T is not None else None,
        'fmax':      linear_interpolation(fmax, INTERPOLATION_PREC) if fmax is not None else None,
        'pre_fmax':  linear_interpolation(pre_relax_fmax, INTERPOLATION_PREC) if pre_relax_fmax is not None else None,
    }
    return sched

# =============================================================================
# Stages
# =============================================================================

def _stage_pre_relax(atoms,
                     pbc_flag: bool,
                     idx_sample: int,
                     sched: Dict[str, Optional[np.ndarray]],
                     *,
                     constant_volume: bool,
                     hydrostatic_strain: bool,
                     optimizer: str,
                     steps_max: int,
                     with_constraints: bool) -> None:

    if steps_max < 1:
        return

    pre_sched = sched['pre_fmax']
    if pre_sched is None:
        return
    pre_fmax_act = float(np.asarray(pre_sched, dtype=float)[idx_sample])
    if pre_fmax_act <= 0:
        return

    saved_constraints = atoms.constraints if hasattr(atoms, 'constraints') else None
    if not with_constraints and saved_constraints is not None:
        atoms.set_constraint()  # temporarily remove

    if pbc_flag and not constant_volume:
        ecf0 = FrechetCellFilter(atoms, hydrostatic_strain=hydrostatic_strain,
                                 constant_volume=constant_volume, scalar_pressure=0.0)
    else:
        ecf0 = None

    if optimizer.upper() == 'BFGS':
        opt0 = BFGS(atoms if ecf0 is None else ecf0, logfile=None, maxstep=0.2)
    else:
        opt0 = FIRE(atoms if ecf0 is None else ecf0, logfile=None)
    opt0.run(fmax=pre_fmax_act, steps=steps_max)

    if not with_constraints and saved_constraints is not None:
        atoms.set_constraint(saved_constraints)


def _stage_md_and_collect(atoms,
                          selected: np.ndarray,
                          freeze_components_norm: Optional[Sequence[int]],
                          idx_sample: int,
                          sched: Dict[str, Optional[np.ndarray]],
                          *,
                          md_timestep_fs: float,
                          vib_correction: bool,
                          vib_store_interval: int,
                          vib_min_samples: int,
                          remove_com_drift: bool,
                          mass_weighted_com: bool,
                          output_filename: str,
                          constraint_action: str,
                          log_interval: int,
                          write_interval: int,
                          # --- new vibrational spectrum params ---
                          vib_spectrum: bool = False,
                          vib_spectrum_max_lag: int = None,
                          vib_spectrum_cutoff_cm1: float = 3200.0,
                          vib_spectrum_mode: str = "total") -> Dict[str, Any]:

    corrections: Dict[str, Any] = {}
    nvt_sched = sched['nvt_steps']
    if nvt_sched is None:
        return corrections

    nvt_steps_act = int(np.asarray(nvt_sched, dtype=float)[idx_sample])
    T_sched = sched['T']
    T_K = float(T_sched[idx_sample]) if T_sched is not None else 300.0

    if nvt_steps_act <= 0:
        return corrections

    # Initialize velocities and thermostat
    MaxwellBoltzmannDistribution(atoms, temperature_K=T_K)
    dyn = Langevin(
        atoms=atoms, 
        timestep=md_timestep_fs * fs, 
        temperature_K=T_K, 
        friction=0.001
    )

    # Determine frozen DOFs for F_vib scaling
    N = len(atoms)
    dof_frozen = 0
    if selected.size > 0:
        if freeze_components_norm is None:
            if constraint_action == "freeze":
                dof_frozen = 3 * int(selected.size)
            else:  # move_only -> complement frozen
                dof_frozen = 3 * (N - int(selected.size))
        else:
            comps = len(set(freeze_components_norm))
            if constraint_action == "freeze":
                dof_frozen = comps * int(selected.size)
            else:
                dof_frozen = comps * (N - int(selected.size))

    dof_count = 3 * N - dof_frozen
    if remove_com_drift and N > 0:
        dof_count -= 3  # translational DOFs projected out by the sampler
    dof_count = max(dof_count, 1)

    store_interval = max(int(vib_store_interval), 1)
    n_samples_pred = 1 + (nvt_steps_act + store_interval - 1) // store_interval
    capture = bool(vib_correction or vib_spectrum) and (n_samples_pred >= int(vib_min_samples))

    sampler = None
    if capture:
        sampler = _VibSampler(
            atoms=atoms,
            n_samples_pred=n_samples_pred,
            store_interval=store_interval,
            remove_com=bool(remove_com_drift),
            mass_weighted=bool(mass_weighted_com),
        )
        sampler.attach(dyn)

    # Light progress printing (optional)
    if isinstance(log_interval, int) and log_interval > 0:
        def _printenergy(dynobj, t0):
            a = dynobj.atoms
            ep = a.get_potential_energy() / max(len(a), 1)
            ek = a.get_kinetic_energy() / max(len(a), 1)
            Tinst = ek / (1.5 * units.kB) if len(a) > 0 else 0.0
            print(f"{time.time()-t0:.1f}s | Epot/atom={ep:.3f} eV | T={Tinst:.0f} K | t={dynobj.get_time()/units.fs:.0f} fs",
                  flush=True)
        t0 = time.time()
        dyn.attach(_printenergy, interval=log_interval, dynobj=dyn, t0=t0)

    # Trajectory output (optional)
    if isinstance(write_interval, int) and write_interval > 0:
        dyn.attach(lambda: ase.io.write(output_filename, atoms, format="extxyz", append=True), interval=write_interval)

    # Run MD
    dyn.run(nvt_steps_act)

    # Best-effort: write last frame
    try:
        out_dir = (output_filename and (os.path.dirname(output_filename) or '.')) or '.'
        os.makedirs(out_dir, exist_ok=True)
        ase.io.write(output_filename, atoms, append=True)
    except Exception:
        pass

    # -------------------------
    # Stage 1.5 – F_vib (your existing pipeline)
    # -------------------------
    if vib_correction and sampler is not None:
        vel_flat = sampler.finalize()
        samples_used = int(vel_flat.shape[0])

        if samples_used >= int(vib_min_samples):
            eff_dt_fs = md_timestep_fs * store_interval
            masses = atoms.get_masses() # if remove_com_drift else None

            res = _vib_pipeline(
                vel_flat=vel_flat,
                dt_fs=eff_dt_fs,
                T_K=T_K,
                dof_count=dof_count,
                masses=masses,
                remove_COM=False,
                mass_weighting=True,
                window="hann",
                n_segments=6,
                overlap=0.5,
                notch_bands_THz=None,
                debye_lowf_blend=True,
                debye_fit_fmax_THz=1.5,
                debye_blend_fmax_THz=1.5,
                stats='both',
            )

            corrections.update(dict(res))
            _ = _save_vib_outputs_to_folder(
                corrections=corrections,
                output_path=out_dir
            )

    # -------------------------
    # NEW: Stage 1.6 – VAF spectrum (total / atom / element)
    # -------------------------
    if vib_spectrum and sampler is not None:
        velocities = sampler.get_velocity_series()

        res = compute_vib_spectrum(
            velocities=velocities,
            masses=atoms.get_masses(),
            symbols=atoms.get_chemical_symbols(),
            positions=atoms.get_positions(),
            cell=(atoms.get_cell().array if atoms.get_pbc().any() else None),
            dt_fs=md_timestep_fs * store_interval,
            output_path=out_dir,
            max_lag=vib_spectrum_max_lag,
            freq_cutoff_cm1=vib_spectrum_cutoff_cm1,
            mode=vib_spectrum_mode,
            remove_com=True,
            mass_weighting=True,
        )
        res["data"]['freq_total'] = np.array(res["data"]['freq_total'])
        res["data"]['spec_total'] = np.array(res["data"]['spec_total'])
        mask = (res["data"]['freq_total'] > 900) & (res["data"]['freq_total'] < 1200)
        integral = np.trapz(res["data"]['spec_total'][mask],
                            res["data"]['freq_total'][mask])
        integral = np.sum(res["data"]['spec_total'][mask])
        corrections["integral"] = integral
        #corrections["vib_spectrum"] = res["data"]
        corrections["vib_spectrum_hash"] = res["hash"]
        corrections["vib_spectrum_folder"] = res["folder"]
        
    return corrections


def _stage_post_relax(atoms,
                      pbc_flag: bool,
                      idx_sample: int,
                      sched: Dict[str, Optional[np.ndarray]],
                      *,
                      constant_volume: bool,
                      hydrostatic_strain: bool,
                      optimizer: str,
                      steps_max: int) -> None:

    fmax_sched = sched['fmax']
    if fmax_sched is None:
        return
    fmax_act = float(np.asarray(fmax_sched, dtype=float)[idx_sample])
    if fmax_act <= 0:
        return

    if pbc_flag and not constant_volume:
        ecf = FrechetCellFilter(atoms, hydrostatic_strain=hydrostatic_strain,
                                constant_volume=constant_volume, scalar_pressure=0.0)
    else:
        ecf = None

    if optimizer.upper() == 'BFGS':
        opt = BFGS(atoms if ecf is None else ecf, logfile=None, maxstep=0.2)
    else:
        opt = FIRE(atoms if ecf is None else ecf, logfile=None)
    opt.run(fmax=fmax_act, steps=steps_max)

def _finalize_outputs(atoms, corrections: Optional[Dict[str, Any]] = None) -> CalculationResult:
    """
    Extracts final state arrays and merges metadata for the return payload.
    """
    cell_obj = atoms.get_cell()
    pbc_out = bool(atoms.get_pbc().any())
    has_volume = float(cell_obj.volume) > 1e-12
    cell_out = cell_obj.array if pbc_out and has_volume else None
    E = float(atoms.get_potential_energy())
    corrections = dict(corrections or {})
    corrections["F"] = E + corrections.get('F_vib_eV', 0.0)
    return (
        np.array(atoms.get_positions()),
        np.array(atoms.get_chemical_symbols()),
        np.array(cell_out) if cell_out is not None else None,
        E,
        corrections,
    )

# =============================================================================
# Public factory
# =============================================================================

def ase_calculator(
    calculator: object = None,
    device: str = 'cuda',
    default_dtype: str = 'float32',

    # --- Stage 1: MD / relaxation controls ---
    nvt_steps: Union[int, Sequence[float], None] = None,

    # --- Stage 2: relaxation controls ---
    fmax: Union[float, Sequence[float], None] = 0.05,
    steps_max: int = 100,
    hydrostatic_strain: bool = False,
    constant_volume: bool = True,
    optimizer: str = 'FIRE',

    # --- temperature schedules ---
    T: Union[float, Sequence[float]] = 300.0,
    T_ramp: bool = False,  # reserved for future use
    # --- timestep (fs) for the MD integrator ---
    md_timestep_fs: float = 1.0,

    # --- vibrational correction controls ---
    vib_correction: bool = False,
    vib_store_interval: int = 1,
    vib_min_samples: int = 20,
    remove_com_drift: bool = False,
    mass_weighted_com: bool = True,
    vacf_window: str = "hann",

    # --- logging / IO performance knobs ---
    log_interval: int = 0,          # 0 disables printing; otherwise print every k steps
    write_interval: int = 0,        # trajectory write every k steps; set 0 to disable during MD

    # --- constraint controls ---
    constraint_logic: str = "all",
    constraint_action: str = "freeze",
    freeze_components: Optional[Sequence[Union[int, str]]] = None,
    constraints: Optional[Sequence[Callable]] = None,

    # --- Stage 0: pre-MD relaxation controls ---
    pre_relax_fmax: Union[float, Sequence[float], None] = None,
    pre_relax_steps_max: int = 0,
    pre_relax_optimizer: str = 'FIRE',
    pre_relax_constant_volume: bool = True,
    pre_relax_hydrostatic_strain: bool = False,
    pre_relax_with_constraints: bool = True,

    # --- vibrational spectrum controls ---
    vib_spectrum: bool = False,
    vib_spectrum_max_lag: int = None,
    vib_spectrum_cutoff_cm1: float = 3200.0,
    vib_spectrum_mode: str = "total",   # 'total' | 'atom' | 'element' | 'all'

) -> Callable[..., Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], float, Dict[str, Any]]]:
    """
    Build a `run(...)` callable that executes a constraint-aware pipeline:
    (optional) pre-MD relaxation → (optional) NVT MD with velocity capture →
    (optional) vibrational free-energy analysis → (optional) post-MD relaxation.

    Args:
        calculator (ase.calculators.Calculator | None): ASE calculator attached to
            the Atoms object. If None, the caller must attach one before use.
        nvt_steps (int | Sequence[float] | None): Number of MD steps. If a scalar,
            a constant schedule is used. If a sequence, it is linearly interpolated
            to an internal schedule (length = INTERPOLATION_PREC), and the value at
            the index selected by `sampling_temperature` is used. None disables MD.
        fmax (float | Sequence[float] | None): Target force threshold (eV/Å) for
            the post-MD relaxation (Stage 2). Scalar or scheduled as above.
            None disables post-relaxation.
        steps_max (int): Maximum optimizer steps for the post-MD relaxation.
        hydrostatic_strain (bool): If True and `constant_volume` is False, enables
            hydrostatic strain in the variable-cell optimizer (FrechetCellFilter).
        constant_volume (bool): If False and PBC is valid, enable variable-cell
            relaxation in post-MD relaxation (Stage 2).
        device (str): Reserved for broader framework compatibility; not used by ASE.
        default_dtype (str): Reserved for broader framework compatibility; not used by ASE.
        optimizer (str): Optimizer for post-MD relaxation, 'FIRE' (default) or 'BFGS'.
        T (float | Sequence[float]): MD temperature (K). Scalar or schedule as above.
        T_ramp (bool): Reserved for future use (temperature ramping handled by schedule).
        md_timestep_fs (float): MD integrator timestep in femtoseconds.

        vib_correction (bool): If True, compute vibrational free energy from the MD
            velocities via VACF/VDOS (Welch PSD) after MD.
        vib_store_interval (int): Store one velocity sample every k MD steps.
            Effective sampling dt = k * `md_timestep_fs`.
        vib_min_samples (int): Minimum number of stored samples required to run the
            VDOS pipeline; below this, vibrational corrections are skipped.
        remove_com_drift (bool): Remove center-of-mass velocity before storing
            velocities for VACF/VDOS.
        mass_weighted_com (bool): If True, COM uses masses; otherwise arithmetic mean.
        vacf_window (str): Window type used in VACF/PSD estimation (e.g., "hann").

        log_interval (int): Print MD diagnostics every `log_interval` steps.
            Set 0 to disable printing (default).
        write_interval (int): Write trajectory frames every `write_interval` steps.
            Set 0 to disable per-step writes; the final frame is still attempted.

        constraint_logic (str): 'all' (intersection) or 'any' (union) when combining
            predicate callables to select atoms.
        constraint_action (str): 'freeze' to freeze the selected atoms/components, or
            'move_only' to freeze the complement (all non-selected DOFs).
        freeze_components (Sequence[int | str] | None): Per-atom Cartesian components
            to freeze: any subset of {0,1,2} or {'x','y','z'}. If None, uses FixAtoms;
            otherwise uses FixCartesian with a boolean mask.
        constraints (Sequence[Callable] | None): List of predicate callables
            `(idx, structure) -> bool` used to select atoms. These are applied at the
            factory level and concatenated with those passed to `run(...)`.

        pre_relax_fmax (float | Sequence[float] | None): Target force threshold
            (eV/Å) for an optional pre-MD relaxation (Stage 0). Scalar or schedule
            as above. None disables pre-relaxation.
        pre_relax_steps_max (int): Maximum optimizer steps for pre-MD relaxation.
        pre_relax_optimizer (str): Optimizer for pre-relaxation, 'FIRE' (default) or 'BFGS'.
        pre_relax_constant_volume (bool): If False and PBC is valid, enable
            variable-cell relaxation during pre-relaxation.
        pre_relax_hydrostatic_strain (bool): If True and variable-cell pre-relax is
            enabled, allow hydrostatic strain.
        pre_relax_with_constraints (bool): If True, apply the same ASE constraints
            during pre-relaxation; if False, temporarily relax without constraints
            and restore them for MD/post-relax.

    Returns:
        Callable[..., Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], float, Dict[str, Any]]]:
            A `run(...)` function that executes the configured pipeline for a single
            structure:
                run(symbols, positions, cell, fixed=None, sampling_temperature=0.0,
                    steps_max_=steps_max, output_filename='MD_out.xyz', constraints=None)

            The return values are:
                positions (np.ndarray): Final Cartesian positions (N, 3).
                symbols (np.ndarray): Final chemical symbols (N,).
                cell (np.ndarray | None): Final 3×3 cell if periodic and valid; else None.
                E_pot (float): Final potential energy (eV).
                corrections (dict): Vibrational-analysis outputs if enabled (e.g.,
                    'F_vib_eV') and a convenience key 'F' = E_pot + F_vib_eV (if present).

    Notes:
        * Scheduling: scalar inputs are promoted to constant schedules; sequences are
          linearly interpolated to internal schedules and selected via
          `sampling_temperature ∈ [0,1)`.
        * Constraints: selection is determined by the provided predicates; ASE
          constraints (FixAtoms/FixCartesian) are built once and reused through the
          stages. Factory-level and run-level predicate lists are concatenated.
        * Performance: logging and trajectory I/O are configurable via
          `log_interval` and `write_interval`. The velocity sampling rate is set by
          `vib_store_interval` to control memory/CPU without violating Nyquist for
          the analyzed frequency range.
    """
    freeze_components_norm = _normalize_components(freeze_components)
    factory_constraints = _to_pred_list(constraints)
    sched = _build_schedules(nvt_steps, T, fmax, pre_relax_fmax)

    def run(
        symbols: Union[np.ndarray, Sequence[str]],
        positions: np.ndarray,
        cell: np.ndarray,
        *,
        fixed: np.ndarray = None,
        sampling_temperature: float = 0.0,
        steps_max_: int = steps_max,
        output_filename: str = 'MD_out.xyz',
        constraints: Optional[Sequence[Callable]] = None,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], float, Dict[str, Any]]:
        # Validate inputs
        if not isinstance(symbols, (list, np.ndarray)):
            raise TypeError("`symbols` must be a list or numpy array of strings")
        positions_arr = np.asarray(positions, dtype=float)
        if positions_arr.ndim != 2 or positions_arr.shape[1] != 3:
            raise ValueError("`positions` must be an array of shape (N, 3)")
        cell_arr = None
        if cell is not None:
            try:
                cell_arr = np.asarray(cell, dtype=float)
            except Exception:
                cell_arr = None
        if not isinstance(output_filename, str):
            raise TypeError("`output_filename` must be a string file")

        # Ensure output dir
        out_dir = os.path.dirname(output_filename) or '.'
        os.makedirs(out_dir, exist_ok=True)

        # Build Atoms
        symbols_arr = np.asarray(symbols, dtype=object)
        atoms, pbc_flag = _build_atoms(symbols_arr, positions_arr, cell_arr, calculator)

        # Constraints: combine factory + run-time
        combined_constraints = list(factory_constraints)
        combined_constraints.extend(_to_pred_list(constraints))

        adapter_cell = cell_arr if pbc_flag else np.eye(3, dtype=float)
        if len(combined_constraints) > 0:
            selected = _select_indices_by_constraints(
                symbols_arr, positions_arr, adapter_cell, fixed,
                combined_constraints, logic=constraint_logic
            )
        else:
            selected = np.array([], dtype=int)

        _apply_constraints(atoms, selected, action=constraint_action, freeze_components_norm=freeze_components_norm)

        # Schedule index from sampling_temperature in [0, 1]
        idx_sample = int(min(max(float(sampling_temperature), 0.0) * INTERPOLATION_PREC, INTERPOLATION_PREC - 1))

        # Stage 0: Pre-relax
        _stage_pre_relax(
            atoms, pbc_flag, idx_sample, sched,
            constant_volume=pre_relax_constant_volume,
            hydrostatic_strain=pre_relax_hydrostatic_strain,
            optimizer=pre_relax_optimizer,
            steps_max=pre_relax_steps_max,
            with_constraints=pre_relax_with_constraints,
        )

        # Stage 1 (+ 1.5): MD and vibrational analysis
        corrections = _stage_md_and_collect(
            atoms, selected, freeze_components_norm, idx_sample, sched,
            md_timestep_fs=md_timestep_fs,
            vib_correction=vib_correction,
            vib_store_interval=vib_store_interval,
            vib_min_samples=vib_min_samples,
            remove_com_drift=remove_com_drift,
            mass_weighted_com=mass_weighted_com,
            output_filename=output_filename,
            constraint_action=constraint_action,
            log_interval=log_interval,
            write_interval=write_interval,

            # --- NEW vibrational spectrum controls ---
            vib_spectrum=vib_spectrum,
            vib_spectrum_max_lag=vib_spectrum_max_lag,
            vib_spectrum_cutoff_cm1=vib_spectrum_cutoff_cm1,
            vib_spectrum_mode=vib_spectrum_mode,
        )

        # Stage 2: Post-relax
        _stage_post_relax(
            atoms, pbc_flag, idx_sample, sched,
            constant_volume=constant_volume,
            hydrostatic_strain=hydrostatic_strain,
            optimizer=optimizer,
            steps_max=steps_max_,
        )

        # Outputs
        return _finalize_outputs(atoms, corrections)

    return run
