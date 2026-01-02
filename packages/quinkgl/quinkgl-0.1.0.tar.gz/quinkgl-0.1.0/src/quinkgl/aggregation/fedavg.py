"""
FedAvg Aggregation Strategy

Federated Averaging: Weighted average of model updates based on sample count.
"""

from typing import List
import numpy as np

from quinkgl.aggregation.base import (
    AggregationStrategy,
    ModelUpdate,
    AggregatedModel
)


class FedAvg(AggregationStrategy):
    """
    Federated Averaging aggregation strategy.

    Computes weighted average of model updates where weights are
    proportional to the number of samples each peer trained on.
    """

    def __init__(self, weight_by: str = "data_size", **kwargs):
        """
        Initialize FedAvg aggregator.

        Args:
            weight_by: How to weight updates
                - "data_size": Weight by sample count (default)
                - "uniform": Equal weight for all updates
                - "inverse_loss": Weight inversely by loss (lower loss = higher weight)
            **kwargs: Additional configuration parameters
        """
        super().__init__(**kwargs)
        self.weight_by = weight_by

    def compute_weight(self, update: ModelUpdate) -> float:
        """
        Compute the weight for a given model update.

        Args:
            update: The model update to weight

        Returns:
            Float weight value
        """
        if self.weight_by == "data_size":
            return float(update.sample_count)
        elif self.weight_by == "uniform":
            return 1.0
        elif self.weight_by == "inverse_loss":
            if update.loss is None or update.loss <= 0:
                return 1.0
            return 1.0 / update.loss
        else:
            return 1.0

    async def aggregate(
        self,
        updates: List[ModelUpdate]
    ) -> AggregatedModel:
        """
        Aggregate multiple model updates using weighted averaging.

        Args:
            updates: List of model updates from peers

        Returns:
            AggregatedModel containing the weighted average weights
        """
        self._validate_updates(updates)

        # Compute weights for each update
        weights_list = [self.compute_weight(u) for u in updates]
        total_weight = sum(weights_list)

        if total_weight == 0:
            raise ValueError("Total weight is zero, cannot aggregate")

        # Aggregate based on weight type
        first_weights = updates[0].weights

        if isinstance(first_weights, np.ndarray):
            aggregated = self._aggregate_numpy(updates, weights_list, total_weight)
        elif isinstance(first_weights, dict):
            aggregated = self._aggregate_dict(updates, weights_list, total_weight)
        else:
            # Fallback: try to handle as generic iterable
            aggregated = self._aggregate_generic(updates, weights_list, total_weight)

        return AggregatedModel(
            weights=aggregated,
            contributing_peers=[u.peer_id for u in updates],
            total_samples=sum(u.sample_count for u in updates),
            metadata={"aggregation_method": "fedavg", "weight_by": self.weight_by}
        )

    def _aggregate_numpy(
        self,
        updates: List[ModelUpdate],
        weights_list: List[float],
        total_weight: float
    ) -> np.ndarray:
        """Aggregate numpy array weights."""
        result = np.zeros_like(updates[0].weights, dtype=np.float64)

        for update, weight in zip(updates, weights_list):
            normalized_weight = weight / total_weight
            result += update.weights.astype(np.float64) * normalized_weight

        # Convert back to original dtype
        return result.astype(updates[0].weights.dtype)

    def _aggregate_dict(
        self,
        updates: List[ModelUpdate],
        weights_list: List[float],
        total_weight: float
    ) -> dict:
        """Aggregate dictionary weights (e.g., PyTorch state_dict)."""
        result = {}

        # Collect all unique keys across all updates
        all_keys = set()
        for update in updates:
            if isinstance(update.weights, dict):
                all_keys.update(update.weights.keys())

        # For each key, aggregate values from updates that have it
        for key in all_keys:
            # Find first update that has this key
            first_value = None
            first_index = -1
            for i, update in enumerate(updates):
                if isinstance(update.weights, dict) and key in update.weights:
                    first_value = update.weights[key]
                    first_index = i
                    break

            if first_value is None:
                continue

            if hasattr(first_value, '__array__'):  # numpy-like
                # Collect values and corresponding weights from updates that have this key
                values = []
                corresponding_weights = []
                for update, weight in zip(updates, weights_list):
                    if isinstance(update.weights, dict) and key in update.weights:
                        values.append(update.weights[key])
                        corresponding_weights.append(weight)

                if values:
                    # Recompute total weight for just this key
                    key_total_weight = sum(corresponding_weights)
                    result[key] = self._aggregate_numpy_values(
                        values,
                        corresponding_weights,
                        key_total_weight
                    )
                else:
                    result[key] = first_value
            else:
                # For non-array values, take from first update that has it
                result[key] = first_value

        return result

    def _aggregate_numpy_values(
        self,
        values: List,
        weights_list: List[float],
        total_weight: float
    ) -> np.ndarray:
        """Helper to aggregate a list of numpy-like values."""
        result = np.zeros_like(values[0], dtype=np.float64)

        for value, weight in zip(values, weights_list):
            normalized_weight = weight / total_weight
            result += value.astype(np.float64) * normalized_weight

        return result.astype(values[0].dtype)

    def _aggregate_generic(
        self,
        updates: List[ModelUpdate],
        weights_list: List[float],
        total_weight: float
    ):
        """Fallback aggregation for generic types."""
        # This would need to be implemented based on actual use cases
        raise NotImplementedError(
            "Generic aggregation not implemented. "
            "Use numpy arrays or dicts with numpy values."
        )
