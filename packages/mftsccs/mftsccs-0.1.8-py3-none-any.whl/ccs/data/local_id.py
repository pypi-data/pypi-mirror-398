"""
Local ID generator - generates unique negative IDs for local concepts.

Local/virtual concepts use negative IDs to distinguish them from
server-assigned positive IDs. After sync, the server assigns a
permanent positive ID.

The ID counters are persisted to a file so that IDs remain unique
across process restarts.
"""

import json
import os
import random
from pathlib import Path
from threading import Lock
from typing import Optional


class LocalId:
    """
    Thread-safe generator for unique local (negative) concept IDs.

    Local IDs are always negative to distinguish them from server IDs.
    The ID counter decrements to ensure uniqueness across sessions.

    **Persistence:**
    ID counters are saved to a file (~/.ccs/local_ids.json by default)
    so that IDs remain unique even after process restarts.

    Example:
        >>> concept_id = LocalId.get_concept_id()
        >>> print(concept_id)  # e.g., -1
        >>> concept_id2 = LocalId.get_concept_id()
        >>> print(concept_id2)  # e.g., -2
        >>> # After restart, continues from -3, not -1
    """

    _concept_counter: int = 0
    _connection_counter: int = 0
    _lock: Lock = Lock()
    _initialized: bool = False
    _storage_path: Optional[Path] = None

    # Reserved ID pools for efficiency (like JS version)
    _reserved_concept_ids: list = []
    _reserved_connection_ids: list = []
    _reserve_batch_size: int = 10

    @classmethod
    def _get_storage_path(cls) -> Path:
        """Get the path to the ID storage file."""
        if cls._storage_path:
            return cls._storage_path

        # Default to ./data/ccs/local_ids.json (app-specific)
        ccs_dir = Path("./data/ccs")
        ccs_dir.mkdir(parents=True, exist_ok=True)
        return ccs_dir / "local_ids.json"

    @classmethod
    def set_storage_path(cls, path: str) -> None:
        """
        Set a custom storage path for ID persistence.

        Args:
            path: File path for storing ID counters.
        """
        cls._storage_path = Path(path)
        cls._storage_path.parent.mkdir(parents=True, exist_ok=True)
        cls._initialized = False  # Force reload

    @classmethod
    def _load_counters(cls) -> None:
        """Load ID counters from persistent storage."""
        if cls._initialized:
            return

        storage_path = cls._get_storage_path()
        try:
            if storage_path.exists():
                with open(storage_path, 'r') as f:
                    data = json.load(f)
                    cls._concept_counter = data.get("concept_counter", 0)
                    cls._connection_counter = data.get("connection_counter", 0)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load ID counters: {e}")
            # Start fresh if file is corrupted
            cls._concept_counter = 0
            cls._connection_counter = 0

        cls._initialized = True

    @classmethod
    def _save_counters(cls) -> None:
        """Save ID counters to persistent storage."""
        storage_path = cls._get_storage_path()
        try:
            with open(storage_path, 'w') as f:
                json.dump({
                    "concept_counter": cls._concept_counter,
                    "connection_counter": cls._connection_counter
                }, f)
        except IOError as e:
            print(f"Warning: Could not save ID counters: {e}")

    @classmethod
    def _reserve_concept_ids(cls) -> None:
        """Reserve a batch of concept IDs for efficiency."""
        for _ in range(cls._reserve_batch_size):
            cls._concept_counter -= 1
            cls._reserved_concept_ids.append(cls._concept_counter)
        cls._save_counters()

    @classmethod
    def _reserve_connection_ids(cls) -> None:
        """Reserve a batch of connection IDs for efficiency."""
        for _ in range(cls._reserve_batch_size):
            cls._connection_counter -= 1
            cls._reserved_connection_ids.append(cls._connection_counter)
        cls._save_counters()

    @classmethod
    def get_concept_id(cls) -> int:
        """
        Get a new unique negative ID for a local concept.

        IDs are persisted to disk, so they remain unique across
        process restarts.

        Returns:
            A unique negative integer ID.
        """
        with cls._lock:
            cls._load_counters()

            # Use reserved pool if available
            if not cls._reserved_concept_ids:
                cls._reserve_concept_ids()

            return cls._reserved_concept_ids.pop(0)

    @classmethod
    def get_connection_id(cls) -> int:
        """
        Get a new unique negative ID for a local connection.

        IDs are persisted to disk, so they remain unique across
        process restarts.

        Returns:
            A unique negative integer ID.
        """
        with cls._lock:
            cls._load_counters()

            # Use reserved pool if available
            if not cls._reserved_connection_ids:
                cls._reserve_connection_ids()

            return cls._reserved_connection_ids.pop(0)

    @classmethod
    def get_random_id(cls) -> int:
        """
        Get a random negative ID (legacy compatibility).

        Note: This does not guarantee uniqueness across sessions.
        Prefer get_concept_id() or get_connection_id() instead.

        Returns:
            A random negative integer ID.
        """
        return -random.randint(1, 100_000_000)

    @classmethod
    def reset(cls) -> None:
        """
        Reset the ID counters (mainly for testing).

        Warning: This will cause ID collisions if used in production!
        """
        with cls._lock:
            cls._concept_counter = 0
            cls._connection_counter = 0
            cls._reserved_concept_ids.clear()
            cls._reserved_connection_ids.clear()
            cls._initialized = False
            cls._save_counters()

    @classmethod
    def get_current_counters(cls) -> dict:
        """
        Get the current counter values (for debugging).

        Returns:
            Dictionary with concept_counter and connection_counter values.
        """
        with cls._lock:
            cls._load_counters()
            return {
                "concept_counter": cls._concept_counter,
                "connection_counter": cls._connection_counter,
                "reserved_concept_ids": len(cls._reserved_concept_ids),
                "reserved_connection_ids": len(cls._reserved_connection_ids)
            }
