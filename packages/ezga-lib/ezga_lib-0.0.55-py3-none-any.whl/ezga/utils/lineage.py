# lineage.py
from ..core.interfaces import ILineage
import uuid
import os

class LineageTracker(ILineage):
    def __init__(self):
        """
        Tracks the lineage (origin) of structures across GA runs.
        Each structure receives a globally unique ID composed of:
          <RUN_UID>-<PID>-<COUNTER>
        """
        self._structure_id_counter = 0
        self._process_id = os.getpid()
        self._run_uid = uuid.uuid4().hex[:8]  # 8-hex unique tag per GA run
        self.lineage = {}

    @staticmethod
    def _obj_id(x) -> int:
        if hasattr(x, "id"):     # LazySingleRunProxy
            return int(x.id)
        if isinstance(x, int):   # already an ID
            return x
        raise TypeError("Expected proxy or integer id")

    def assign_lineage_info(self, structure, generation: int, parents: list, operation: str, mutation_list: list=None):
        """
        Assigns lineage metadata to a structure.

        Parameters
        ----------
        structure : object
            The structure to which lineage info will be assigned.
        generation : int
            The current generation index.
        parents : list
            A list of parent structures.
        operation : str
            Genetic operation type, e.g., "mutation" or "crossover".
        mutation_list : list, optional
            List of mutations applied to the structure.
        """
        if not hasattr(structure.AtomPositionManager, 'metadata'):
            structure.AtomPositionManager.metadata = {}
        if not isinstance(structure.AtomPositionManager.metadata, dict):
            structure.AtomPositionManager.metadata = {}

        self._structure_id_counter += 1
        unique_id = f"{self._run_uid}-{self._process_id}-{self._structure_id_counter:010d}"

        metadata = structure.AtomPositionManager.metadata
        metadata['id'] = unique_id
        metadata['generation'] = generation
        metadata['parents'] = parents
        metadata['operation'] = operation
        metadata['run_uid'] = self._run_uid
        metadata['pid'] = self._process_id

        if mutation_list:
            metadata['mutation_list'] = mutation_list

        self.lineage[unique_id] = {
            'generation': generation,
            'parents': parents,
            'operation': operation,
            'pid': self._process_id,
            'run_uid': self._run_uid,
        }

        return unique_id

    def assign_lineage_info_par_partition(self, dataset, generation: int, parents: list, operation: str, ):
        """
        """
        for proxy in dataset.containers:
            self.assign_lineage_info(proxy, generation=generation, parents=parents, operation=operation)

        return self._structure_id_counter



