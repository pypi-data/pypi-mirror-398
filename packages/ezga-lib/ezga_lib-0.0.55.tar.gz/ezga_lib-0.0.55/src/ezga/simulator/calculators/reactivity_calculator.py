"""Factory module for reactivity exploration calculators in EZGA.

This module provides a specialized factory function to generate calculator
instances capable of exploring potential energy surfaces (PES). It automates
the workflow of optimizing a starting structure, finding Transition States (TS)
via stochastic perturbations, and tracing reaction paths to connected minima.

UPDATED: Now includes advanced constraint handling (predicates, freeze/move_only, 
component locking) identical to the MD pipeline.

Typical usage example:

    from ezga.simulator.calculators.reactivity_calculator import reactivity_calculator

    # Define a predicate to freeze slab atoms
    def freeze_slab(i, s):
        return s.atomPositions[i, 2] < 5.0

    calc_func = reactivity_calculator(
        calculator_factory=EMT(),
        constraints=[freeze_slab],
        constraint_action="freeze",
        num_perturbations=10
    )
"""

from __future__ import annotations

import copy
import logging
import warnings
import os
import uuid
import numpy as np
from typing import Union, Sequence, Optional, Callable, Tuple, Dict, Any, List

import ase.io
from ase import Atoms
from ase.constraints import FixAtoms, FixCartesian
from ase.optimize import FIRE

try:
    from sella import Sella, IRC
    SELLA_AVAILABLE = True
except ImportError:
    SELLA_AVAILABLE = False

# Configure module-level logger
logger = logging.getLogger(__name__)

# Type alias for the standard return format expected by the EZGA Simulator
CalcResult = Tuple[
    np.ndarray,         # Positions
    List[str],          # Symbols
    Optional[np.ndarray], # Cell
    float,              # Energy
    Dict[str, Any]      # Metadata
]

# =============================================================================
# Constraint Helper Functions (Ported from MD Module)
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

def _to_pred_list(preds: Optional[Sequence[Callable]]) -> list:
    """Normalize predicates to a plain Python list."""
    if preds is None:
        return []
    if callable(preds):
        return [preds]
    try:
        return list(preds)
    except TypeError:
        return [preds]

def _evaluate(idx: int, structure: _StructAdapter, constraints: Sequence[Callable], logic: str = "all") -> bool:
    """Return True if atom `idx` should be **selected** by the constraint predicates."""
    if not constraints:
        return False
    if logic == "all":
        return all(c(idx, structure) for c in constraints)
    if logic == "any":
        return any(c(idx, structure) for c in constraints)
    raise ValueError("logic must be 'all' or 'any'")

def _select_indices_by_constraints(
    symbols, positions, cell, fixed: Optional[Sequence[bool]],
    constraints: Sequence[Callable], logic: str = "all",
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

def _build_ase_constraints(
    atoms: Atoms, 
    selected: np.ndarray, 
    action: str, 
    freeze_components: Optional[Sequence[int]]
) -> Tuple[Optional[Union[FixAtoms, FixCartesian]], np.ndarray]:
    """
    Creates the ASE constraint object AND a boolean mask for noise generation.
    
    Returns:
        (ConstraintObject, BooleanMask)
        BooleanMask is (N, 3) where True means "Frozen".
    """
    N = len(atoms)
    selected = np.unique(selected) if selected.size > 0 else np.array([], dtype=int)
    
    if action not in ("freeze", "move_only"):
        raise ValueError("constraint_action must be 'freeze' or 'move_only'")

    # Determine which atoms are affected
    if action == "freeze":
        target_indices = selected
    else: # move_only -> freeze complement
        mask_all = np.ones(N, dtype=bool)
        mask_all[selected] = False
        target_indices = np.where(mask_all)[0]

    # Create the full (N, 3) frozen mask for noise application
    noise_mask = np.zeros((N, 3), dtype=bool)
    
    if freeze_components is None:
        # Full atom freeze
        if len(target_indices) > 0:
            noise_mask[target_indices, :] = True
            return FixAtoms(indices=target_indices), noise_mask
        else:
            return None, noise_mask
    else:
        # Cartesian component freeze
        comps = list(freeze_components)
        if len(target_indices) > 0:
            noise_mask[np.ix_(target_indices, comps)] = True
            return FixCartesian(mask=noise_mask), noise_mask
        else:
            return None, noise_mask

# =============================================================================
# Core Functionality
# =============================================================================

def _build_atoms_obj(
    symbols: Sequence[str],
    positions: np.ndarray,
    cell: Optional[np.ndarray],
    calculator_factory: Union[Callable[[], object], object]
) -> Atoms:
    pbc = False
    if cell is not None:
        if np.abs(np.linalg.det(cell)) > 1e-6:
            pbc = True
        else:
            cell = None

    atoms = Atoms(symbols=symbols, positions=positions, cell=cell, pbc=pbc)

    if calculator_factory:
        if callable(calculator_factory):
            atoms.calc = calculator_factory()
        elif hasattr(calculator_factory, 'copy'):
            atoms.calc = calculator_factory.copy()
        else:
            atoms.calc = copy.deepcopy(calculator_factory)
    return atoms


def _package_result(atoms: Atoms, metadata: Dict[str, Any]) -> CalcResult:
    try:
        energy = float(atoms.get_potential_energy())
    except Exception:
        energy = float('nan')

    cell = np.array(atoms.get_cell()) if atoms.pbc.any() else None
    clean_meta = copy.deepcopy(metadata)

    return (
        np.array(atoms.get_positions()),
        atoms.get_chemical_symbols(),
        cell,
        energy,
        clean_meta
    )


def _save_trajectory(atoms_list: List[Atoms], filename: str) -> None:
    if not atoms_list:
        return
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        ase.io.write(filename, atoms_list)
    except Exception as e:
        logger.warning("Failed to save trajectory to %s: %s", filename, e)


# =============================================================================
# Reactivity Calculator Factory
# =============================================================================

def reactivity_calculator(
    calculator_factory: Union[Callable[[], object], object],
    
    # --- Optimization / Exploration Params ---
    root_fmax: float = 0.02,
    num_perturbations: int = 5,
    perturbation_scale: float = 0.15,
    ts_fmax: float = 0.05,
    ts_steps: int = 500,
    sella_order: int = 1,
    run_irc: bool = True,
    irc_fmax: float = 0.05,
    final_relax_fmax: float = 0.01,
    write_trajectories: bool = True,
    
    # --- Constraint Params (New) ---
    constraint_logic: str = "all",
    constraint_action: str = "freeze",
    freeze_components: Optional[Sequence[Union[int, str]]] = None,
    constraints: Optional[Sequence[Callable]] = None

) -> Callable[..., List[CalcResult]]:
    """Builds a callable for reactivity exploration with advanced constraints.

    Args:
        calculator_factory: ASE calculator instance or factory function.
        root_fmax: Force threshold for initial root optimization.
        num_perturbations: Number of stochastic attempts to find TS.
        perturbation_scale: Scale of Gaussian noise for kicks (Angstrom).
        ts_fmax: Force threshold for Sella TS optimization.
        ts_steps: Max steps for Sella.
        run_irc: Whether to run Intrinsic Reaction Coordinate descent.
        
        constraint_logic: 'all' (intersection) or 'any' (union) for predicates.
        constraint_action: 'freeze' selected atoms, or 'move_only' (freeze others).
        freeze_components: Subset of {0,1,2} or {'x','y','z'} to freeze.
        constraints: List of predicate functions `(idx, struct) -> bool`.

    Returns:
        A callable `run(...)` compatible with EZGA Simulator.
    """
    if not SELLA_AVAILABLE:
        raise ImportError("The 'sella' package is required.")

    # Pre-process static constraint settings
    freeze_components_norm = _normalize_components(freeze_components)
    factory_constraints = _to_pred_list(constraints)

    def run(
        symbols: Sequence[str],
        positions: np.ndarray,
        cell: Optional[np.ndarray],
        fixed: Optional[np.ndarray] = None,
        parent_hash: str = "root",
        output_filename: str = "trajectories",
        constraints: Optional[Sequence[Callable]] = None,  # Runtime constraints
        **kwargs
    ) -> List[CalcResult]:
        
        discovered_structures: List[CalcResult] = []

        # ---------------------------------------------------------------------
        # 1. Setup Root Structure & Constraints
        # ---------------------------------------------------------------------
        root = _build_atoms_obj(symbols, positions, cell, calculator_factory)

        # Combine constraints (Factory + Runtime)
        combined_constraints = list(factory_constraints)
        combined_constraints.extend(_to_pred_list(constraints))

        # Determine Selection Indices
        adapter_cell = cell if cell is not None else np.eye(3)
        if len(combined_constraints) > 0:
            selected_indices = _select_indices_by_constraints(
                symbols, positions, adapter_cell, fixed,
                combined_constraints, logic=constraint_logic
            )
        else:
            # If explicit 'fixed' mask is passed but no predicates, support legacy behavior
            if fixed is not None and np.any(fixed):
                # Map boolean mask to indices, treat as 'freeze' action
                selected_indices = np.where(np.asarray(fixed).flatten())[0]
            else:
                selected_indices = np.array([], dtype=int)

        # Build the ASE Constraint Object and the Noise Mask
        ase_cons, noise_mask = _build_ase_constraints(
            root, selected_indices, 
            action=constraint_action, 
            freeze_components=freeze_components_norm
        )

        if ase_cons is not None:
            root.set_constraint(ase_cons)

        # Optimize Root
        try:
            opt = FIRE(root, logfile=None)
            opt.run(fmax=root_fmax, steps=100)
        except Exception:
            pass
        
        discovered_structures.append(_package_result(
            root, {"type": "initial_state", "hash": parent_hash}
        ))

        # Check system size for Sella internal coordinates
        if len(root) < 2:
            return discovered_structures
        use_internal = len(root) >= 4

        # ---------------------------------------------------------------------
        # 2. Exploration Loop
        # ---------------------------------------------------------------------
        for i in range(num_perturbations):
            
            path_up: List[Atoms] = []
            
            # --- A. Perturbation ---
            candidate = root.copy()
            candidate.calc = _build_atoms_obj(symbols, positions, cell, calculator_factory).calc
            # Constraints are preserved by copy(), but we ensure it explicitly if needed
            if ase_cons:
                candidate.set_constraint(ase_cons)
            
            # Apply Gaussian noise
            pos = candidate.get_positions()
            noise = np.random.normal(0, perturbation_scale, pos.shape)
            
            # Zero out noise on frozen DOFs using the calculated mask
            # noise_mask is (N, 3) boolean where True = Frozen
            noise[noise_mask] = 0.0
            
            candidate.set_positions(pos + noise)

            # Soft Pre-relaxation
            try:
                pre = FIRE(candidate, logfile=None)
                pre.attach(lambda: path_up.append(candidate.copy()), interval=1)
                pre.run(fmax=1.5, steps=15)
            except Exception:
                pass

            # --- B. Transition State Search (Sella) ---
            ts_found = False
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    
                    dyn = Sella(
                        candidate,
                        internal=use_internal,
                        order=sella_order,
                        logfile=None
                    )
                    dyn.attach(lambda: path_up.append(candidate.copy()), interval=1)
                    ts_found = dyn.run(fmax=ts_fmax, steps=ts_steps)
            except Exception:
                continue

            if not ts_found:
                continue

            # Mark TS
            ts_snapshot = candidate.copy()
            ts_snapshot.info['type'] = 'TS_SADDLE'
            path_up.append(ts_snapshot)
            ts_uid = f"{parent_hash}_p{i}_{uuid.uuid4().hex[:6]}"
            
            discovered_structures.append(_package_result(candidate, {
                "type": "transition_state",
                "temp_id": ts_uid,
                "connected_to_root": parent_hash,
                "perturbation_idx": i
            }))

            # --- C. Connectivity (IRC) ---
            if run_irc:
                for direction in ['forward', 'reverse']:
                    path_down: List[Atoms] = []
                    irc_atoms = candidate.copy()
                    irc_atoms.calc = _build_atoms_obj(symbols, positions, cell, calculator_factory).calc
                    if ase_cons:
                        irc_atoms.set_constraint(ase_cons)
                    
                    path_success = False
                    
                    # IRC Descent
                    try:
                        irc = IRC(irc_atoms, logfile=None, dx=0.1)
                        irc.attach(lambda: path_down.append(irc_atoms.copy()), interval=1)
                        irc.run(direction=direction, steps=40)
                        path_success = True
                    except Exception:
                        # Fallback Kick if IRC fails (respecting constraints)
                        kick = np.random.normal(0, 0.05, irc_atoms.positions.shape)
                        kick[noise_mask] = 0.0
                        irc_atoms.positions += kick
                        path_down.append(irc_atoms.copy())
                        path_success = True

                    # Final Relax
                    if path_success:
                        try:
                            opt = FIRE(irc_atoms, logfile=None)
                            opt.attach(lambda: path_down.append(irc_atoms.copy()), interval=2)
                            opt.run(fmax=final_relax_fmax, steps=100)
                            
                            discovered_structures.append(_package_result(irc_atoms, {
                                "type": "final_state",
                                "connected_to_ts": ts_uid,
                                "reaction_path": direction,
                                "root_origin": parent_hash,
                                "is_product": True
                            }))
                            
                            if write_trajectories:
                                fname = os.path.join(
                                    os.path.dirname(output_filename),
                                    'reactivity_path',
                                    f"{parent_hash[:8]}_p{i}_{direction}.xyz"
                                )
                                _save_trajectory(path_up + path_down, fname)

                        except Exception as e:
                            logger.warning("Product relax failed: %s", e)

        return discovered_structures

    return run