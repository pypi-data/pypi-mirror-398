# logger.py
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.interfaces import ILogger

class WorkflowLogger(ILogger):
    """
    Workflow logger for structured logging within workflows.

    This class provides a simple wrapper around Python's built-in logging
    system, ensuring that workflow-related messages are consistently formatted
    and written to a log file located at the specified output path.
    """
    def __init__(self, output_path:str = '.'):
        """
        Workflow logger for structured logging and metadata tracking within workflows.

        Extends the traditional text log with a synchronized `metadata.json` file
        that records workflow progress, status, and key metrics. This allows external
        monitoring tools (e.g., HiSE or dashboards) to detect completion, failure,
        or convergence states in real time.

        Args:
            output_path (str): Path to the directory where the log file will be stored.
                               Defaults to the current directory '.'.
        """
        self.output_path = Path(output_path or ".").resolve()
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.logger = self.setup_logger("workflow", str(self.output_path))
        self.metadata_file = self.output_path / "metadata.json"

    # ------------------------------------------------------------
    # Setup and basic logging
    # ------------------------------------------------------------
    @staticmethod
    def setup_logger(name: str, output_path: str) -> logging.Logger:
        """
        Configure and return a logger instance for the workflow.

        This method ensures that the logging directory exists, creates a file
        handler for persistent logging, and applies a standard log format.
        If the logger already has handlers, no additional handlers are added
        to prevent duplicate log entries.

        Args:
            name (str): The name of the logger instance.
            output_path (str): Directory where the log file will be stored.

        Returns:
            logging.Logger: Configured logger instance ready for use.
        """

        output_path = output_path or self.output_path

        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Create and configure logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Define log file location
        log_file = os.path.join(output_path, 'workflow.log')

        # Create file handler
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Avoid adding multiple handlers to the same logger
        if not logger.handlers:
            logger.addHandler(handler)

        return logger

    # ------------------------------------------------------------
    # Metadata utilities
    # ------------------------------------------------------------
    def _read_metadata(self) -> Dict[str, Any]:
        """Read metadata.json if it exists."""
        if not self.metadata_file.exists():
            return {}
        try:
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_metadata(self, data: Dict[str, Any]) -> None:
        """Write metadata.json atomically."""
        data["last_update"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        tmp = self.metadata_file.with_suffix(".tmp")
        try:
            with open(tmp, "w") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self.metadata_file)
        except Exception as e:
            self.logger.warning(f"[Logger] Could not write metadata: {e}")

    # ------------------------------------------------------------
    # Public API for metadata tracking
    # ------------------------------------------------------------
    def init_metadata(
        self,
        stage: Optional[str] = None,
        max_generations: Optional[int] = None,
    ) -> None:
        """Initialize metadata file at the start of a workflow."""
        data = {
            "status": "running",
            "stage": stage or str(self.output_path),
            "generation": 0,
            "max_generations": max_generations,
            "n_structures": 0,
            "converged": False,
            "stagnation": 0,
        }
        self._write_metadata(data)
        self.logger.info("[Logger] Metadata initialized.")

    def update_metadata(
        self,
        generation: Optional[int] = None,
        n_structures: Optional[int] = None,
        converged: Optional[bool] = None,
        stagnation: Optional[int] = None,
        elapsed_seconds: Optional[float] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update metadata file with current progress."""
        data = self._read_metadata()
        if generation is not None:
            data["generation"] = generation
        if n_structures is not None:
            data["n_structures"] = n_structures
        if converged is not None:
            data["converged"] = bool(converged)
        if stagnation is not None:
            data["stagnation"] = stagnation
        if elapsed_seconds is not None:
            data["elapsed_seconds"] = float(elapsed_seconds)
        if status:
            data["status"] = status
        self._write_metadata(data)

    def mark_completed(self, converged: bool, elapsed_seconds: float) -> None:
        """Mark the workflow as completed."""
        data = self._read_metadata()
        data.update({
            "status": "completed",
            "converged": bool(converged),
            "elapsed_seconds": float(elapsed_seconds),
        })
        self._write_metadata(data)
        self.logger.info("[Logger] Workflow marked as completed.")

    def mark_failed(self, error: Optional[str] = None) -> None:
        """Mark the workflow as failed."""
        data = self._read_metadata()
        data["status"] = "failed"
        if error:
            data["error_message"] = str(error)
        self._write_metadata(data)
        self.logger.error("[Logger] Workflow marked as failed.")
