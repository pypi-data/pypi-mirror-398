from __future__ import annotations

import os
import time
import copy
import logging
import warnings
import numpy as np
import json  # Added for parameter logging
from typing import List, Optional
from pathlib import Path
from tqdm import tqdm

from sage_lib.partition.Partition import Partition

from ezga.core.interfaces import (
    IPopulation, ILineage, IHash, IAgent, IDoE
)

from ezga.utils.lineage import LineageTracker  # type: ignore
from ezga.utils.structure_hash_map import Structure_Hash_Map # type: ignore
from ezga.sync.agenticsync import Agentic_Sync
from ezga.DoE.DoE import DesignOfExperiments
from ezga.utils.molecule_blacklist import BlacklistDetector

class Population(IPopulation):
    """
    """
    def __init__(
        self,
        *,
        dataset_path: str | None = None,
        template_path: str | None = None,
        output_path: str | None = None,
        collision_factor: float | None = None,
        filter_duplicates: bool | None = True,
        size_limit: float | None = None,
        fetch_limit: int | None = None,

        db_path: str | None = None,
        db_ro_path: str | None = None,

        debug: bool = False,
        hash_map: Type[IHash] = Structure_Hash_Map,
        agent: Type[IAgent] = Agentic_Sync,
        lineage: Type[ILineage] = LineageTracker,

        constraints = None,
        ef_bounds: Tuple[float, float] | None = None,  # Pontetial units/atom bounds (typical GGAs)
        blacklist: List[str] = None,
    ):
        """
        Initializes the Population with file paths and default parameters.

        Parameters
        ----------
        dataset_path : str
            Path to the initial structures file.
        template_path : str
            Path to the template structure file.
        output_path : str
            Directory to save output files and logs.
        """
        self._dataset_path = dataset_path 
        self._template_path = None if template_path is None else template_path 
        self._output_path = '.' if output_path is None else output_path
        self.collision_factor = collision_factor
        self._filter_duplicates = filter_duplicates
        self.size_limit = size_limit
        self.fetch_limit = fetch_limit

        self.db_path = db_path
        self.db_ro_path = db_ro_path

        self.ef_bounds = ef_bounds
        self.blacklist_detector = BlacklistDetector(blacklist or [])

        self.debug = debug

        # Placeholder for Partition objects
        self._datasets = {
            'template':None,
            'dataset':None,
            'generation':None,
            'template_preload':None,
            'dataset_preload':None,
        }  # Should be set by load_population()

        self.hash_map   = hash_map
        self.agent      = agent
        self.lineage    = lineage
        self.DoE        = DesignOfExperiments(constraints=constraints)

    # ----------------------------------------------------------------
    # GETTERS/SETTERS
    # ----------------------------------------------------------------
    @property
    def dataset_path(self):
        """Gets the file path for the initial structures."""
        return self._dataset_path

    @dataset_path.setter
    def dataset_path(self, value):
        """Sets the file path for the initial structures."""
        self._dataset_path = value

    # --------------------------------------------------------------
    # Writable database path
    # --------------------------------------------------------------
    @property
    def db_path(self) -> Path:
        """Path to the writable database (as a Path object)."""
        return Path(self._db_path)

    @db_path.setter
    def db_path(self, value: str | Path | None):
        """Set writable database path; create directory if needed."""
        value = Path(value or ".")
        value.mkdir(parents=True, exist_ok=True)
        self._db_path = str(value)

    # --------------------------------------------------------------
    # Read-only database path
    # --------------------------------------------------------------
    @property
    def db_ro_path(self) -> Path:
        """Path to the read-only database (as a Path object)."""
        return Path(self._db_ro_path)

    @db_ro_path.setter
    def db_ro_path(self, value: str | Path | None):
        """Set read-only database path; create directory if needed."""
        value = Path(value or "db_ro")
        value.mkdir(parents=True, exist_ok=True)
        self._db_ro_path = str(value)


    @property
    def template_path(self):
        """Gets the template file path."""
        return self._template_path

    @template_path.setter
    def template_path(self, value):
        """Sets the template file path."""
        self._template_path = value

    @property
    def output_path(self):
        """Gets the output directory path."""
        return self._output_path

    @output_path.setter
    def output_path(self, value):
        """Sets the output directory path."""
        self._output_path = value

    @property
    def datasets(self):
        """Gets the dictionary of partition objects."""
        return self._datasets

    def get_dataset(self, name:str): 
        """Gets the dictionary of partition objects."""
        return self._datasets[name]

    def get_containers(self, name:str):
        """Gets the dictionary of partition objects."""
        if name in self._datasets:
            return list(self._datasets[name].containers)

        return None

    def set_dataset(self, name:str, dataset:object=None):
        """Gets the dictionary of dataset objects."""
        self._datasets[name] = dataset if not dataset is None else Partition()
        return self._datasets[name]

    def dataset_add(self, name:str, dataset:object) -> None: 
        """ """
        self._datasets[name].add(dataset)
        return True

    def size(self, name:str=None):
        """
        """
        return self._datasets[name].size if name else self._datasets['dataset'].size
 
    def filter(self, name:str, idx:list):
        """
        """
        # Bulk materialize efficiently:
        try:
            pop = self.get_dataset(name).materialize_by_ids(
                idx,
                dedup=True,                 # load each id once even if repeated
                sort_backend_reads=True,    # helps HDF5 locality
                independent_duplicates=True
            )
        except:
            pop = self.get_dataset(name).materialize_by_ids(
                idx,
                dedup=True,                 # load each id once even if repeated
                sort_backend_reads=False,    # helps HDF5 locality
                independent_duplicates=True
            )
        return pop 
        #return copy.deepcopy([self.get_dataset(name).containers[i] for i in idx])

    def set_population(self, name:str, population:list) -> bool:
        """
        """
        self.set_dataset( name, Partition() )
        self.get_dataset(name).add( population )

        return True

    # ----------------------------------------------------------------
    # LOAD
    # ----------------------------------------------------------------
    def load_population(self, logger:object = None): 
        """
        """

        # ------------------------------------------------------------------
        # 0)  Book‑keeping: log start‑up and start a wall‑clock timer
        # ------------------------------------------------------------------
        if logger:
            logger.info("Loading dataset from files.")

        # ------------------------------------------------------------------
        # 1)  DATASET PARTITION ------------------------------------------------
        # ------------------------------------------------------------------
        # 1.1  Always create an *empty* Partition object first so that we have a
        #      valid container even if subsequent file I/O fails.  This avoids
        #      having to repeat *None* checks later on.
        if not isinstance(self.db_ro_path, (str, Path) ):
            self.db_ro_path = 'db_ro'
        if not isinstance(self.db_path, (str, Path) ):
            self.db_path = '.'

        self.set_dataset( 
            'dataset', 
            Partition(
                storage='composite', # composite # hybrid
                base_root=self.db_ro_path,
                local_root=self.db_path,
            )
        )

        # 1.2  If the caller provided a valid *path* (and not, e.g., ``None`` or
        #      an already‑opened file object), read the structure files.
        if isinstance(self.dataset_path, (str, os.PathLike)):
            
            if self.size_limit:
                self.get_dataset('dataset').read_files(
                    file_location=self.dataset_path,
                    verbose=True,
                    sampling='random',
                    n_samples=self.size_limit
                )
            else:
                self.get_dataset('dataset').read_files(
                    file_location=str(self.dataset_path),
                    verbose=True,
                )
                
        # 1.3  Merge any *pre‑loaded* containers (prepared by the caller before
        #      invoking this method) into the freshly created partition.
        if isinstance(self.get_dataset('dataset_preload'), list):
            self.dataset_add(name='dataset', dataset=self.get_dataset('dataset_preload'))

        # 1.4  Feed every single *Structure* object into the global hash map so
        #      that the rest of the code base can perform O(1) look‑ups for
        #      de‑duplication or collision tracking.
        '''
        for container in tqdm(
            self.get_dataset('dataset').containers,
            desc="[load] Registering structures in hash map",
            unit="struct"
        ):
            self.hash_map.add_structure( container, force_rehash=False )
        '''

        # 1.5  If we are running in *synchronised* mode (i.e., multiple workers
        #      on different nodes), pull the current batch of structures from
        #      the synchronisation backend and add only the ones that do *not*
        #      produce a hash collision.
        if self.agent.active():
            try: 
                sync_new = list(self.agent.get_batch(prune=False, fetch_limit=self.fetch_limit))
                containers_list = [];  [containers_list.extend(sub.containers) for _, sub in sync_new]
                unique_structures, not_unique_structures = self.filter_hash_collisions(individuals=containers_list, force_rehash=False)
                self.dataset_add(name='dataset', dataset=unique_structures )

                logger.info(
                    "Genetic injection: %d structures added to dataset (Gen=%d).",
                    len(unique_structures),         
                    0,                                            
                )
            except Exception as exc:
                if hasattr(self, "logger"):
                    self.logger.warning(
                        "[Agentic_Sync] Failed during load_population step: %s", exc, exc_info=True
                    )

        # ------------------------------------------------------------------
        # 2)  TEMPLATE PARTITION ---------------------------------------------
        # ------------------------------------------------------------------
        # 2.1  Create an empty partition exactly as was done for the dataset.
        self.set_dataset('template')
        if isinstance(self.template_path, str):
            self._dataset['template'].read_files(
                file_location=self.template_path,
                source='xyz',
                verbose=True
            )
        else:
            logger.info("No template file provided, skipping template partition.")

        if isinstance(self.get_dataset('template_preload'), list):
            self.dataset_add(name='template', dataset=self.get_dataset('template_preload'))

        # ------------------------------------------------------------------
        # 3)  RECORD LINEAGE ---------------------------------------------------
        # ------------------------------------------------------------------
        # Every *Structure* gets tagged with lineage metadata so that its origin
        # can be traced throughout the workflow.  Stage‑index *0* indicates the
        # very first step; the empty list is the parent set, and the string
        # "initialization" becomes the *event* label.
        '''
        self.lineage.assign_lineage_info_par_partition(
            self.get_dataset('dataset'),     # partition to annotate
            0,                              # stage index generation
            [],                             # parent UIDs (none at this point)
            "initialization"                # event label
        )
        '''
        logger.info(f"Partitions loaded successfully.")

    
    def export_structures(
        self,
        dataset,
        file_path: str,
        sort: bool = False,
        key: int = 0,
        default_label: str = "config",
    ):
        """
        Export structures in the given dataset.

        Parameters
        ----------
        dataset : dataset
            Partition containing the structures to export.
        file_path : str
            Either:
              • a directory (no extension) → writes to <dir>/<default_label>.xyz, or
              • a full file path with extension (e.g., *.xyz) → writes exactly there.
        sort : bool
            If True, sort by objective 'key' (ascending) and store objectives in metadata.
        key : int
            Objective column to sort by when sort=True.
        default_label : str
            Used as filename when file_path is a directory.
        """
        p = Path(file_path)

        # Determine output directory and final file path
        if p.suffix:  # looks like a file (has extension)
            out_dir   = p.parent
            out_file  = p
        else:         # looks like a directory
            out_dir   = p
            out_file  = out_dir / f"{default_label}.xyz"

        # Create all needed directories
        out_dir.mkdir(parents=True, exist_ok=True)

        # Optional sorting by objective
        if sort:
            objectives = evaluate_objectives( list(dataset.containers), self.objective_funcs)
            for container, objective in zip(dataset.containers, objectives):
                apm = container.AtomPositionManager
                if not isinstance(getattr(apm, "metadata", None), dict):
                    apm.metadata = {}
                apm.metadata["objectives"] = list(objective)

            numeric = np.array([float(obj[key]) for obj in objectives])
            order = np.argsort(numeric, kind="mergesort")
            dataset.containers = [dataset.containers[i] for i in order]

        # Write using a full path (what your exporter expects)
        dataset.export_files(
            file_location=str(out_file),  # full path including filename + extension
            source="xyz",
            verbose=True,
        )
        return True


    def agent_sync(
        self, 
        dataset:list,
        objectives: np.ndarray,
        features: np.ndarray,
    ) -> list:
        """
        Synchronize the local population with the shared multi-agent backend.

        This method implements a fault-tolerant, scalable data-exchange mechanism 
        between workers (agents) in a distributed evolutionary search. It performs
        three tasks: (i) publish locally generated structures, (ii) retrieve unseen
        structures from other workers, and (iii) provide adaptive feedback signals
        (diversity, pressure) to the agent’s communication policy.

        Parameters
        ----------
        dataset : list
            Partition or list-like container holding the newly generated candidate 
            structures to be published to the shared synchronization backend.

        objectives : np.ndarray, shape (N, M)
            Objective matrix for the newly generated individuals. Each row represents
            an individual, and each column corresponds to an objective function to be
            minimized. This array is used to compute a lightweight aggregate measure 
            of selective pressure, which informs the agent’s adaptive communication 
            policy.

        features : np.ndarray, shape (N, F)
            Feature descriptors for the new individuals, used to compute a fast, 
            variance-based proxy for population diversity. This metric is 
            O(NF) and suitable for very large populations (millions of individuals).

        Returns
        -------
        list
            A flat list containing all newly received structure containers obtained
            from the synchronization backend. The list may be empty if no new data
            is available or if the backend is inactive.

        Notes
        -----
        • Fetching uses `get_batch(prune=False)` to avoid filesystem races during
          recursive directory scans on parallel filesystems.

        • Pruning is performed separately, rate-limited, and always wrapped in
          try/except to ensure robustness under concurrent access.

        • The method computes two adaptive metrics:
            - Diversity:    sum_k Var(features[:, k])
            - Pressure:     mean_i ||objectives[i]||

          Both metrics are designed to be mathematically meaningful yet extremely
          inexpensive to compute, allowing real-time policy updates even for 
          populations of size >10⁶.

        • The metrics are passed to `self.agent.update_policy_metrics(...)` which 
          executes the communication policy (e.g. Nash-style best response, 
          adaptive throttling, or any other decision rule implemented in the agent).
        """

        containers = list(dataset.containers)

        # 0) No agent configured
        if not getattr(self, "agent", None):
            if hasattr(self, "logger"):
                self.logger.warning("[Agentic_Sync] No agent configured; skipping sync.")
            return []

        try:
            # ============================================================
            # 1) Check agent readiness
            # ============================================================
            try:
                if not self.agent.active():
                    if hasattr(self, "logger"):
                        self.logger.warning("[Agentic_Sync] Agent inactive; skipping sync.")
                    return []
            except Exception as exc:
                if hasattr(self, "logger"):
                    self.logger.warning("[Agentic_Sync] active() failed: %s", exc, exc_info=True)
                return []


            # ============================================================
            # 2) ADAPTIVE POLICY UPDATE  (Nash-response logic)
            # ============================================================
            try:
                # --- diversity metric (simple but robust) ---
                #    distinct total atom counts
                local_div = len(containers)

                # --- pressure metric ---
                incoming_pressure = len(containers)

                # update the internal policies of the agent

                # --- Fast diversity estimate (O(NF)) ---
                try:
                    feats = np.asarray(features, dtype=float)
                    if feats.shape[0] > 1:
                        # Sum of variances = proxy for E||X−Y||²
                        diversity = float(feats.var(axis=0).sum())
                    else:
                        diversity = 0.0
                except Exception:
                    diversity = 0.0

                # --- Fast pressure estimate (O(N)) ---
                try:
                    objs = np.asarray(objectives, dtype=float)
                    if objs.shape[0] > 0:
                        # Mean magnitude of objective vectors
                        pressure = float(np.linalg.norm(objs, axis=1).mean())
                    else:
                        pressure = 0.0
                except Exception:
                    pressure = float(len(containers))

                # --- Update policy ---
                self.agent.update_policy_metrics(
                    diversity=diversity,
                    pressure=pressure,
                )
                
            except Exception as exc:
                if hasattr(self, "logger"):
                    self.logger.warning(
                        "[Agentic_Sync] policy update failed: %s",
                        exc,
                        exc_info=True
                    )
                # continue even on policy failure


            # ============================================================
            # 3) Append local candidates to shared backend
            # ============================================================
            # Try appending candidate containers
            try:
                self.agent.append(containers)
            except Exception as exc:
                if hasattr(self, "logger"):
                    self.logger.warning(
                        "[Agentic_Sync] Failed during append step: %s", exc, exc_info=True
                    )
                # <-- do NOT return here; proceed to get_batch

            # ============================================================
            # 4) Fetch unseen batches (safe, prune disabled here)
            # ============================================================
            try:
                # Important: consume inside the try so generator exceptions are caught here
                sync_new = list(self.agent.get_batch( prune=False, fetch_limit=self.fetch_limit )) # prune=False

            except Exception as exc:
                if hasattr(self, "logger"):
                    self.logger.warning(
                        "[Agentic_Sync] Failed during get_batch step: %s", exc, exc_info=True
                    )
                return []

            # ============================================================
            # 5) Merge new structures defensively
            # ============================================================
            # Collect all containers from the new dataset
            containers_list = []
            for batch_id, dataset in sync_new:
                try:
                    containers_list.extend(getattr(dataset, "containers", []))
                except Exception as exc:
                    if hasattr(self, "logger"):
                        self.logger.warning(
                            "[Agentic_Sync] Failed while merging containers "
                            "from batch %s: %s", batch_id, exc, exc_info=True
                        )
                    continue

            # ============================================================
            # 6) Controlled, time-gated prune
            # ============================================================
            try:
                pruned = self.agent.attempt_prune(interval=60.0, budget=8, min_age=5.0)
                if pruned and hasattr(self, "logger"):
                    self.logger.debug("[Agentic_Sync] Pruned %d old batches.", pruned)
            except Exception as exc:
                if hasattr(self, "logger"):
                    self.logger.warning("[Agentic_Sync] maybe_prune() failed: %s", exc, exc_info=True)

            # ============================================================
            # 7) Return newly synchronised structures
            # ============================================================
            return containers_list

        except Exception as exc:
            # ============================================================
            # Final safeguard
            # ============================================================
            # Last-resort safeguard
            if hasattr(self, "logger"):
                self.logger.warning(
                    "[Agentic_Sync] Unexpected failure in agent_sync: %s",
                    exc,
                    exc_info=True,
                )
            return []

    def validate_candidates(self, individuals: list, features: np.array, remove:Optional[bool] = None) -> list:
        """
        Validate candidate individuals based on their composition in feature space.

        This method computes feature descriptors for each candidate structure using the provided
        feature functions (self.features_funcs) and then validates each candidate by applying the
        design validator (self.DoE.validate). The validator returns True if the candidate's features
        satisfy the design requirements and False otherwise.

        Parameters
        ----------
        individuals : list
            A list of candidate structure objects to be validated.

        Returns
        -------
        list
            A list of candidate individuals that meet the feature space requirements.
        """

        # 2) Local bindings for speed
        validate = self.DoE.validate if self.DoE else lambda *args, **kwargs: True

        # 3) Single pass: build valid list and penalise invalid
        valid_candidates = []
        physically_invalid_candidates = []
        out_of_doe_candidates = []
        blacklist_invalid_candidates = []

        for struct, feat in zip(individuals, features):
            # 1) DOE‐validation check
            if not self.DoE.validate(features=feat):
                out_of_doe_candidates.append(struct)
                continue  # skip to next structure

            # 2) Physical‐sanity check
            if self.ef_bounds is not None:
                apm = struct.AtomPositionManager
                if apm.E is not None and apm.atomCount != 0:
                    ef_per_atom = apm.E / apm.atomCount
                    if not self.ef_bounds[0] <= ef_per_atom <= self.ef_bounds[1]:
                        physically_invalid_candidates.append(struct)
                        continue

            # 2) blacklist_detector check
            try:
                present, tag = self.blacklist_detector.contains(struct, remove=remove)
            except Exception as ex:
                # Fail-soft: proceed with other checks; optionally log when debug
                if True or self.debug:
                    print(f"[validate_candidates] blacklist check error: {ex}")
                present, tag = (False, None)

            if present:
                # Optionally annotate offending motif for auditability
                apm = struct.AtomPositionManager
                md = getattr(apm, "metadata", None)
                if isinstance(md, dict):
                    md["blacklist_hit"] = tag
                elif hasattr(apm, "metadata"):
                    try:
                        apm.metadata = {"blacklist_hit": tag}
                    except Exception:
                        pass
                blacklist_invalid_candidates.append(struct)
                continue

            # 4) Survives all checks
            valid_candidates.append(struct)

        # --- Export invalid groups (mirroring your existing behavior) ---

        # 3a) Export any out_of_doe invalid individuals
        if out_of_doe_candidates:
            invalid_dataset = Partition()
            invalid_dataset.add_container( out_of_doe_candidates )
            self.export_structures(
                invalid_dataset,
                f'{self.output_path}/out_of_doe.xyz'
            )

        # 3b) Export any physically invalid individuals
        if physically_invalid_candidates:
            invalid_dataset = Partition()
            invalid_dataset.add_container( physically_invalid_candidates )
            self.export_structures(
                invalid_dataset,
                f'{self.output_path}/physically_invalid.xyz'
            )

        if blacklist_invalid_candidates:
            invalid_dataset = Partition()
            invalid_dataset.add_container(blacklist_invalid_candidates)
            self.export_structures(invalid_dataset, f"{self.output_path}/blacklisted.xyz")

        return valid_candidates, out_of_doe_candidates+physically_invalid_candidates+blacklist_invalid_candidates 

    def filter_hash_collisions(self, individuals:list, force_rehash:bool=True):
        """
        Filters out individuals that collide in the hash map (i.e., duplicates).

        Parameters
        ----------
        individuals : list
            List of candidate individuals after the physical model.

        Returns
        -------
        unique_structures : list
            Structures that are unique (not in the hash map).
        """

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
            g = 1 #reduce(gcd, counts) or 1                       # robust gcd
            return "-".join(
                f"{el}{int(comp[el] // g)}"                    # always include ‘1’
                for el in sorted(comp)
            )

        if not self._filter_duplicates:
            return individuals, []

        unique_structures = []
        not_unique_structures = []
        for individual in individuals:
            hash_ = self.hash_map.get_hash(individual, force_rehash=force_rehash)

            '''
            # deduplicate a batch of candidate payload-hashes in one shot
            seen = composite_store.has_hashes(batch_hashes)
            new_candidates = [cand for cand in candidates if not seen[cand.hash]]
            '''

            if not self.get_dataset('dataset').has_hash(hash_):
                unique_structures.append(individual)
                continue

            elif force_rehash:
                dataset = Partition()
                dataset.add_container(individual)
                
                comp_key = _composition_key(individual.AtomPositionManager.atomCountDict)
                self.export_structures(
                    dataset=dataset,
                    file_path=f'{self._output_path}/basin/{comp_key}/{individual.AtomPositionManager.metadata["hash"]}/config_basin.xyz',
                )

            not_unique_structures.append(individual)

        return unique_structures, not_unique_structures


    def filter_selfcollision(self, individuals:list, remove:bool=False):
        """
        Filters out individuals that have self-collision above the collision factor threshold.

        Parameters
        ----------
        individuals : list
            List of candidate individuals to filter.

        Returns
        -------
        non_colliding : list
            Filtered list of individuals without self-collisions.
        """
        if self.collision_factor < 1e-6:
            return individuals, []

        # 1) Compute collision mask in one pass (C-optimized list comp)
        mask = [
            s.AtomPositionManager.self_collision(factor=self.collision_factor, remove=remove) 
            for s in individuals
        ]

        # 2) Use mask to filter in C-level loops
        non_colliding = [s for s, m in zip(individuals, mask) if not m]
        colliding = [s for s, m in zip(individuals, mask) if m]

        # 3) Export invalid individuals, if any
        if colliding:
            dataset = Partition()
            dataset.add_container( colliding )
            self.export_structures(
                dataset,
                f"{self.output_path}/selfcollision.xyz"
            )

        return non_colliding, colliding


    def update_main_dataset(
        self,
        dataset: list,
        generation: int,
        features_prev: np.ndarray,
        objectives_prev: np.ndarray,
    ) -> bool:
        """
        Updates the main dataset with new structures and records the structure IDs and generations.

        Parameters
        ----------
        dataset : object
            Newly generated unique structures.
        generation : int
            Current generation index.
        """

        cap  = self.size_limit
        ds   = self.get_dataset("dataset")
        discard_structs = []

        if not cap is None:
            # --- Global size population control --------------------------
            needed_size = ds.size + dataset.size
            if needed_size > cap: 
                excess = needed_size - cap

                old_containers   = list(ds.containers)

                # --- Rank only the *old* population --------------------------
                w       = np.ones(objectives_prev.shape[1])
                scores  = objectives_prev @ w                  # lower = better
                idx_bad = np.argsort(scores)[-excess:]         # worst performers
                idx_bad = [i for i in idx_bad if i < len(old_containers)]
                
                # Build keep / discard lists
                discard_structs  = [old_containers[i] for i in idx_bad]
                keep_structs_old = [
                    c for i, c in enumerate(old_containers) if i not in idx_bad
                ]

                # Export the overflow
                if discard_structs:
                    overflow = Partition()
                    overflow.add_container(discard_structs)
                    overflow.export_files(
                        file_location=f"{self.output_path}/config_overflow.xyz",
                        source="xyz",
                        label="enumerate",
                        verbose=True,
                    )

                # Replace the dataset with survivors
                ds.set_container(keep_structs_old)

        # --- 2) Insert the new generation (always survives) -------------- ###
        ds.add( list(dataset.containers) )
        
        return len(discard_structs)
        