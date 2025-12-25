import time
import numpy as np
from typing import List, Callable

from ..core.interfaces import (
    IEvaluator,
    IPopulation,
)

class Evaluator(IEvaluator):
    """
    Evaluator class that normalizes inputs upon initialization.
    Whether you pass a single function or a list of functions, 
    internally it treats them as a single executable callable.
    """

    def __init__(self, 
        features_funcs: Callable | List[Callable] = None, 
         objectives_funcs: Callable | List[Callable] = None,
        debug = False):
        """
        Initializes the Evaluator.
        
        It automatically converts lists of functions into a single concatenated callable.
        """

        self.features_funcs = features_funcs
        self.objectives_funcs = objectives_funcs

        # --- NORMALIZATION STEP ---
        # Here we process the inputs immediately. 
        # self.features_funcs will ALWAYS be a single callable returning (N, D_total)
        self.features_funcs = self._build_combined_callable(features_funcs, default_val=1.0)
        
        # self.objectives_funcs will ALWAYS be a single callable returning (N, K_total)
        self.objectives_funcs = self._build_combined_callable(objectives_funcs, default_val=0.0)

        self.debug = debug

    def _build_combined_callable(self, input_funcs, default_val=0.0):
        """
        Factory method: Transforms list[func] -> single_func
        """
        # 1. Handle None: Return a dummy function
        if input_funcs is None:
            # Returns (N, 1) array with default_val
            return lambda x: np.full((len(x), 1), default_val, dtype=np.float64)

        # 2. Handle List: Create a wrapper that concatenates outputs
        if isinstance(input_funcs, list):
            def combined_wrapper(x):
                outputs = []
                for func in input_funcs:
                    res = func(x)
                    res = np.array(res)
                    # Safety check: ensure 2D shape (N, 1) for concatenation
                    if res.ndim == 1:
                        res = res.reshape(-1, 1)
                    outputs.append(res)
                
                # Concatenate along columns (features/objectives)
                return np.concatenate(outputs, axis=1)
            
            return combined_wrapper

        # 3. Handle Single Callable: Return as is
        return input_funcs

    def evaluate_features_objectives(self, dataset:object):
        """
        Evaluates features and objectives for a list of structures.

        Parameters
        ----------
        structures : list
            List of structure containers.

        Returns
        -------
        features : np.ndarray
            Computed features for each structure.
        objectives : np.ndarray
            Computed objectives for each structure.
        """

        # Evaluate features
        features = self.get_features( dataset )
        

        # Evaluate objectives
        objectives = self.get_objectives( dataset )

        return features, objectives

    def get_features(self, dataset):
        # Directly call the pre-processed callable
        return self.features_funcs(dataset)

    def get_objectives(self, dataset):
        # Directly call the pre-processed callable
        return self.objectives_funcs(dataset)

    # --- DEPRECATED / INTERNAL METHODS (Now Simplified) ---

    def _evaluate_features(self, dataset, features_funcs=None):
        """
        Legacy wrapper. Now just calls the stored function.
        """
        f = features_funcs if features_funcs else self.features_funcs
        return f(dataset)

    def _evaluate_objectives(self, dataset, objectives_funcs=None):
        """
        Legacy wrapper. Now just calls the stored function.
        The complex logic of transposing lists is no longer needed here
        because __init__ already handled it.
        """
        f = objectives_funcs if objectives_funcs else self.objectives_funcs
        return f(dataset)
