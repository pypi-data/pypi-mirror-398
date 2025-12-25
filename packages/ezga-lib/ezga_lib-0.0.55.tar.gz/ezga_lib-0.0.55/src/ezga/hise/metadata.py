from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional

class _StageMetadata:
    """Lightweight per-stage metadata writer used by HiSE only."""
    def __init__(self, stage_root: Path, sc: Tuple[int, int, int], max_generations: int):
        self.stage_root = Path(stage_root)
        self.path = self.stage_root / "metadata.json"
        self.data = {
            "status": "initializing",
            "stage": f"SC_{sc}",
            "generation": 0,
            "max_generations": int(max_generations),
            "last_update": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

    def write(self, **updates):
        """Atomically write updated metadata."""
        self.data.update(updates)
        self.data["last_update"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        tmp = self.path.with_suffix(".tmp")
        try:
            with open(tmp, "w") as f:
                json.dump(self.data, f, indent=2)
            tmp.replace(self.path)
        except Exception as e:
            logging.warning(f"[HiSE] Could not write metadata: {e}")

    @staticmethod
    def read(stage_root: Path):
        path = Path(stage_root) / "metadata.json"
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
