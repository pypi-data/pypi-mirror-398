"""Tests for tmp_manager module."""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import time
import json

from agentic_dev_boilerplate.tmp_manager import TmpManager, TmpConfig, get_tmp_manager


@pytest.fixture
def temp_base_dir(tmp_path):
    """Fixture for temporary base directory."""
    base_dir = tmp_path / "tmp_test"
    base_dir.mkdir()
    yield base_dir
    # Cleanup is handled by tmp_path


@pytest.fixture
def tmp_config(temp_base_dir):
    """Fixture for TmpConfig with test settings."""
    return TmpConfig(
        base_tmp_dir=temp_base_dir,
        max_age_hours=0.001,  # Very short for testing
        max_project_dirs=5
    )


@pytest.fixture
def tmp_manager(tmp_config):
    """Fixture for TmpManager instance."""
    return TmpManager("test_project", tmp_config)


@pytest.mark.parametrize("project_name", [
    "simple_project",
    "project-with-dashes",
    "project_with_underscores",
    "ProjectWithCamelCase",
    "project with spaces",  # Edge case
])
def test_initialization(project_name, tmp_config):
    """Test TmpManager initialization with various project names."""
    manager = TmpManager(project_name, tmp_config)
    assert manager.project_name == project_name
    assert manager.project_tmp_dir.exists()
    assert len(manager.project_hash) == 16  # SHA256 hex truncated to 16 chars


@pytest.mark.parametrize("task_id,subtask_id", [
    ("task_123", "subtask_456"),
    ("simple_task", "simple_subtask"),
    ("task-with-dashes", "subtask-with-dashes"),
    ("task_with_underscores", "subtask_with_underscores"),
])
def test_directory_creation(tmp_manager, task_id, subtask_id):
    """Test creating task and subtask directories."""
    task_dir = tmp_manager.get_task_dir(task_id)
    assert task_dir.exists()
    assert task_dir.name == task_id

    subtask_dir = tmp_manager.get_subtask_dir(task_id, subtask_id)
    assert subtask_dir.exists()
    assert subtask_dir.name == subtask_id
    assert subtask_dir.parent == task_dir


def test_context_persistence(tmp_manager):
    """Test writing and reading task context."""
    task_id = "test_task"
    context = {
        "status": "in_progress",
        "metadata": {"key": "value"},
        "timestamp": time.time()
    }

    tmp_manager.write_task_context(task_id, context)
    read_context = tmp_manager.read_task_context(task_id)

    assert read_context == context

    # Test reading non-existent context
    assert tmp_manager.read_task_context("non_existent") is None


def test_binary_data_persistence(tmp_manager):
    """Test writing and reading binary data."""
    task_id = "test_task"
    subtask_id = "test_subtask"
    filename = "data.bin"
    data = b"test binary data \x00\x01\x02"

    tmp_manager.write_subtask_data(task_id, subtask_id, filename, data)
    read_data = tmp_manager.read_subtask_data(task_id, subtask_id, filename)

    assert read_data == data

    # Test reading non-existent data
    assert tmp_manager.read_subtask_data(task_id, subtask_id, "non_existent.bin") is None


def test_cleanup_operations(tmp_manager):
    """Test cleanup of tasks and subtasks."""
    task_id = "test_task"
    subtask_id = "test_subtask"

    # Create directories and files
    task_dir = tmp_manager.get_task_dir(task_id)
    subtask_dir = tmp_manager.get_subtask_dir(task_id, subtask_id)
    (task_dir / "task_file.txt").write_text("content")
    (subtask_dir / "subtask_file.txt").write_text("content")

    assert task_dir.exists()
    assert subtask_dir.exists()

    # Cleanup subtask
    tmp_manager.cleanup_subtask(task_id, subtask_id)
    assert not subtask_dir.exists()
    assert task_dir.exists()  # Task dir should remain

    # Cleanup task
    tmp_manager.cleanup_task(task_id)
    assert not task_dir.exists()


def test_pruning_mechanism(tmp_config, temp_base_dir):
    """Test automatic pruning of old directories."""
    # Create manager
    manager = TmpManager("test_project", tmp_config)

    # Create an "old" directory by setting its mtime
    old_project_dir = tmp_config.base_tmp_dir / "old_project_hash"
    old_project_dir.mkdir()
    old_time = time.time() - 3600 * 2  # 2 hours ago
    os.utime(old_project_dir, (old_time, old_time))

    # Create a new directory
    new_project_dir = tmp_config.base_tmp_dir / "new_project_hash"
    new_project_dir.mkdir()

    # Run pruning
    manager.prune_old_directories()

    # Old directory should be gone, new should remain
    assert not old_project_dir.exists()
    assert new_project_dir.exists()


def test_project_info(tmp_manager):
    """Test getting project information."""
    # Create some test files
    task_dir = tmp_manager.get_task_dir("task1")
    (task_dir / "file1.txt").write_text("hello world")  # 11 bytes
    (task_dir / "file2.txt").write_text("test")  # 4 bytes

    subtask_dir = tmp_manager.get_subtask_dir("task1", "subtask1")
    (subtask_dir / "file3.txt").write_text("more content")  # 12 bytes

    info = tmp_manager.get_project_info()

    assert info["project_name"] == "test_project"
    assert info["file_count"] == 3
    assert info["dir_count"] >= 2  # task and subtask dirs
    assert info["total_size_bytes"] >= 27  # 11 + 4 + 12
    assert info["last_modified"] is not None


def test_singleton_behavior(tmp_config):
    """Test that get_tmp_manager returns singleton instances."""
    manager1 = get_tmp_manager("project_a", tmp_config)
    manager2 = get_tmp_manager("project_a", tmp_config)
    manager3 = get_tmp_manager("project_b", tmp_config)

    assert manager1 is manager2
    assert manager1 is not manager3


def test_error_handling(tmp_config):
    """Test error handling in various scenarios."""
    manager = TmpManager("test_project", tmp_config)

    # Test with invalid JSON in context file
    task_dir = manager.get_task_dir("test_task")
    context_file = task_dir / "context.json"
    context_file.write_text("invalid json")

    # Should handle gracefully
    result = manager.read_task_context("test_task")
    assert result is None  # Or raises, but currently returns None on error


@pytest.mark.parametrize("max_dirs", [1, 3, 10])
def test_max_project_dirs_pruning(temp_base_dir, max_dirs):
    """Test pruning when exceeding max project directories."""
    config = TmpConfig(
        base_tmp_dir=temp_base_dir,
        max_age_hours=24,  # Don't prune by age
        max_project_dirs=max_dirs
    )

    # Create more directories than max
    for i in range(max_dirs + 2):
        project_dir = config.base_tmp_dir / f"project_{i}_hash"
        project_dir.mkdir()
        # Set different mtimes
        mtime = time.time() - i * 60  # Older first
        os.utime(project_dir, (mtime, mtime))

    # Create manager and trigger pruning
    manager = TmpManager("test_project", config)
    manager.prune_old_directories()

    # Should keep only max_dirs - 1 (since manager's dir is also kept)
    remaining = [d for d in config.base_tmp_dir.iterdir() if d.is_dir() and d != manager.project_tmp_dir]
    assert len(remaining) == max_dirs - 1