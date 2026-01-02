"""
Model Store

Storage and versioning for model checkpoints.

SECURITY: Uses msgpack serialization instead of pickle to prevent
arbitrary code execution vulnerabilities when loading checkpoints.
"""

import hashlib
import io
import logging
import msgpack
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field, asdict

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelCheckpoint:
    """
    Represents a saved model checkpoint.
    """
    round_number: int
    weights: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, float] = field(default_factory=dict)
    contributing_peers: List[str] = field(default_factory=list)
    checkpoint_id: str = ""

    def __post_init__(self):
        if not self.checkpoint_id:
            # Generate ID from content hash
            content = f"{self.round_number}_{self.timestamp}"
            self.checkpoint_id = hashlib.sha256(content.encode()).hexdigest()[:16]


def _serialize_numpy_array(arr: np.ndarray) -> bytes:
    """Safely serialize a numpy array to bytes."""
    buffer = io.BytesIO()
    np.save(buffer, arr, allow_pickle=False)
    return buffer.getvalue()


def _deserialize_numpy_array(data: bytes) -> np.ndarray:
    """Safely deserialize bytes to a numpy array."""
    buffer = io.BytesIO(data)
    return np.load(buffer, allow_pickle=False)


def _serialize_value(value: Any) -> Any:
    """
    Convert Python/numpy types to msgpack-serializable format.
    """
    if isinstance(value, np.ndarray):
        return {
            "__type__": "numpy.ndarray",
            "__data__": _serialize_numpy_array(value).hex(),
            "dtype": str(value.dtype),
            "shape": value.shape
        }
    elif isinstance(value, np.integer):
        return int(value)
    elif isinstance(value, np.floating):
        return float(value)
    elif isinstance(value, datetime):
        return {
            "__type__": "datetime",
            "value": value.isoformat()
        }
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    return value


def _deserialize_value(value: Any) -> Any:
    """
    Convert msgpack-deserialized data back to Python/numpy types.
    """
    if isinstance(value, dict):
        # Check for special types
        if value.get("__type__") == "numpy.ndarray":
            array_bytes = bytes.fromhex(value["__data__"])
            return _deserialize_numpy_array(array_bytes)
        elif value.get("__type__") == "datetime":
            return datetime.fromisoformat(value["value"])
        # Regular dict
        return {k: _deserialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_deserialize_value(v) for v in value]
    return value


def _serialize_checkpoint(checkpoint: ModelCheckpoint) -> bytes:
    """Serialize a checkpoint to bytes using msgpack."""
    data = {
        "round_number": checkpoint.round_number,
        "timestamp": checkpoint.timestamp,
        "metrics": checkpoint.metrics,
        "contributing_peers": checkpoint.contributing_peers,
        "checkpoint_id": checkpoint.checkpoint_id,
        # Serialize weights specially
        "weights": _serialize_value(checkpoint.weights)
    }
    return msgpack.packb(data, use_bin_type=True)


def _deserialize_checkpoint(data: bytes) -> ModelCheckpoint:
    """Deserialize bytes to a checkpoint using msgpack."""
    unpacked = msgpack.unpackb(data, raw=False)
    return ModelCheckpoint(
        round_number=unpacked["round_number"],
        timestamp=_deserialize_value(unpacked["timestamp"]),
        metrics=unpacked["metrics"],
        contributing_peers=unpacked["contributing_peers"],
        checkpoint_id=unpacked["checkpoint_id"],
        weights=_deserialize_value(unpacked["weights"])
    )


class ModelStore:
    """
    Handles model storage and versioning.

    Supports in-memory and disk-based storage.
    """

    def __init__(self, storage_dir: Optional[str] = None, keep_in_memory: bool = True):
        """
        Initialize the model store.

        Args:
            storage_dir: Directory for disk-based storage (None = memory only)
            keep_in_memory: Whether to keep all checkpoints in memory
        """
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.keep_in_memory = keep_in_memory

        self._checkpoints: Dict[str, ModelCheckpoint] = {}
        self._round_index: Dict[int, str] = {}  # round_number -> checkpoint_id

        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Model store initialized with storage dir: {self.storage_dir}")

    def save_checkpoint(
        self,
        round_number: int,
        weights: Any,
        metrics: Optional[Dict[str, float]] = None,
        contributing_peers: Optional[List[str]] = None
    ) -> ModelCheckpoint:
        """
        Save a model checkpoint.

        Args:
            round_number: Training round number
            weights: Model weights
            metrics: Optional metrics (loss, accuracy, etc.)
            contributing_peers: List of peer IDs that contributed

        Returns:
            ModelCheckpoint instance
        """
        checkpoint = ModelCheckpoint(
            round_number=round_number,
            weights=weights,
            metrics=metrics or {},
            contributing_peers=contributing_peers or []
        )

        # Store in memory
        if self.keep_in_memory:
            self._checkpoints[checkpoint.checkpoint_id] = checkpoint
            self._round_index[round_number] = checkpoint.checkpoint_id

        # Store on disk
        if self.storage_dir:
            self._save_to_disk(checkpoint)

        logger.debug(f"Saved checkpoint for round {round_number}: {checkpoint.checkpoint_id}")
        return checkpoint

    def _save_to_disk(self, checkpoint: ModelCheckpoint):
        """Save checkpoint to disk using safe msgpack serialization."""
        filepath = self.storage_dir / f"checkpoint_{checkpoint.checkpoint_id}.msgpack"

        try:
            serialized = _serialize_checkpoint(checkpoint)
            with open(filepath, 'wb') as f:
                f.write(serialized)
        except Exception as e:
            logger.error(f"Failed to save checkpoint to disk: {e}")

    def load_checkpoint(self, checkpoint_id: str) -> Optional[ModelCheckpoint]:
        """
        Load a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            ModelCheckpoint or None if not found
        """
        # Check memory first
        if checkpoint_id in self._checkpoints:
            return self._checkpoints[checkpoint_id]

        # Check disk
        if self.storage_dir:
            return self._load_from_disk(checkpoint_id)

        return None

    def _load_from_disk(self, checkpoint_id: str) -> Optional[ModelCheckpoint]:
        """Load checkpoint from disk using safe msgpack deserialization."""
        # Try .msgpack extension first (new format)
        filepath = self.storage_dir / f"checkpoint_{checkpoint_id}.msgpack"

        # Fall back to .pkl for backward compatibility (but don't load it safely)
        if not filepath.exists():
            old_filepath = self.storage_dir / f"checkpoint_{checkpoint_id}.pkl"
            if old_filepath.exists():
                logger.warning(
                    f"Old pickle format found for {checkpoint_id}. "
                    f"Please migrate checkpoints. Not loading for security reasons."
                )
                return None
            return None

        try:
            with open(filepath, 'rb') as f:
                data = f.read()

            checkpoint = _deserialize_checkpoint(data)

            # Cache in memory if enabled
            if self.keep_in_memory:
                self._checkpoints[checkpoint_id] = checkpoint

            return checkpoint
        except Exception as e:
            logger.error(f"Failed to load checkpoint from disk: {e}")
            return None

    def get_checkpoint_by_round(self, round_number: int) -> Optional[ModelCheckpoint]:
        """
        Get the checkpoint for a specific round.

        Args:
            round_number: Round number

        Returns:
            ModelCheckpoint or None if not found
        """
        checkpoint_id = self._round_index.get(round_number)
        if checkpoint_id:
            return self.load_checkpoint(checkpoint_id)

        # Search disk if not in index
        if self.storage_dir:
            # Search both new and old formats
            for pattern in ["checkpoint_*.msgpack", "checkpoint_*.pkl"]:
                for filepath in self.storage_dir.glob(pattern):
                    checkpoint_id = filepath.stem.replace("checkpoint_", "")
                    checkpoint = self._load_from_disk(checkpoint_id)
                    if checkpoint and checkpoint.round_number == round_number:
                        self._round_index[round_number] = checkpoint.checkpoint_id
                        return checkpoint

        return None

    def get_latest_checkpoint(self) -> Optional[ModelCheckpoint]:
        """
        Get the most recent checkpoint.

        Returns:
            ModelCheckpoint or None if no checkpoints exist
        """
        if not self._round_index:
            return None

        latest_round = max(self._round_index.keys())
        return self.get_checkpoint_by_round(latest_round)

    def list_checkpoints(self) -> List[ModelCheckpoint]:
        """
        List all stored checkpoints.

        Returns:
            List of ModelCheckpoint objects
        """
        checkpoints = []

        # Add memory checkpoints
        if self.keep_in_memory:
            checkpoints.extend(self._checkpoints.values())

        # Add disk checkpoints if not in memory
        if self.storage_dir:
            # Search both new and old formats
            for pattern in ["checkpoint_*.msgpack", "checkpoint_*.pkl"]:
                for filepath in self.storage_dir.glob(pattern):
                    checkpoint_id = filepath.stem.replace("checkpoint_", "")
                    if checkpoint_id not in self._checkpoints:
                        checkpoint = self._load_from_disk(checkpoint_id)
                        if checkpoint:
                            checkpoints.append(checkpoint)

        # Sort by round number
        checkpoints.sort(key=lambda c: c.round_number)
        return checkpoints

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Remove from memory
        checkpoint = None
        if checkpoint_id in self._checkpoints:
            checkpoint = self._checkpoints.pop(checkpoint_id)
            # Remove from round index
            self._round_index.pop(checkpoint.round_number, None)

        # Remove from disk (try both formats)
        if self.storage_dir:
            for ext in [".msgpack", ".pkl"]:
                filepath = self.storage_dir / f"checkpoint_{checkpoint_id}{ext}"
                if filepath.exists():
                    filepath.unlink()
                    return True

        return False

    def clear_old_checkpoints(self, keep_last_n: int = 5):
        """
        Remove old checkpoints, keeping only the most recent N.

        Args:
            keep_last_n: Number of recent checkpoints to keep
        """
        checkpoints = self.list_checkpoints()

        if len(checkpoints) <= keep_last_n:
            return

        # Remove oldest checkpoints
        to_delete = checkpoints[:-keep_last_n]
        for checkpoint in to_delete:
            self.delete_checkpoint(checkpoint.checkpoint_id)

        logger.info(f"Cleared {len(to_delete)} old checkpoints, kept {keep_last_n}")

    def get_storage_size(self) -> int:
        """
        Get the total size of stored checkpoints in bytes.

        Returns:
            Total size in bytes
        """
        if not self.storage_dir:
            return sum(
                len(_serialize_checkpoint(c)) for c in self._checkpoints.values()
            )

        total = 0
        # Count both formats
        for pattern in ["checkpoint_*.msgpack", "checkpoint_*.pkl"]:
            for filepath in self.storage_dir.glob(pattern):
                total += filepath.stat().st_size
        return total
