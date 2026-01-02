"""
Aggregation Strategies Module

This module provides pluggable aggregation strategies for combining
model updates from multiple peers.

Usage:
    from quinkgl.aggregation import FedAvg

    aggregator = FedAvg(weight_by="data_size")
    aggregated = await aggregator.aggregate(updates)
"""

from quinkgl.aggregation.base import (
    AggregationStrategy,
    ModelUpdate,
    AggregatedModel
)
from quinkgl.aggregation.fedavg import FedAvg

# Export main classes
__all__ = [
    "AggregationStrategy",
    "ModelUpdate",
    "AggregatedModel",
    "FedAvg",
]
