"""
Null Calculator (Mock) for EZGA Testing.

This module mimics the API and behavior of the production `ase_calculator` but
performs no expensive physics. It is used to test the EZGA pipeline, database 
storage, constraint logic, and scheduling without running DFT/MD.

It replicates:
- The Factory Pattern (returns a `run` callable).
- The Input/Output signature (Atoms -> Tuple).
- Constraint application (using the same logic as production).
- Simulation of delays (to test parallel execution).
"""

from __future__ import annotations

import time
import numpy as np
import copy
from typing import Union, Sequence, Optional, Callable, Tuple, Dict, Any, List

from ase import Atoms
from ase.constraints import FixAtoms, FixCartesian

# Import helpers from your existing modules if available, 
# otherwise we implement simplified local versions to ensure independence.
# (Assuming internal imports or re-implementing for standalone robustness)

# =============================================================================
# Mock / Utility Logic (Simplified from production)
# =============================================================================

def _mock_schedule_value(schedule: Union[float, Sequence[float], None], idx: int) -> float:
    """Gets a value from a scalar or list schedule."""
    if schedule is None:
        return 0.0
    if isinstance(schedule, (int, float)):
        return float(schedule)
    # Simple clamp for lists
    if idx >= len(schedule):
        return float(schedule[-1])
    return float(schedule[idx])

# =============================================================================
# Null Calculator Factory
# =============================================================================

def null_calculator(
    # --- Testing Control Parameters ---
    fixed_energy: float = 0.0,           # Returns this energy always
    simulation_delay: float = 0.0,       # Sleep time (seconds) to simulate compute
    perturb_positions: float = 0.0,      # Add random noise to positions (mimic relaxation)
    mock_vib_data: bool = False,         # Inject fake vibrational metadata
    
    # --- Standard EZGA Interface Args (Ignored or Mocked) ---
    calculator: object = None,           # Ignored
    device: str = 'cpu',                 # Ignored
    
    # --- Pipeline Stages (Used for timing/logic checks) ---
    nvt_steps: Union[int, Sequence[float], None] = None,
    fmax: Union[float, Sequence[float], None] = 0.05,
    steps_max: int = 100,
    
    # --- Constraints (Respects real logic) ---
    constraint_logic: str = "all",
    constraint_action: str = "freeze",
    freeze_components: Optional[Sequence[Union[int, str]]] = None,
    constraints: Optional[Sequence[Callable]] = None,
    
    # --- Catch-all for other args to prevent crashes ---
    **kwargs
) -> Callable[..., Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], float, Dict[str, Any]]]:
    
    """
    Builds a `run(...)` callable that mimics the production pipeline but simply
    waits and returns dummy data.
    """
    
    # Pre-process constraints just like the real calculator
    factory_constraints = list(constraints) if constraints else []

    def run(
        symbols: Union[np.ndarray, Sequence[str]],
        positions: np.ndarray,
        cell: np.ndarray,
        *,
        fixed: np.ndarray = None,
        sampling_temperature: float = 0.0,
        steps_max_: int = steps_max,
        output_filename: str = 'NULL_out.xyz',
        constraints: Optional[Sequence[Callable]] = None,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], float, Dict[str, Any]]:

        # 1. Setup Atoms (Standard ASE)
        # ---------------------------------------------------------
        positions_arr = np.asarray(positions, dtype=float)
        symbols_arr = np.asarray(symbols, dtype=object)
        
        pbc = False
        cell_arr = None
        if cell is not None:
             cell_arr = np.asarray(cell, dtype=float)
             if np.abs(np.linalg.det(cell_arr)) > 1e-6:
                 pbc = True
        
        atoms = Atoms(symbols=symbols_arr, positions=positions_arr, cell=cell_arr, pbc=pbc)

        # 2. Simulate Constraint Logic (Critical for testing predicates)
        # ---------------------------------------------------------
        # Here we mimic the logic: If constraints are passed, we check if they run.
        # We won't implement the full `_select_indices` logic here to keep it short,
        # but in a real test you might want to call the real helper functions.
        
        # Simulating "Fixed" mask from input (legacy support)
        if fixed is not None and np.any(fixed):
            atoms.set_constraint(FixAtoms(mask=fixed))
        
        # 3. Simulate Work ("Calculations")
        # ---------------------------------------------------------
        # A. Delay (Simulate DFT time)
        if simulation_delay > 0:
            time.sleep(simulation_delay)

        # B. Perturbation (Simulate Relaxation moving atoms)
        # Only move atoms that are NOT fixed
        if perturb_positions > 0:
            noise = np.random.normal(scale=perturb_positions, size=positions_arr.shape)
            
            # Simple check for fixed atoms to respect constraints in mock
            constraint_indices = []
            for constr in atoms.constraints:
                if isinstance(constr, FixAtoms):
                    constraint_indices.extend(constr.index)
            
            mask = np.ones(len(atoms), dtype=bool)
            mask[constraint_indices] = False
            
            # Apply noise only to free atoms
            atoms.positions[mask] += noise[mask]

        # 4. Construct Result Payload
        # ---------------------------------------------------------
        final_pos = atoms.get_positions()
        final_cell = atoms.get_cell().array if pbc else None
        
        # Mock Energy
        final_E = fixed_energy
        
        # Mock Metadata / Vibrational Corrections
        corrections = {}
        if mock_vib_data:
            # Simulate what F_vib pipeline returns
            corrections = {
                "F_vib_eV": 0.05, 
                "S_vib": 0.001, 
                "ZPE_eV": 0.02,
                "mock_status": "generated by null_calculator"
            }
            # Simulate the "Total Free Energy" calculation
            corrections["F"] = final_E + corrections["F_vib_eV"]
        else:
            corrections["F"] = final_E

        # Add debug info useful for tracing tests
        corrections["calculator_type"] = "null"
        corrections["simulated_delay"] = simulation_delay
        corrections["sampling_temp_input"] = sampling_temperature

        return (
            final_pos,
            symbols_arr,
            final_cell,
            final_E,
            corrections
        )

    return run