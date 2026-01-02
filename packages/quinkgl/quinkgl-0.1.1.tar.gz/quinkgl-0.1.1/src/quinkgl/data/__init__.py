"""
Data Loading and Management for QuinkGL

Provides dataset loaders and utilities for gossip learning.

Usage:
    from quinkgl.data import DatasetLoader, FederatedDataSplitter

    loader = DatasetLoader()
    (X, y), info = loader.load_cifar10()

    splitter = FederatedDataSplitter()
    splits = splitter.create_iid_split(X, y, num_nodes=5)
"""

from quinkgl.data.datasets import (
    load_dataset,
    list_datasets,
    create_federated_splits,
    load_cifar10,
    create_cifar10_splits,
    DatasetLoader,
    FederatedDataSplitter,
    DatasetInfo
)

__all__ = [
    # Main classes
    'DatasetLoader',
    'FederatedDataSplitter',
    'DatasetInfo',
    # Convenience functions
    'load_dataset',
    'list_datasets',
    'create_federated_splits',
    'load_cifar10',
    'create_cifar10_splits',
]
