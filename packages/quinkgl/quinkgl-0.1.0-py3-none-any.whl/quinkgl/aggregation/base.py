"""
Base Aggregation Strategy

Abstract base class for all aggregation strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np


@dataclass
class ModelUpdate:
    """
    Represents a model update from a peer.

    Framework agnostic - works with any model format that can
    be serialized to/from numpy arrays or bytes.
    """
    peer_id: str
    weights: Any  # numpy array, dict, or bytes depending on framework
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional fields for weighted aggregation
    sample_count: int = 1
    loss: Optional[float] = None
    accuracy: Optional[float] = None
    round_number: int = 0

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AggregatedModel:
    """
    Result of aggregating multiple model updates.
    """
    weights: Any
    contributing_peers: List[str]
    total_samples: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class AggregationStrategy(ABC):
    """
    Abstract base class for aggregation strategies.

    An aggregation strategy combines multiple model updates
    into a single aggregated model.
    """

    def __init__(self, **kwargs):
        """Initialize the aggregation strategy with configuration."""
        self.config = kwargs

    @abstractmethod
    async def aggregate(
        self,
        updates: List[ModelUpdate]
    ) -> AggregatedModel:
        """
        Aggregate multiple model updates into one.

        Args:
            updates: List of model updates from peers

        Returns:
            AggregatedModel containing the combined weights
        """
        pass

    @abstractmethod
    def compute_weight(self, update: ModelUpdate) -> float:
        """
        Compute the weight for a given model update.

        Weights determine how much influence each peer's update
        has in the final aggregation.

        Args:
            update: The model update to weight

        Returns:
            Float weight value (higher = more influence)
        """
        pass

    def _validate_updates(self, updates: List[ModelUpdate]) -> None:
        """
        Validate that updates can be aggregated.

        Args:
            updates: List of model updates to validate

        Raises:
            ValueError: If updates are invalid or incompatible
        """
        if not updates:
            raise ValueError("Cannot aggregate empty list of updates")

        # Check for compatible shapes if using numpy arrays
        if len(updates) > 1:
            first_shape = self._get_shape(updates[0].weights)
            for update in updates[1:]:
                if self._get_shape(update.weights) != first_shape:
                    raise ValueError(
                        f"Incompatible weight shapes: "
                        f"{update.peer_id} has different shape"
                    )

    def _get_shape(self, weights: Any) -> tuple:
        """
        Get the shape of weights if possible.

        Args:
            weights: Weights object (numpy array, dict, etc.)

        Returns:
            Shape tuple or empty tuple if shape cannot be determined
        """
        if isinstance(weights, np.ndarray):
            return weights.shape
        elif isinstance(weights, dict):
            # Return sorted tuple of keys for dict weights
            return tuple(sorted(weights.keys()))
        return ()
