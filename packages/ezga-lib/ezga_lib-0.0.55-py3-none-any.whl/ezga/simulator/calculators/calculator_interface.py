"""
EZGA Calculator Interface Adapter.

This module provides a decorator-based interface that allows users to define 
physical models using standard ASE `Atoms` objects, shielding them from 
the internal data management of the evolutionary algorithm (arrays, hashes, SQL).

The adapter handles:
1. Reconstruction of ASE Atoms from raw gene data.
2. Automatic application of geometric constraints.
3. Injection of lineage metadata (parent hashes).
4. Serialization of results back to the simulator's raw format.
"""

from __future__ import annotations

import copy
import logging
from typing import Callable, Union, List, Dict, Any, Tuple, Optional

import numpy as np
from ase import Atoms
from ase.constraints import FixAtoms

# =============================================================================
# Type Definitions
# =============================================================================

# 1. Input/Output types for the USER function
# The user receives an `Atoms` object and can return:
#   - A single Atoms object (Standard Optimization)
#   - A tuple (Atoms, MetadataDict) (Optimization with extra logging)
#   - A list of Atoms objects (Reactivity/Branching exploration)
UserFunctionResult = Union[Atoms, Tuple[Atoms, Dict[str, Any]], List[Atoms]]
UserFunction = Callable[..., UserFunctionResult]

# 2. Input/Output types for the SIMULATOR (Internal API)
# Format: (Positions, Symbols, Cell, Energy, Metadata)
RawCalculationResult = Tuple[np.ndarray, List[str], Optional[np.ndarray], float, Dict[str, Any]]
SimulatorFunction = Callable[..., Union[RawCalculationResult, List[RawCalculationResult]]]

# Logger configuration
logger = logging.getLogger(__name__)


# =============================================================================
# The Adapter Decorator
# =============================================================================

def register_calculator(func: UserFunction) -> SimulatorFunction:
    """
    Decorator that adapts a simplified user-defined calculator (Atoms -> Atoms)
    into the strict signature required by the EZGA Simulator.

    Features:
    - Automatically builds the `Atoms` object from raw positions/symbols.
    - Applies `FixAtoms` constraints based on the `fixed` boolean mask.
    - Injects `parent_hash` into `atoms.info` for connectivity tracking.
    - Serializes the output(s) back to raw NumPy arrays.

    Parameters
    ----------
    func : UserFunction
        A function with signature `f(atoms: Atoms, **kwargs) -> result`.

    Returns
    -------
    wrapper : SimulatorFunction
        The wrapped function to be passed to the `Simulator` class.
    """
    
    def internal_wrapper(
        symbols: List[str],
        positions: np.ndarray,
        cell: Optional[np.ndarray],
        fixed: Optional[np.ndarray] = None,
        constraints: Optional[List[Callable]] = None,
        parent_hash: Optional[str] = None,
        **kwargs # Captures runtime args like temperature, generation, etc.
    ) -> Union[RawCalculationResult, List[RawCalculationResult]]:
        
        # ---------------------------------------------------------------------
        # 1. Construction (Raw Data -> ASE Atoms)
        # ---------------------------------------------------------------------
        # Detect Periodic Boundary Conditions based on cell validity
        pbc = False
        if cell is not None and np.abs(np.linalg.det(cell)) > 1e-6:
            pbc = True
            
        atoms = Atoms(symbols=symbols, positions=positions, cell=cell, pbc=pbc)
        
        # Apply Geometric Constraints (FixAtoms)
        # This ensures the user cannot accidentally move frozen atoms
        if fixed is not None and np.any(fixed):
            atoms.set_constraint(FixAtoms(mask=fixed))
            
        # Inject Lineage Metadata
        # This allows the user function to access the parent ID if needed
        if parent_hash:
            atoms.info['parent_hash'] = parent_hash
        
        # ---------------------------------------------------------------------
        # 2. Execution (User Logic)
        # ---------------------------------------------------------------------
        try:
            # Pass **kwargs so users can use 'sampling_temperature' or 'generation'
            user_output = func(atoms, **kwargs)
        except Exception as e:
            logger.error(f"User calculator '{func.__name__}' failed: {e}")
            raise RuntimeError(f"User calculator failure: {e}") from e

        # ---------------------------------------------------------------------
        # 3. Normalization (Polymorphic Return Handling)
        # ---------------------------------------------------------------------
        results_to_process: List[Atoms] = []
        
        # Case A: Reactivity/Exploration (1 -> Many)
        if isinstance(user_output, list):
            if not all(isinstance(a, Atoms) for a in user_output):
                raise TypeError("List returned by calculator must contain only ASE Atoms objects.")
            results_to_process = user_output
            is_branching = True
            
        # Case B: Optimization with Extra Metadata (1 -> 1)
        elif isinstance(user_output, tuple):
            atoms_res, meta_res = user_output
            if not isinstance(atoms_res, Atoms) or not isinstance(meta_res, dict):
                raise TypeError("Tuple return must be (Atoms, dict).")
            # Merge extra metadata into atoms.info for unified processing
            atoms_res.info.update(meta_res)
            results_to_process = [atoms_res]
            is_branching = False
            
        # Case C: Standard Optimization (1 -> 1)
        elif isinstance(user_output, Atoms):
            results_to_process = [user_output]
            is_branching = False
            
        else:
            raise TypeError(
                f"Invalid return type {type(user_output)}. "
                "Expected Atoms, (Atoms, dict), or List[Atoms]."
            )

        # ---------------------------------------------------------------------
        # 4. Serialization (ASE Atoms -> Raw Data)
        # ---------------------------------------------------------------------
        final_payload = []
        
        for res_atoms in results_to_process:
            # Extract Geometry
            new_pos = np.array(res_atoms.get_positions())
            new_sym = res_atoms.get_chemical_symbols()
            
            # Extract Cell (only if PBC is active)
            new_cell = None
            if res_atoms.pbc.any():
                new_cell = np.array(res_atoms.get_cell())
            
            # Extract Energy (Fail-safe)
            try:
                new_E = float(res_atoms.get_potential_energy())
            except (RuntimeError, ValueError):
                new_E = float('nan')
            
            # Extract Metadata
            # Deepcopy ensures no reference issues with the internal info dict
            new_meta = copy.deepcopy(res_atoms.info)
            
            # Clean up internal keys that shouldn't persist to the database
            new_meta.pop('parent_hash', None) 
            
            final_payload.append((new_pos, new_sym, new_cell, new_E, new_meta))

        # Return format expected by Simulator
        # If user returned a single Atom (Case B/C), return a Tuple.
        # If user returned a List (Case A), return a List.
        if not is_branching and len(final_payload) == 1:
             return final_payload[0]
        
        return final_payload

    return internal_wrapper


'''
from ase.calculators.emt import EMT
from calculator_interface import register_calculator

@register_calculator
def calc_rapida(atoms, **kwargs):
    # El usuario solo define la física
    atoms.calc = EMT()
    atoms.get_potential_energy()
    return atoms


from ase.optimize import FIRE
from mace.calculators import MACECalculator
from calculator_interface import register_calculator

# Instancia global o singleton para no recargar modelo
mace_calc = MACECalculator(model_paths='large.model', device='cuda')

@register_calculator
def relax_structure(atoms, sampling_temperature=0.0, **kwargs):
    atoms.calc = mace_calc
    
    # El usuario decide lógica basada en temperatura del GA
    fmax_target = 0.05 if sampling_temperature < 0.5 else 0.1
    
    dyn = FIRE(atoms)
    dyn.run(fmax=fmax_target, steps=50)
    
    # El usuario puede agregar metadata personalizada
    atoms.info['optimizer'] = 'FIRE'
    atoms.info['fmax_reached'] = fmax_target
    
    return atoms
'''