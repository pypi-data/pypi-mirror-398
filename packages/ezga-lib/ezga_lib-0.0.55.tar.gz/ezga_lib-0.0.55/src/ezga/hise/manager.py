# ezga/hise/manager.py
# SPDX-License-Identifier: GPL-3.0-only
"""
HiSE (Hierarchical Supercell Escalation) manager.

Lift methods (hise.lift_method):
  - "tile":            Use Partition + AtomPositionManager.generate_supercell(repeat=...).
  - "best_compatible": Pick the largest previous supercell (by volume) that divides the
                       target coord-wise, then lift via Partition as above.
  - "ase":             Fallback method using ASE Atoms.repeat (no Partition required).

Both "tile" and "best_compatible" REQUIRE `sage_lib.partition.Partition`.
"""

from __future__ import annotations
from typing import Tuple, List, Dict, Any, Optional
from pathlib import Path
import logging
import numpy as np
import os, shutil, re

from ase import Atoms
from ase.io import read as ase_read, write as ase_write

from sage_lib.IO.storage.hybrid import HybridStorage  # <-- REQUIRED
from sage_lib.partition.Partition import Partition  # <-- REQUIRED

from ezga.core.config import GAConfig, HiSEParams
from ezga.factory import build_default_engine
from ezga.io.config_loader import _materialize_factories  
from .metadata import _StageMetadata

logger = logging.getLogger(__name__)

def _materialize_stage_constraints_if_any(stage_cfg: GAConfig) -> None:
    """Normalize and materialize ``population.constraints`` into callables.

    This helper fixes two common situations that arise when constraints are
    provided via YAML overrides on a per-stage basis:

    1) **Single dict instead of list**  
       Some YAMLs assign one factory-spec (a dict) to ``population.constraints``
       for a given stage (e.g., via an overrides array). The population expects a
       *list* of callables, so we wrap a single dict into a list.

    2) **Unmaterialized factory-specs**  
       Constraints may appear as factory-specs (e.g.,
       ``{"factory": "pkg.mod:make_constraint", "args": [...], ...}``) or dotted
       references. We convert them into *live Python callables* using the same
       materializer employed by the config loader.

    If a mapping ``population.constraint_name_map`` is present (e.g., ``{"C": 0,
    "H": 1}``), we register it with ``ConstraintGenerator.set_name_mapping`` so
    any constraint that accepts *string* feature keys (like ``"C"``/``"H"``) can
    resolve them to integer indices at runtime.

    The function mutates ``stage_cfg`` in place and is safe to call multiple times.

    Args:
      stage_cfg: Stage-local :class:`GAConfig` that will be mutated in place.

    Returns:
      None

    Notes:
      - Input shapes accepted:
        * ``None`` → no-op
        * a single dict factory-spec → wrapped as a list, then materialized
        * a list/tuple of factory-specs or callables → materialized element-wise
        * already-live callables → left as-is
      - This uses ``_materialize_factories`` from the loader to keep behavior
        consistent with top-level YAML parsing.
    """
    pop = getattr(stage_cfg, "population", None)
    if pop is None:
        return

    cons = getattr(pop, "constraints", None)
    if cons is None:
        return

    # 1) Tolerate a single dict by wrapping it as a list.
    if isinstance(cons, dict):
        cons = [cons]
    elif isinstance(cons, tuple):
        cons = list(cons)

    # 2) Materialize a list of factory-specs/dotted refs into live callables.
    if isinstance(cons, list):
        try:
            pop.constraints = _materialize_factories(cons)
        except Exception as e:
            logger.warning("[HiSE] Failed to materialize population.constraints: %s", e)
            # Keep the original value so downstream code can decide how to react.
            pop.constraints = cons

    # Optional: register a name→index mapping for string feature keys ("C", "H", ...).
    cmap = getattr(pop, "constraint_name_map", None)
    if cmap:
        try:
            # Local import to avoid import-time cycles and heavy modules at import.
            from ezga.DoE.DoE import ConstraintGenerator
            ConstraintGenerator.set_name_mapping(dict(cmap))
        except Exception as e:
            logger.warning("[HiSE] Could not register constraint_name_map on ConstraintGenerator: %s", e)

def _lift_inputs(
    method: str,
    src_path: Path,
    dst_path: Path,
    ratio: Optional[Tuple[int, int, int]],
    reseed_fraction: float,
    rng: np.random.Generator,
) -> Optional[Path]:
    """
    Generate a supercell-expanded database from an existing HybridStorage directory.

    Args:
        method: Name of the lift method ("tile", "ase", etc.) — currently only "tile" supported.
        path: Source stage directory containing the original HybridStorage database.
        ratio: Tuple (a, b, c) replication factors for each lattice direction.
        reseed_fraction: Fraction of entries to retain (currently unused here).
        rng: Random number generator (for future stochastic selection support).

    Returns:
        Path to the newly generated supercell database, or None if operation failed.
    """
    if ratio is None:
        logger.warning("[HiSE] No valid ratio provided for _lift_inputs; skipping supercell generation.")
        return None

    src_path = Path(src_path).resolve()
    if not src_path.exists():
        logger.warning(f"[HiSE] Source database path does not exist: {src_path}")
        return None

    try:
        logger.info(
            f"[HiSE] Generating supercell database: {src_path.name} → {dst_path.name} (repeat={ratio})"
        )
        HybridStorage.generate_supercells(
            src_root=str(src_path),
            dst_root=str(dst_path),
            repeat=tuple(int(x) for x in ratio),
            # mode="parallel",  # optional future parallelization
            # max_workers=8,
        )
        logger.info(f"[HiSE] Supercell generation completed successfully at {dst_path}")
        return dst_path

    except Exception as e:
        logger.exception(f"[HiSE] Failed to generate supercell database from {src_path}: {e}")
        return None

# ---------------------------------------------------------------------
# Path & discovery helpers
# ---------------------------------------------------------------------
def _stage_dir(root: Path, sc: Tuple[int, int, int], pattern: str) -> Path:
    """Return absolute stage directory path."""
    a, b, c = map(int, sc)
    return (root / pattern.format(a=a, b=b, c=c)).resolve()

def _detect_stage_inputs(stage_root: Path, mode: str) -> List[Path]:
    """
    Return input XYZ files according to `mode` for a given stage directory.

    Supported modes:
      - "final_dataset": stage_root/config_all.xyz (preferred), fallback to stage_root/config.xyz
      - "generation":    stage_root/generation/gen*/config_g*.xyz (numeric-ordered), 
                         fallback to stage_root/generation/*/config.xyz
      - "basin":         stage_root/basin/*/*/config_basin.xyz
    """
    stage_root = Path(stage_root)

    if mode == "final_dataset":
        return stage_root

    if mode == "generation":
        gen_root = stage_root / "generation"
        if not gen_root.exists():
            return []

        # New naming: generation/genN/config_gN.xyz
        candidates = list(gen_root.glob("gen*/config_g*.xyz"))
        if not candidates:
            # Backward compatibility: generation/*/config.xyz
            candidates = list(gen_root.glob("*/config.xyz"))

        def _gen_index(path: Path) -> int:
            # Prefer N from filename (config_gN.xyz); fallback to dir name (genN).
            m = re.search(r"(\d+)", path.stem)
            if m:
                return int(m.group(1))
            m = re.search(r"(\d+)", path.parent.name)
            return int(m.group(1)) if m else -1

        return sorted(candidates, key=lambda p: (_gen_index(p), str(p)))

    if mode == "basin":
        basin_root = stage_root / "basin"
        if not basin_root.exists():
            return []
        # basin/<species>/<hash>/config_basin.xyz
        candidates = list(basin_root.glob("*/*/config_basin.xyz"))
        # Stable order: by species folder then hash, then filename
        return sorted(candidates, key=lambda p: (p.parents[1].name, p.parent.name, p.name))

    raise ValueError(f"Unsupported mode: {mode!r}")

def _get_stage_status(stage_root: Path) -> Optional[str]:
    """
    Return the current status string from metadata.json, or None if not present.
    """
    meta_path = Path(stage_root) / "metadata.json"
    if not meta_path.exists():
        return None
    try:
        meta = _StageMetadata.read(stage_root)
        return meta.get("status", None)
    except Exception as e:
        logger.warning(f"[HiSE] Could not read stage metadata at {stage_root}: {e}")
        return None

def _ratio_or_raise(next_sc: Tuple[int, int, int], prev_sc: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Compute integer replication ratio next/prev; raise if not an exact divisor."""
    r: List[int] = []
    for n, p in zip(next_sc, prev_sc):
        if p == 0 or (n % p) != 0:
            raise ValueError(f"Target supercell {next_sc} is not an integer multiple of {prev_sc}")
        r.append(n // p)
    return tuple(r)  # type: ignore[return-value]


def _best_compatible_source(
    target: Tuple[int, int, int],
    candidates: List[Tuple[int, int, int]],
) -> Optional[Tuple[int, int, int]]:
    """Pick volume-maximizing candidate that divides `target` coord-wise."""
    best: Optional[Tuple[int, int, int]] = None
    best_vol = -1
    ta, tb, tc = target
    for ca, cb, cc in candidates:
        if (ta % ca == 0) and (tb % cb == 0) and (tc % cc == 0):
            vol = ca * cb * cc
            if vol > best_vol:
                best = (ca, cb, cc)
                best_vol = vol
    return best

def _is_commensurate(target: Tuple[int, int, int], prev: Tuple[int, int, int]) -> bool:
    """Return True if each target coord is an integer multiple of prev coord."""
    ta, tb, tc = target
    pa, pb, pc = prev
    return (pa != 0 and tb % pb == 0 and tc % pc == 0 and ta % pa == 0)

def _compute_stage_shared_dir(base_shared: Path, out_root: Path, stage_root: Path) -> Path:
    """Make a stage-shared mailbox path (common to all agents of the stage)."""
    try:
        rel = stage_root.relative_to(out_root)
    except Exception:
        rel = Path(stage_root.name)
    return (base_shared / rel).resolve()

# ---------------------------------------------------------------------
# Lift implementations (Partition / ASE)
# --------------------------------------------------------------------- 



# ---------------------------------------------------------------------
# Config utilities
# ---------------------------------------------------------------------
def _deep_set(cfg: GAConfig, dotted_key: str, value: Any) -> None:
    """Set nested value on a GAConfig using dotted-path keys."""
    obj: Any = cfg
    parts = dotted_key.split(".")
    for k in parts[:-1]:
        obj = getattr(obj, k)
    setattr(obj, parts[-1], value)


def _apply_stage_overrides(stage_cfg: GAConfig, overrides: Dict[str, List[Any]] | None, idx: int) -> None:
    """Apply per-stage overrides (dot path → list of values), if present."""
    if not overrides:
        return
    for dotted_key, values in overrides.items():
        if idx < len(values):
            _deep_set(stage_cfg, dotted_key, values[idx])


def _adjust_stage_scoped_paths(stage_cfg: GAConfig, out_root: Path, stage_root: Path) -> None:
    """Set output_path and agentic.shared_dir for the given stage.

    The agentic.shared_dir becomes a *stage-shared* mailbox:
      base_shared / stage_root.relative_to(out_root)
    """
    stage_cfg.output_path = str(stage_root)
    try:
        if stage_cfg.agentic and stage_cfg.agentic.shared_dir:
            base_shared = Path(stage_cfg.agentic.shared_dir)
            stage_shared = _compute_stage_shared_dir(base_shared, out_root, stage_root)
            stage_shared.mkdir(parents=True, exist_ok=True)
            stage_cfg.agentic.shared_dir = str(stage_shared)
    except Exception:
        pass


# ---------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------
def run_hise(cfg: GAConfig) -> Dict[Tuple[int, int, int], Path]:
    """Execute a HiSE (coarse-to-fine) campaign.

    For each supercell stage:
      * Build an isolated stage directory.
      * Optionally **replace** the base input by lifting (tiling) previous results
        according to `hise.lift_method` and `hise.input_from`.
      * Apply per-stage overrides.
      * Scope agentic.shared_dir to a stage-shared mailbox directory.
      * Skip completed stages if `hise.restart=True`.
      * Run the GA.

    Lift methods:
      - "tile":            Partition lifting by generate_supercell (immediate previous).
      - "best_compatible": Partition lifting from the largest prior stage that divides target.
      - "ase":             ASE fallback (Atoms.repeat).

    Returns:
      Mapping from supercell tuple → stage directory Path.
    """
    assert cfg.hise and cfg.hise.supercells, "HiSE requires a non-empty list of supercells."
    hise: HiSEParams = cfg.hise

    supercells = [tuple(map(int, sc)) for sc in hise.supercells]
    out_root = Path(cfg.output_path).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    stage_dirs: Dict[Tuple[int, int, int], Path] = {}
    done_sc: List[Tuple[int, int, int]] = []   # stages already completed (for best_compatible)
    rng = np.random.default_rng(73)

    for idx, sc in enumerate(supercells):
        stage_root = _stage_dir(out_root, sc, hise.stage_dir_pattern)
        stage_dirs[sc] = stage_root
        stage_root.mkdir(parents=True, exist_ok=True)

        # Build a deep-copied stage-local config
        stage_cfg: GAConfig = cfg.model_copy(deep=True)
        _apply_stage_overrides(stage_cfg, hise.overrides, idx)
        _materialize_stage_constraints_if_any(stage_cfg)

        if "max_generations" not in (hise.overrides or {}):
            stage_cfg.max_generations = cfg.max_generations
        _adjust_stage_scoped_paths(stage_cfg, out_root, stage_root)

        # --- determine state ---
        stage_status = _get_stage_status(stage_root)

        # A — completed → skip
        # Restart/skip if the stage sentinel exists
        if hise.restart and stage_status == "completed":
            logger.info(f"[HiSE] Skipping completed stage {sc} at {stage_root}")
            done_sc.append(sc)
            continue

        # B — incomplete / failed → resume
        elif stage_status in ("running", "failed"):
            logger.info(f"[HiSE] Resuming incomplete stage {sc} at {stage_root}")
            # You can choose whether to reset metadata or just continue
            print(stage_cfg.max_generations)
            meta = _StageMetadata(stage_root, sc, stage_cfg.max_generations)
            meta.write(status="restarted")

        # C — not initialized → prepare (possibly upscale input)
        elif stage_status is None:
            logger.info(f"[HiSE] Initializing new stage {sc} at {stage_root}")

            # Replace base input from previous results for idx>0
            if idx > 0:
                source_sc: Optional[Tuple[int, int, int]] = _best_compatible_source(sc, done_sc)
                if source_sc is None:
                    logger.warning(f"[HiSE] No compatible previous stage found for target {sc}; proceeding unscaled.")
                else:
                    src_root = _stage_dir(out_root, source_sc, hise.stage_dir_pattern)
                    try:
                        ratio = _ratio_or_raise(sc, source_sc)
                    except ValueError:
                        logger.warning(
                            f"[HiSE] Source {source_sc} not commensurate with target {sc}; skipping upscale."
                        )
                        ratio = None

                    if ratio is not None:
                        _lift_inputs(
                            method=hise.lift_method,
                            src_path=src_root,
                            dst_path=stage_root,
                            ratio=ratio,
                            reseed_fraction=float(hise.reseed_fraction),
                            rng=rng,
                        )

        try:
            stage_cfg.population.db_path = stage_root
            
            if idx > 0: 
                stage_cfg.population.dataset_path = None
                stage_cfg.population.db_ro_path = Path(stage_root) / "db_ro"
                
        except Exception as e:
            logger.warning(f"[HiSE] Direct preload from Partition not available/failed: {e}. "
                           f"Falling back to dataset_path.")

        logger.info(f"[HiSE] Stage {idx+1}/{len(supercells)} — SC={sc} → {stage_root}")
        engine = build_default_engine(stage_cfg)

        # Initialize metadata tracker
        meta = _StageMetadata(stage_root, sc, stage_cfg.max_generations)
        meta.write(status="running")

        try:
            _ = engine.run()
            meta.write(
                status="completed",
                generation=getattr(engine.ctx, "generation", stage_cfg.max_generations),
                converged=getattr(engine.ctx, "is_converge", None),
                elapsed_seconds=getattr(engine.ctx, "elapsed", lambda _: 0)("engine"),
            )
            done_sc.append(sc)

        except Exception as e:
            logger.exception(f"[HiSE] Stage {sc} failed: {e}")
            meta.write(status="failed", error=str(e))
            continue

    return stage_dirs


    