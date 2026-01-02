#!/usr/bin/env python3
"""
Temporary Directory Manager for Agentic Development

Provides structured, secure, and automatically pruned temporary directory management
for task and subtask level context in agentic workflows.
"""

import os
import shutil
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from threading import Lock
import logging

logger = logging.getLogger(__name__)

@dataclass
class TmpConfig:
    """Configuration for temporary directory management."""
    base_tmp_dir: Path = Path("/tmp/agentic_projects")
    max_age_hours: int = 1  # Prune directories older than this
    prune_interval_minutes: int = 30  # How often to run pruning
    max_project_dirs: int = 100  # Maximum number of project directories to keep

class TmpManager:
    """
    Manages temporary directories for agentic projects with automatic pruning.

    Structure:
    /tmp/agentic_projects/
    ├── project_name_hash/
    │   ├── task_id/
    │   │   ├── subtask_id/
    │   │   │   ├── context.json
    │   │   │   └── data.bin
    │   │   └── another_subtask/
    │   └── another_task/
    └── another_project/
    """

    def __init__(self, project_name: str, config: Optional[TmpConfig] = None):
        self.project_name = project_name
        self.config = config or TmpConfig()
        self.project_hash = hashlib.sha256(project_name.encode()).hexdigest()[:16]
        self.project_tmp_dir = self.config.base_tmp_dir / self.project_hash
        self._lock = Lock()
        self._last_prune = 0

        # Ensure base directory exists
        self.config.base_tmp_dir.mkdir(parents=True, exist_ok=True)

        # Create project directory
        self.project_tmp_dir.mkdir(exist_ok=True)

    def get_task_dir(self, task_id: str) -> Path:
        """Get the temporary directory for a specific task."""
        task_dir = self.project_tmp_dir / task_id
        task_dir.mkdir(exist_ok=True)
        return task_dir

    def get_subtask_dir(self, task_id: str, subtask_id: str) -> Path:
        """Get the temporary directory for a specific subtask."""
        subtask_dir = self.get_task_dir(task_id) / subtask_id
        subtask_dir.mkdir(exist_ok=True)
        return subtask_dir

    def write_task_context(self, task_id: str, context: Dict[str, Any]) -> Path:
        """Write context data for a task."""
        task_dir = self.get_task_dir(task_id)
        context_file = task_dir / "context.json"
        import json
        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2)
        return context_file

    def read_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Read context data for a task."""
        context_file = self.get_task_dir(task_id) / "context.json"
        if context_file.exists():
            import json
            with open(context_file, 'r') as f:
                return json.load(f)
        return None

    def write_subtask_data(self, task_id: str, subtask_id: str, filename: str, data: bytes) -> Path:
        """Write binary data for a subtask."""
        subtask_dir = self.get_subtask_dir(task_id, subtask_id)
        file_path = subtask_dir / filename
        with open(file_path, 'wb') as f:
            f.write(data)
        return file_path

    def read_subtask_data(self, task_id: str, subtask_id: str, filename: str) -> Optional[bytes]:
        """Read binary data for a subtask."""
        file_path = self.get_subtask_dir(task_id, subtask_id) / filename
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return f.read()
        return None

    def cleanup_task(self, task_id: str):
        """Clean up all temporary data for a specific task."""
        task_dir = self.get_task_dir(task_id)
        if task_dir.exists():
            shutil.rmtree(task_dir)
            logger.info(f"Cleaned up task directory: {task_dir}")

    def cleanup_subtask(self, task_id: str, subtask_id: str):
        """Clean up temporary data for a specific subtask."""
        subtask_dir = self.get_subtask_dir(task_id, subtask_id)
        if subtask_dir.exists():
            shutil.rmtree(subtask_dir)
            logger.info(f"Cleaned up subtask directory: {subtask_dir}")

    def prune_old_directories(self):
        """Prune old temporary directories across all projects."""
        with self._lock:
            current_time = time.time()
            if current_time - self._last_prune < self.config.prune_interval_minutes * 60:
                return  # Not time to prune yet

            self._last_prune = current_time
            logger.info("Starting pruning of old temporary directories")

            pruned_count = 0
            for project_dir in self.config.base_tmp_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                # Check if project directory is too old
                try:
                    mtime = project_dir.stat().st_mtime
                    if current_time - mtime > self.config.max_age_hours * 3600:
                        shutil.rmtree(project_dir)
                        pruned_count += 1
                        logger.info(f"Pruned old project directory: {project_dir}")
                except OSError as e:
                    logger.warning(f"Error pruning {project_dir}: {e}")

            # Also limit total number of project directories
            project_dirs = sorted(
                [d for d in self.config.base_tmp_dir.iterdir() if d.is_dir()],
                key=lambda d: d.stat().st_mtime
            )

            if len(project_dirs) > self.config.max_project_dirs:
                to_remove = project_dirs[:-self.config.max_project_dirs]
                for old_dir in to_remove:
                    try:
                        shutil.rmtree(old_dir)
                        pruned_count += 1
                        logger.info(f"Pruned excess project directory: {old_dir}")
                    except OSError as e:
                        logger.warning(f"Error pruning {old_dir}: {e}")

            if pruned_count > 0:
                logger.info(f"Pruned {pruned_count} old temporary directories")

    def get_project_info(self) -> Dict[str, Any]:
        """Get information about the project's temporary usage."""
        total_size = 0
        file_count = 0
        dir_count = 0

        for root, dirs, files in os.walk(self.project_tmp_dir):
            dir_count += len(dirs)
            for file in files:
                file_path = Path(root) / file
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except OSError:
                    pass

        return {
            "project_name": self.project_name,
            "project_hash": self.project_hash,
            "tmp_dir": str(self.project_tmp_dir),
            "total_size_bytes": total_size,
            "file_count": file_count,
            "dir_count": dir_count,
            "last_modified": self.project_tmp_dir.stat().st_mtime if self.project_tmp_dir.exists() else None
        }

# Global instance for convenience
_default_managers: Dict[str, TmpManager] = {}

def get_tmp_manager(project_name: str, config: Optional[TmpConfig] = None) -> TmpManager:
    """Get or create a TmpManager instance for a project."""
    if project_name not in _default_managers:
        _default_managers[project_name] = TmpManager(project_name, config)
    manager = _default_managers[project_name]
    manager.prune_old_directories()  # Check for pruning on access
    return manager</content>
<parameter name="filePath">/home/spooky/Documents/projects/bootdisk/agentic-dev-boilerplate/tmp_manager.py