# ----------------------------------------------------------------------------- #
# Simulator
# ----------------------------------------------------------------------------- #
from __future__ import annotations

import random
import copy
import traceback   
import logging

from pathlib import Path
from typing import Optional, Union, Sequence, Callable, Any, List, Tuple, Dict

import numpy as np
from tqdm import tqdm
from math import nan

from ..core.interfaces import ISimulator, ILogger

# ----------------------------------------------------------------------------- #
# Type Definitions
# ----------------------------------------------------------------------------- #

# A single calculation result: (Positions, Symbols, Cell, Energy, Metadata)
CalcResult = Tuple[np.ndarray, List[str], Optional[np.ndarray], float, Dict[str, Any]]

# A calculator can return one result (Optimization) or a list of results (Exploration)
CalculatorReturn = Union[CalcResult, List[CalcResult]]

# Function signature for the Calculator
Calculator = Callable[..., CalculatorReturn]
#Calculator = Callable[..., tuple[np.ndarray, list[str], np.ndarray, float]]

Mode = Union[str, None]  # "sampling", "random", "uniform"
#Mode = Literal["sampling", "random", "uniform"]

# ----------------------------------------------------------------------------- #
# Utility
# ----------------------------------------------------------------------------- #
def linear_interpolation(data, N):
    """
    Generates N linearly interpolated points over M input points.

    Parameters
    ----------
    data : int, float, list, tuple, or numpy.ndarray
        Input data specifying M control points. If scalar or of length 1,
        returns a constant array of length N.
    N : int
        Number of points to generate. Must be a positive integer and at least
        as large as the number of control points when M > 1.

    Returns
    -------
    numpy.ndarray
        Array of N linearly interpolated points.

    Raises
    ------
    ValueError
        If N is not a positive integer, N < M (when M > 1), or data is invalid.
    """
    # Validate N
    if not isinstance(N, int) or N <= 0:
        raise ValueError("N must be a positive integer.")
    
    # Handle scalar input
    if isinstance(data, (int, float)):
        return np.full(N, float(data))
    
    # Convert sequence input to numpy array
    try:
        arr = np.asarray(data, dtype=float).flatten()
    except Exception:
        raise ValueError("Data must be an int, float, list, tuple, or numpy.ndarray of numeric values.")
    
    M = arr.size
    if M == 0:
        raise ValueError("Input data cannot be empty : Input data sequence must contain at least one element.")
    if M == 1:
        return np.full(N, arr[0])
    
    # Ensure N >= M for piecewise interpolation
    if N < M:
        raise ValueError(f"Target size N ({N}) must be >= input size M ({M}).")

    # Define original and target sample positions
    xp = np.arange(M)
    xi = np.linspace(0, M - 1, N)
    
    # Perform piecewise linear interpolation
    return np.interp(xi, xp, arr)

# ----------------------------------------------------------------------------- #
# Simulator
# ----------------------------------------------------------------------------- #

class Simulator(ISimulator):
    """
    Core engine for running physical simulations on evolutionary individuals.
    
    It supports two modes of operation:
    1. **Optimization Mode (1-to-1):** Relaxing a structure to a local minimum.
    2. **Exploration Mode (1-to-N):** Expanding a structure into multiple 
       Transition States (TS) and products (branching).
    """
    def __init__(
        self,
        *,
        mode: str = "sampling",
        output_path: Union[str, Path] = Path("simulation_out.xyz"),
        calculator: Calculator | Sequence[Calculator],
        logger: Optional[ILogger] = None,
        debug: bool = False,
    ):
        """
        Initialize the Simulator.

        Args:
            mode: Temperature sampling mode ('sampling', 'random', 'uniform').
            output_path: Default path for trajectory logs.
            calculator: A callable or list of callables that perform the physics.
            logger: Custom logger instance.
            debug: Enable verbose traceback logging.
        """
        self.mode = mode or 'sampling'      
        self.output_path = Path(output_path) if output_path else Path("simulation_out.xyz")

        self.logger = logger or logging.getLogger(__name__)
        self.debug = debug

        self._calculators: tuple[Calculator, ...] = self._normalise_calculator(calculator)

    # ──────────────────────────────────────────────────────────────────────
    # calculator property
    # ──────────────────────────────────────────────────────────────────────
    @property
    def calculator(self) -> Calculator | tuple[Calculator, ...]:
        """Return the current calculator pool."""
        return self._calculators if len(self._calculators) > 1 else self._calculators[0]

    @calculator.setter
    def calculator(self, value: Calculator | Sequence[Calculator]) -> None:
        """Replace the calculator pool, applying the same validation as ``__init__``."""
        self._calculators = self._normalise_calculator(value)

    # ──────────────────────────────────────────────────────────────────────
    # public API
    # ──────────────────────────────────────────────────────────────────────
    def run(
        self, 
        individuals: Sequence[object],
        *,
        temperature: float = 1.0,
        mode: Mode | None = "sampling",
        generation: Optional[int] = None,
        output_path: Path | str | None = None,
        constraints: Optional[Sequence[Callable]] = None,
    ) -> Sequence[object]:
        """
        Execute simulations on a batch of individuals.

        If the calculator returns a single result (standard optimization), 
        the individual is updated in-place.
        If the calculator returns a list of results (TS search), 
        the individual is cloned and branched into multiple new individuals.

        Args:
            individuals: List of EZGA Individual objects.
            temperature: Base temperature for the batch.
            mode: Override for temperature sampling mode.
            generation: Current generation index (for logging).
            output_path: Specific output path for this run.
            constraints: List of constraint functions.

        Returns:
            List[object]: A flat list containing all processed/generated individuals.
        """
        self._validate_args(individuals, temperature, mode, generation)

        n_struct = len(individuals)
        output_path = Path(output_path or self.output_path)
        mode = mode or self.mode
        total_individuals = len(individuals)
        generation_idx = generation if generation is not None else 0

        # Generate temperature schedule for the batch
        temps = self._build_temperature_array(total_individuals, temperature, mode)

        # 2) If device='cpu', run tasks sequentially in the main process
        self.logger.info(
            f"Starting simulation batch: {total_individuals} structures "
            f"(Gen={generation_idx}, T={temperature:.2f}, mode={mode})"
        )

        expanded_population: List[object] = []
    
        # --- Main Simulation Loop ---        
        for idx, (individual, T_i) in enumerate(
            tqdm(zip(individuals, temps),
                 total=total_individuals,
                 desc="Simulations"),
            start=1
        ):
            try:
                # 1. Extract Atomic Data
                apm = individual.AtomPositionManager

                # Sanitize/Reset properties before calculation
                apm.charge = None
                apm.magnetization = None
                
                symbols = apm.atomLabelsList
                positions = np.asarray(apm.atomPositions, dtype=float)
                cell = np.asarray(apm.latticeVectors, dtype=float)
                fixed = np.asarray(apm.atomicConstraints, dtype=bool) if apm.atomicConstraints is not None else None

                # Extract Parent Hash (Essential for Connectivity Graph)
                parent_meta = getattr(apm, "metadata", {}) or {}
                parent_hash = parent_meta.get("hash", None)

                # 2. Prepare Output Directory
                calc_out_file = (
                    output_path 
                    / "generation" 
                    / f"gen{generation_idx}" 
                    / f"simulator_out_{generation_idx}.xyz"
                )

                # 3. Select & Execute Calculator
                calc_func = random.choice(self._calculators)

                # The calculator receives the parent_hash to tag new nodes in the graph
                results_payload: CalculatorReturn = calc_func(
                    symbols=symbols,
                    positions=positions,
                    cell=cell,
                    fixed=fixed,
                    constraints=constraints,
                    sampling_temperature=T_i,
                    output_filename=str(calc_out_file),
                    parent_hash=parent_hash 
                )

                # 4. Handle Polymorphic Return (One vs Many)
                results_list: List[CalcResult] = []
                is_branching = False

                if isinstance(results_payload, list):
                    # Case A: Exploration (1 -> N). We received multiple new states.
                    results_list = results_payload
                    is_branching = True
                elif isinstance(results_payload, tuple) and len(results_payload) == 5:
                    # Case B: Optimization (1 -> 1). Standard update.
                    results_list = [results_payload]
                    is_branching = False
                else:
                    raise TypeError(
                        f"Invalid return type from calculator: {type(results_payload)}. "
                        "Expected tuple (len 5) or list of tuples."
                    )

                # 5. Update/Create Individuals
                for res_idx, (new_pos, new_sym, new_cell, new_E, new_meta) in enumerate(results_list):
                    
                    # Strategy: If we are branching (TS search), we ALWAYS clone to preserve
                    # the reactant minimum and create new independent TS/Product objects.
                    # If we are just optimizing (1-to-1), we update in-place for efficiency.
                    
                    if not is_branching and res_idx == 0:
                        target_ind = individual
                    else:
                        target_ind = copy.deepcopy(individual)

                    # Update Physics
                    target_ind.AtomPositionManager.set_atomPositions(new_pos)
                    target_ind.AtomPositionManager.set_atomLabels(new_sym)
                    target_ind.AtomPositionManager.set_latticeVectors(new_cell)
                    target_ind.AtomPositionManager.set_E(new_E)

                    # Initialize Metadata if missing
                    if getattr(target_ind.AtomPositionManager, "metadata", None) is None:
                        target_ind.AtomPositionManager.metadata = {}
                    
                    # Merge new metadata (containing connectivity info)
                    if new_meta:
                        # Sanitize numpy arrays in metadata for JSON compatibility
                        sanitized_meta = {
                            k: (v.tolist() if isinstance(v, np.ndarray) else v)
                            for k, v in new_meta.items()
                        }
                        target_ind.AtomPositionManager.metadata.update(sanitized_meta)

                    # Append to the result list
                    expanded_population.append(target_ind)

                # Log progress for the primary result
                first_E = results_list[0][3] if results_list else float('nan')
                self.logger.debug(
                    f"Structure {idx}/{total_individuals} processed. "
                    f"Generated {len(results_list)} states. Primary E={first_E:.4f}"
                )

            except Exception as exc:
                # Fault Tolerance: Log failure but do not crash the entire generation
                calc_name = getattr(calc_func, "__name__", str(calc_func))
                self.logger.error(
                    f"Calculator '{calc_name}' failed on structure {idx} (Gen={generation_idx}). "
                    f"Error: {exc}"
                )
                self.logger.error(traceback.format_exc())
                
                # Optional: In strict GA, we might discard the individual. 
                # Or we can append the original with a high penalty energy.
                # Here we skip appending, effectively killing the failed individual.

        return expanded_population

    # ──────────────────────────────────────────────────────────────────────
    # Helpers & Validation
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _normalise_calculator(
        calculator: Calculator | Sequence[Calculator],
    ) -> tuple[Calculator, ...]:
        """Ensures calculator is always a tuple of callables."""
        if callable(calculator):
            return (calculator,)
        if isinstance(calculator, Sequence) and calculator:
            if not all(callable(c) for c in calculator):
                raise TypeError("All elements in calculator sequence must be callable.")
            return tuple(calculator)
        raise TypeError("Calculator must be a callable or non-empty sequence of callables.")

    def _validate_args(
        self,
        individuals: Sequence[object],
        temperature: float,
        mode: Mode,
        generation: Optional[int],
    ) -> None:
        if temperature < 0:
            raise ValueError("`temperature` must be non-negative")
        if generation is not None and not isinstance(generation, int):
            raise TypeError("`generation` must be an int or None")
        if mode not in {"sampling", "random", "uniform"}:          # FIX: mode variable name
            raise ValueError(f"unknown mode {mode!r}")
        if not hasattr(individuals, "__len__"):                    # FIX: clearer check
            raise TypeError("`individuals` must be a sized container")

    @staticmethod
    def _build_temperature_array(n: int, base_t: float, mode: Mode) -> np.ndarray:
        """Constructs the temperature schedule for the batch."""
        if mode == "uniform":
            return np.linspace(0.0, 1.0, num=n, dtype=float)
        if mode == "random":
            return np.random.uniform(0.0, 1.0, size=n)
        # Default: constant sampling temperature
        return np.full(n, base_t, dtype=float)
        



