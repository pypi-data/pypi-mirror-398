"""
Base Model Wrapper

Abstract base class for framework-specific model wrappers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class TrainingConfig:
    """Configuration for a training round."""
    epochs: int = 1
    batch_size: int = 32
    learning_rate: float = 0.001
    verbose: bool = False
    # Optional callbacks
    on_epoch_end: Optional[Callable] = None
    # Optional custom loss function (for PyTorch/TensorFlow)
    loss_fn: Optional[Any] = None
    # Optional custom optimizer class (for PyTorch) or optimizer name (for TensorFlow)
    optimizer: Optional[Any] = None
    # Optional optimizer kwargs
    optimizer_kwargs: Optional[dict] = None


@dataclass
class TrainingResult:
    """Result of a training round."""
    epochs_completed: int
    final_loss: float
    final_accuracy: Optional[float] = None
    samples_trained: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelWrapper(ABC):
    """
    Abstract base class for model wrappers.

    A model wrapper provides a framework-agnostic interface for:
    - Getting and setting model weights
    - Training on local data
    - Evaluating model performance
    """

    def __init__(self, model: Any):
        """
        Initialize the model wrapper.

        Args:
            model: The underlying model object (PyTorch Module, TF Model, etc.)
        """
        self.model = model
        self._current_round = 0

    @abstractmethod
    def get_weights(self) -> Any:
        """
        Get the current model weights.

        Returns:
            Model weights in a format suitable for serialization.
            Should be numpy arrays, dicts of arrays, or bytes.
        """
        pass

    @abstractmethod
    def set_weights(self, weights: Any) -> None:
        """
        Set the model weights.

        Args:
            weights: Model weights in the same format returned by get_weights()
        """
        pass

    @abstractmethod
    async def train(
        self,
        data: Any,
        config: Optional[TrainingConfig] = None
    ) -> TrainingResult:
        """
        Train the model on local data.

        Args:
            data: Training data (format depends on implementation)
            config: Training configuration

        Returns:
            TrainingResult with metrics
        """
        pass

    @abstractmethod
    def evaluate(self, data: Any, loss_fn: Any = None) -> Dict[str, float]:
        """
        Evaluate the model on test data.

        Args:
            data: Test data
            loss_fn: Optional custom loss function

        Returns:
            Dict with metrics like {"loss": float, "accuracy": float}
        """
        pass

    def get_data_schema_hash(self) -> str:
        """
        Get a hash representing the model's input/output schema.

        This is used for peer compatibility checking.

        Returns:
            Hash string representing the data schema
        """
        # Default implementation - can be overridden
        import hashlib
        model_info = f"{self.__class__.__name__}_{self.model.__class__.__name__}"
        return hashlib.sha256(model_info.encode()).hexdigest()[:16]

    def get_model_version(self) -> str:
        """
        Get the model architecture version.

        Returns:
            Version string (e.g., "1.0.0")
        """
        return "1.0.0"

    @property
    def current_round(self) -> int:
        """Get the current training round number."""
        return self._current_round

    def increment_round(self):
        """Increment the round counter."""
        self._current_round += 1
