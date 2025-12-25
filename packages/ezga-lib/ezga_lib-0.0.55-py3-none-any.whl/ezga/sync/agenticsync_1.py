"""hash_batch_sync.py
Content-addressable batch exchange backend.

This implementation fills in the missing pieces of *HashBatchSync* so it can be
used as a drop‑in component for your GA or worker processes.

Key features
------------
*   **Deterministic sharded directories** based on SHA‑256 of the buffer payload.
*   Thread‑safe public API (all mutating methods behind an *RLock*).
*   **Crash tolerant**: processed batch IDs are persisted to *seen.json*.
*   Optional pruning of old batches via *max_retained*.
*   Minimal external dependencies – only `Partition` from your own code base.

Usage example
-------------
```python
sync = HashBatchSync(shared_dir="/path/to/shared", max_buffer=2048)

sync.append(obj1)
sync.append(obj2)
...
# Flush manually if auto_publish=False
sync.flush()

# Consumer side
for batch_id, payload in sync.get_batch():
    ...
```
"""

from __future__ import annotations

import json
import hashlib
import pickle
import shutil
import time
import os
from pathlib import Path
from threading import RLock
from sage_lib.partition.Partition import Partition
from ezga.core.interfaces import IAgent

from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple

class Agentic_Sync(IAgent):
    """Batch‑exchange backend with *content‑addressed folders*.
    
    Parameters
    ----------
    shared_dir : str | Path
        Root directory on a shared filesystem where batches will be written.
    shard_width : int, default=2
        Number of leading hex digits of the digest used as sharding sub‑folder.
    max_buffer : int, default=8
        Flush automatically once this many objects have been appended.
    max_retained : int, optional
        Keep at most this many batch folders on disk (oldest are deleted).
        ``None`` disables pruning.
    persist_seen : bool, default=True
        Persist the *seen* index (``seen.json``) so a crash/restart does not
        re‑process the same batches.
    poll_interval : float, default=2.0
        Seconds between polls inside :meth:`watch` (exposed for future use).
    auto_publish : bool, default=True
        If *True*, :meth:`append` flushes automatically once ``max_buffer`` is
        reached.
    hash_name : str, default="sha256"
        Digest algorithm recognised by :pymod:`hashlib`.
    """

    _SEEN_FILE = "seen.json"

    # ------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------
    def __init__(
        self,
        *,
        shared_dir: str | Path,
        shard_width: int = 2,
        max_buffer: int = 4,
        max_retained: Optional[int] = None,
        persist_seen: bool = True,
        poll_interval: float = 2.0,
        auto_publish: bool = True,
        hash_name: str = "sha256",
        fetch_every: int = 5,
        default_fetch_limit: Optional[int] = None,
    ) -> None:

        # ── 1. root directory (try–convert) ───────────────────────────────────
        try:
            self.root = Path(shared_dir).expanduser().resolve()
            self.root.mkdir(parents=True, exist_ok=True)
        except (TypeError, AttributeError, OSError):
            # Any failure ⇒ disable backend (is_active → False)
            self.root = None

        # ── 2. hash-algorithm resolver / aliases ──────────────────────────────
        alias = {"hash": "sha256", "sha": "sha256", "sha256": "sha256", "md5": "md5"}
        algo  = alias.get(hash_name.lower().strip(), hash_name.lower().strip())

        if algo not in hashlib.algorithms_available:
            raise ValueError(
                f"Unsupported hash algorithm '{hash_name}'. "
                f"Available: {', '.join(sorted(hashlib.algorithms_available))}"
            )
        self._hash_name = hash_name

        # ── 3. misc configuration ─────────────────────────────────────────────
        self.shard_width = max(0, shard_width)
        self._max_buffer = max(1, max_buffer)
        self._max_retained = max_retained
        self.poll_interval = poll_interval
        self.auto_publish = auto_publish
        self._default_fetch_limit = default_fetch_limit

        self._fetch_counter = 0
        self._fetch_every = max(1, fetch_every)   

        self._buffer: List[Any] = []
        self._lock = RLock()

        # ── 4. seen-index handling ────────────────────────────────────────────
        self._persist_seen = persist_seen
        self._seen_path    = self.root / self._SEEN_FILE if self.root else None
        self._seen: Dict[str, int] = self._load_seen() if self._seen_path else {}


        # Time‑tracking for watch()/append()
        self._last_flush = time.monotonic()

    # ------------------------------------------------------------
    # Runtime status helpers
    # ------------------------------------------------------------
    def is_active(self) -> bool:  # noqa: D401 – keep simple name
        """Return ``True`` when the backend is ready to use.

        The check is simple and fast – we confirm that the *root* directory
        exists **and** is writable.  External components can therefore call
        either :meth:`is_active` or its alias :meth:`active` as a lightweight
        guard before interacting with the instance.
        """
        return (
            self.root is not None
            and self.root.is_dir()
            and os.access(self.root, os.W_OK)
        )

    # Backward‑compatibility alias
    active = is_active

    # ------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------
    def append(self, obj: Any) -> bool:
        """Stage *obj* into the in‑memory buffer.

        Returns ``True`` if the call triggered an automatic flush.
        """
        with self._lock:
            if isinstance(obj, list):
                self._buffer.extend(obj)
            else:
                self._buffer.append(obj)

            auto = False
            if self.auto_publish and len(self._buffer) >= self._max_buffer:
                self.flush()
                auto = True
            return auto

    def flush(self) -> str | None:
        """Write the current buffer to disk (if not empty) and reset state.

        Returns the *batch id* (digest string) that was written, or ``None`` when
        there was nothing to flush.
        """
        with self._lock:
            if not self._buffer:
                return None

            batch_id = self._publish_generation(self._buffer)
            self._buffer.clear()
            self._last_flush = time.monotonic()
            return batch_id

    def get_batch(
        self,
        *,
        prune: bool = True,
        sleep: float | None = None,
        fetch_limit: Optional[int] = None,   
    ) -> Generator[Tuple[str, Any], None, None]:
        """ 
        Yield unseen (batch_id, payload) pairs.

        Parameters
        ----------
        prune : bool, default=True
            Prune according to max_retained after each scan.
        sleep : float | None
            Optional sleep between polling iterations.
        fetch_limit : int | None
            Upper bound on the **sum of payload.size** across yielded batches
            in this call. If None, unlimited. Batches are not split.
        """

        # --- Throttle scans --------------------------------------------------
        self._fetch_counter = (self._fetch_counter + 1) % self._fetch_every
        if self._fetch_counter:
            if sleep is not None:
                time.sleep(sleep)
            return  # empty generator (no scan this turn)

        # resolve effective limit
        eff_limit = self._default_fetch_limit if fetch_limit is None else fetch_limit
        try:
            eff_limit = None if eff_limit is None else max(0, int(eff_limit))
        except (TypeError, ValueError):
            eff_limit = None

        yielded_structs = 0
        while True:

            for batch_path in self._discover_batches():
                if eff_limit is not None and yielded_structs >= eff_limit:
                    break

                batch_id = batch_path.name
                if batch_id in self._seen:
                    continue

                try:
                    payload = self._read_partition(batch_path)
                except FileNotFoundError:
                    # Directory vanished between discovery and read → skip silently
                    continue
                except Exception as exc:
                    # Optional: log and continue, in case Partition raises something else
                    print("[HashBatchSync] read failed:", exc)
                    continue

                # authoritative per-batch count
                try:
                    n_in_batch = int(getattr(payload, "size"))
                except Exception:
                    n_in_batch = len(getattr(payload, "containers", []))

                # do NOT split a batch; stop before exceeding the cap
                # Exit outer loop if limit reached or no polling requested
                if eff_limit is not None and yielded_structs + n_in_batch > eff_limit:
                    break

                self._seen[batch_id] = int(time.time())
                self._save_seen()
                yielded_structs += n_in_batch
                yield batch_id, payload

            # --- Prune once per scan ---------------------------------------
            if prune:
                self._prune_old()

            if sleep is None:
                break
            time.sleep(sleep)

    def update_behaviour(
        self,
        *,
        population: list = None,
        ctx: object = None,
    ) -> bool:
        """
        """
        return True

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------
    def _publish_generation(self, buffer: List[Any]) -> str:
        """Write *buffer* to a newly created sharded directory."""
        digest = self._hash_object_list(buffer)
        shard = digest[: self.shard_width] if self.shard_width else ""
        batch_dir = self.root / shard / digest

        if not batch_dir.exists():
            batch_dir.mkdir(parents=True, exist_ok=True)
            part = Partition()
            part.add_container(buffer)
            part.export_files(
                file_location=str(batch_dir),
                source="xyz",
                label="enumerate",
                verbose=False,
            )
        if digest not in self._seen:
            self._seen[digest] = int(time.time())
            self._save_seen()
        return digest

    def _discover_batches(self) -> List[Path]:
        """Return existing batch folders, sorted by mtime (oldest → newest).
        Directories that disappear during the scan are ignored to prevent
        FileNotFoundError races with concurrent pruning or external processes.
        """
        candidates: list[tuple[float, Path]] = []

        for path in self.root.rglob("*"):
            # Heuristic: final path component is a 64-hex SHA-256 digest.
            if len(path.parts[-1]) == 64 and path.is_dir():
                try:
                    mtime = path.stat().st_mtime        # may raise FileNotFoundError
                except FileNotFoundError:
                    continue                            # vanished between rglob and stat
                candidates.append((mtime, path))

        candidates.sort(key=lambda t: t[0])             # ascending mtime
        return [p for _, p in candidates]

    def _discover_batches(self) -> List[Path]:
        """Return existing batch folders (oldest → newest), robust to concurrent FS changes.

        We avoid recursive globbing and guard every FS touch so directories that
        disappear mid-scan are treated as benign.
        """
        candidates: list[tuple[float, Path]] = []
        root = self.root
        if not root or not root.exists():
            return []

        with self._lock:
            # 1) list shards (or the root itself if shard_width==0)
            try:
                if self.shard_width > 0:
                    try:
                        shards = [p for p in root.iterdir() if p.is_dir()]
                    except (FileNotFoundError, PermissionError, OSError):
                        shards = []
                    w = int(self.shard_width)
                    shards = [
                        s for s in shards
                        if len(s.name) == w and all(c in "0123456789abcdef" for c in s.name.lower())
                    ]
                else:
                    shards = [root]
            except (FileNotFoundError, PermissionError, OSError):
                shards = []

            # 2) list candidate batch dirs inside each shard
            for shard in shards:
                try:
                    entries = list(shard.iterdir())
                except (FileNotFoundError, PermissionError, OSError):
                    continue

                for batch in entries:
                    try:
                        if not batch.is_dir():
                            continue
                        name = batch.name
                        if len(name) != 64 or not all(c in "0123456789abcdef" for c in name.lower()):
                            continue
                        try:
                            mtime = batch.stat().st_mtime
                        except FileNotFoundError:
                            continue
                        candidates.append((mtime, batch))
                    except (FileNotFoundError, PermissionError, OSError):
                        continue

        candidates.sort(key=lambda t: t[0])  # oldest → newest
        return [p for _, p in candidates]

    def _read_partition(self, batch_path: Path) -> Any:
        """Load data from *batch_path* via Partition.read_files."""
        part = Partition()
        part.read_files(
            file_location=os.path.join(batch_path, "config.xyz"),
            source="xyz",
            verbose=False,
        )
        return part  # You may want to return part.containers[0] or similar

    # ---------------- Seen‑index persistence --------------------
    def _load_seen(self) -> Dict[str, int]:
        if not self._persist_seen or not self._seen_path.exists():
            return {}
        try:
            return json.loads(self._seen_path.read_text())
        except Exception:
            return {}

    def _save_seen(self) -> None:
        if not self._persist_seen:
            return

        tmp = self._seen_path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(self._seen, indent=2))
            tmp.replace(self._seen_path)
        except OSError as exc:
            # Log but do not crash—seen index will be retried next call.
            print("[HashBatchSync] failed to write seen.json:", exc)

    # ---------------- House‑keeping helpers ---------------------
    # ---------------- Shard‑aware pruning -----------------------
    def _prune_old(self) -> None:
        """Delete *excess* oldest batches, **max one per shard** per cycle.

        This keeps I/O balanced across shard sub‑directories and eliminates the
        possibility of wiping an entire shard in one go.
        """
        if self._max_retained is None:
            return

        all_batches = self._discover_batches()  # already sorted by mtime
        excess = len(all_batches) - self._max_retained
        if excess < 1:
            return

        to_delete: List[Path] = []
        visited_shards: set[Path] = set()
        for path in all_batches:
            shard = path.parent
            if shard in visited_shards:
                continue  # already selected one from this shard this round
            to_delete.append(path)
            visited_shards.add(shard)
            if len(to_delete) == excess:
                break

        for path in to_delete:
            try:
                shutil.rmtree(path, ignore_errors=True)
            except FileNotFoundError:
                # Already gone – benign.
                continue
            except Exception as exc:
                print("[HashBatchSync] prune failed:", exc)
                continue

            # House‑keeping after successful delete
            self._seen.pop(path.name, None)
            parent = path.parent
            if parent != self.root:
                try:
                    parent.rmdir()          # deletes only if shard is empty
                except OSError:
                    # ENOENT, ENOTEMPTY, or any other benign OS error
                    # can be ignored safely
                    pass

    def attempt_prune(
        self,
        *,
        interval: float = 60.0,   # seconds between prune attempts
        budget: int = 8,          # max batch dirs to delete per call
        min_age: float = 5.0,     # do not delete if younger than this (seconds)
    ) -> int:
        """
        Perform a **bounded, race-tolerant pruning cycle** of old batch folders.

        This method implements a *best-effort garbage collection* strategy that 
        removes only the **oldest and excess** batch directories, while ensuring 
        filesystem safety under concurrent readers/writers.

        Deletion is **rate-limited**, **age-guarded**, and **shard-balanced** to 
        avoid deleting freshly written data or overloading any particular subdirectory.

        ---------------------------------------------------------------------------
        Parameters
        ---------------------------------------------------------------------------
        interval : float, default=60.0
            Minimum elapsed time (in seconds) between consecutive prune attempts.
            The method will return immediately (without doing any work) if called
            again before `interval` seconds have passed since the previous execution.
            This throttling protects against excessive filesystem traversal during
            rapid batch production.

        budget : int, default=8
            Maximum number of batch directories to delete in a single pruning pass.
            Even if the number of excess batches greatly exceeds this value, the
            function will remove at most `budget` folders per call.  This bounds the
            I/O cost and improves fairness under concurrent workloads.

        min_age : float, default=5.0
            Minimum age (in seconds) of a batch directory required for eligibility.
            Directories younger than this threshold are **never deleted**, to prevent
            race conditions with in-flight write operations or recently published
            generations.  The age is computed as:

                age = time.time() - path.stat().st_mtime

        ---------------------------------------------------------------------------
        Returns
        ---------------------------------------------------------------------------
        int
            The number of batch directories successfully pruned during this call.

        ---------------------------------------------------------------------------
        Algorithmic steps
        ---------------------------------------------------------------------------
        1. **Throttle by interval**
           - Skip execution if less than `interval` seconds since `_last_prune`.
           - Record the timestamp of this pruning pass (`_last_prune = now`).

        2. **Check retention limit**
           - Gather all existing batch folders via `_discover_batches()`, which 
             returns a list sorted from oldest → newest (by modification time).
           - Compute `excess = len(all_batches) - self._max_retained`.
           - If `excess <= 0`, nothing is deleted.

        3. **Iterate oldest → newest**
           - Traverse `all_batches` in ascending `mtime` order.
           - Apply the following filters for each candidate batch folder `path`:
             - *Shard fairness*: delete at most one per shard per cycle.
             - *Age guard*: skip if `mtime` is younger than `min_age` seconds.
             - *Budget*: stop once `pruned >= budget`.
           - Only when **all conditions** are satisfied will the folder be deleted.

        4. **Deletion**
           - Attempt `shutil.rmtree(path, ignore_errors=True)`.
           - On success, remove the corresponding entry from `self._seen`.
           - Attempt to remove the shard directory if now empty (`shard.rmdir()`).

        5. **Race tolerance**
           - All filesystem operations are wrapped in `try/except` to absorb
             benign race conditions (e.g. another process deleting the same folder).
           - Non-fatal errors are logged to stdout but do not interrupt execution.

        ---------------------------------------------------------------------------
        Safety guarantees
        ---------------------------------------------------------------------------
        * Newly created batches are protected by the `min_age` guard.
        * The method never prunes more than one batch per shard in a single pass.
        * The number of deletions per call is bounded by `budget`.
        * It will never run more often than every `interval` seconds.
        * No pruning occurs when `self._max_retained` is `None` or not exceeded.
        * Locks (`self._lock`) prevent concurrent mutation of shared state.

        ---------------------------------------------------------------------------
        Notes
        ---------------------------------------------------------------------------
        * The `self._seen` dictionary is updated (entries removed) but not persisted
          to disk until the next `_save_seen()` call.  To keep `seen.json` in sync,
          consider invoking `_save_seen()` after pruning.
        * The selection order is deterministic with respect to modification time;
          oldest eligible batches are always deleted first.
        * The function is safe for concurrent use by multiple workers sharing the
          same `shared_dir`, though each worker will redundantly scan the filesystem.

        ---------------------------------------------------------------------------
        Example
        ---------------------------------------------------------------------------
        >>> sync = Agentic_Sync(shared_dir="~/shared_batches", max_retained=20)
        >>> pruned = sync.attempt_prune(interval=30.0, budget=4, min_age=10.0)
        >>> print(f"Removed {pruned} obsolete batch folders.")
        """
        if self._max_retained is None:
            return 0

        now = time.monotonic()
        last = getattr(self, "_last_prune", 0.0)
        if now - last < interval:
            return 0

        with self._lock:
            self._last_prune = now

            all_batches = self._discover_batches()  # already sorted oldest → newest
            excess = len(all_batches) - self._max_retained
            if excess <= 0:
                return 0

            # Bound the amount of work we attempt this round
            target = min(excess, max(1, int(budget)))

            pruned = 0
            visited_shards: set[Path] = set()

            for path in all_batches:
                if pruned >= target:
                    break

                shard = path.parent
                if shard in visited_shards:
                    continue  # only 1 per shard per cycle

                # age filter: skip very new entries to avoid touching in-flight writes
                try:
                    if (time.time() - path.stat().st_mtime) < float(min_age):
                        continue
                except FileNotFoundError:
                    continue

                # attempt deletion
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except FileNotFoundError:
                    # Already gone – benign.
                    continue
                except Exception as exc:
                    print("[HashBatchSync] prune failed:", exc)
                    continue

                # housekeeping after successful delete
                self._seen.pop(path.name, None)
                visited_shards.add(shard)
                pruned += 1

                # try to remove empty shard dir; ignore failures
                if shard != self.root:
                    try:
                        shard.rmdir()
                    except OSError:
                        pass

            return pruned

    # ---------------- Static utilities --------------------------
    def _hash_object_list(self, objs: Sequence[object]) -> str:
        payload = pickle.dumps(objs, protocol=4)
        digest = hashlib.new(self._hash_name)
        digest.update(payload)
        return digest.hexdigest()
