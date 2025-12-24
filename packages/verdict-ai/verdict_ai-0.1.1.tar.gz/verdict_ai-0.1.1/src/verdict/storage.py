"""Storage and file management for Verdict artifacts."""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class StorageManager:
    """Manages persistent storage of decision artifacts."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize storage manager.

        Args:
            base_dir: Base directory for storage (defaults to ~/.verdict/)
        """
        if base_dir is None:
            base_dir = Path.home() / ".verdict"

        self.base_dir = Path(base_dir)
        self.decisions_dir = self.base_dir / "decisions"
        self.plans_dir = self.base_dir / "plans"
        self.state_dir = self.base_dir / "state"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create directory structure if it doesn't exist."""
        for directory in [
            self.base_dir,
            self.decisions_dir,
            self.plans_dir,
            self.state_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def _generate_timestamp(self) -> str:
        """Generate timestamp string for filenames.

        Returns:
            Timestamp in YYYYMMDD-HHMMSS format
        """
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    def _atomic_write(self, file_path: Path, content: str) -> None:
        """Write file atomically to prevent corruption.

        Writes to temporary file first, then renames to final destination.
        The rename operation is atomic on most filesystems.

        Args:
            file_path: Destination file path
            content: Content to write

        Raises:
            OSError: If write or rename fails
        """
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file in same directory (ensures same filesystem)
        fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent, prefix=".tmp-", suffix=file_path.suffix
        )

        try:
            # Write content to temporary file
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                # Ensure data is flushed to disk
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename to final destination
            os.replace(temp_path, file_path)

        except Exception:
            # Clean up temporary file if anything fails
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def save_artifacts(
        self, decision_id: str, artifacts: Dict[str, str]
    ) -> Dict[str, Path]:
        """Save all artifacts to disk with timestamped filenames.

        Args:
            decision_id: Unique decision ID (for reference)
            artifacts: Dictionary with keys: decision_json, todo_md, state_json

        Returns:
            Dictionary mapping artifact type to saved file path

        Raises:
            OSError: If file write fails
            KeyError: If required artifact keys are missing
        """
        timestamp = self._generate_timestamp()
        saved_paths = {}

        # Save decision.json
        decision_filename = f"{timestamp}-{decision_id}-decision.json"
        decision_path = self.decisions_dir / decision_filename
        self._atomic_write(decision_path, artifacts["decision_json"])
        saved_paths["decision"] = decision_path

        # Save todo.md
        todo_filename = f"{timestamp}-{decision_id}-plan.md"
        todo_path = self.plans_dir / todo_filename
        self._atomic_write(todo_path, artifacts["todo_md"])
        saved_paths["plan"] = todo_path

        # Save state.json
        state_filename = f"{timestamp}-{decision_id}-state.json"
        state_path = self.state_dir / state_filename
        self._atomic_write(state_path, artifacts["state_json"])
        saved_paths["state"] = state_path

        return saved_paths

    def get_latest_state(self) -> Optional[Path]:
        """Get path to most recent state file.

        Returns:
            Path to latest state.json file, or None if no states exist
        """
        state_files = sorted(self.state_dir.glob("*-state.json"))
        return state_files[-1] if state_files else None

    def list_decisions(self, limit: Optional[int] = None) -> list[Path]:
        """List decision files, sorted by timestamp (newest first).

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of paths to decision.json files
        """
        decisions = sorted(
            self.decisions_dir.glob("*-decision.json"), reverse=True
        )
        return decisions[:limit] if limit else decisions
