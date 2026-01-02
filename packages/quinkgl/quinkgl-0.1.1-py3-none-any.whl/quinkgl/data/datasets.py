"""
Dataset Loaders for QuinkGL Gossip Learning

Provides ready-to-use datasets for testing and production.
Datasets are split across nodes to simulate federated/gossip learning scenarios.
"""

import logging
import numpy as np
from typing import Tuple, Dict, List, Optional, Union, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DatasetInfo:
    """Information about a dataset."""
    name: str
    domain: str
    num_samples: int
    num_features: int
    num_classes: int
    description: str
    source: str = "scikit-learn"


# Available datasets registry
DATASET_REGISTRY: Dict[str, DatasetInfo] = {}


def register_dataset(info: DatasetInfo):
    """Register a dataset in the registry."""
    DATASET_REGISTRY[info.name] = info


class DatasetLoader:
    """
    Loads and prepares datasets for gossip learning.

    Features:
    - Load common datasets
    - Normalize/scale features
    - Create federated splits (IID or non-IID)
    """

    def __init__(self, normalize: bool = True, seed: int = 42):
        """
        Initialize dataset loader.

        Args:
            normalize: Whether to normalize features to [0, 1]
            seed: Random seed for reproducibility
        """
        self.normalize = normalize
        self.seed = seed
        np.random.seed(seed)

    def _normalize_data(self, X: np.ndarray) -> np.ndarray:
        """Normalize features to [0, 1] range."""
        if not self.normalize:
            return X

        # Min-max normalization per feature
        X_min = X.min(axis=0)
        X_max = X.max(axis=0)
        # Avoid division by zero
        X_range = X_max - X_min
        X_range[X_range == 0] = 1

        return (X - X_min) / X_range

    def load_breast_cancer(self) -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
        """
        Load Breast Cancer Wisconsin dataset.

        Binary classification: Malignant vs Benign
        30 features, 569 samples

        Returns:
            ((features, labels), dataset_info)
        """
        try:
            from sklearn.datasets import load_breast_cancer
        except ImportError:
            raise ImportError("scikit-learn required. Install with: pip install scikit-learn")

        data = load_breast_cancer()
        X = data.data.astype(np.float32)
        y = data.target.astype(np.int64)

        X = self._normalize_data(X)

        info = DatasetInfo(
            name="breast_cancer",
            domain="health",
            num_samples=len(X),
            num_features=X.shape[1],
            num_classes=2,
            description="Breast Cancer Wisconsin (Diagnostic) Dataset",
            source="scikit-learn"
        )
        register_dataset(info)

        logger.info(f"Loaded {info.name}: {X.shape} samples, {X.shape[1]} features, {info.num_classes} classes")
        return (X, y), info

    def load_heart_disease(self) -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
        """
        Load Heart Disease UCI dataset.

        Binary classification: Heart disease presence
        13 features, 303 samples

        Returns:
            ((features, labels), dataset_info)
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required. Install with: pip install pandas")

        # Load from UCI ML repository
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
        try:
            df = pd.read_csv(url, header=None, na_values='?')
        except Exception:
            # Fallback: use sklearn if available
            try:
                from sklearn.datasets import fetch_openml
                df = fetch_openml('heart-disease', version=1, as_frame=True).frame
            except ImportError:
                raise ImportError("Cannot load heart disease dataset. Install scikit-learn and pandas.")

        # Drop rows with missing values
        df = df.dropna()

        # Get features and labels
        # Last column is the target (0 = no disease, 1-4 = disease severity)
        # Convert to binary: 0 = no disease, 1 = disease
        X = df.iloc[:, :-1].values.astype(np.float32)
        y = (df.iloc[:, -1].values > 0).astype(np.int64)

        X = self._normalize_data(X)

        info = DatasetInfo(
            name="heart_disease",
            domain="health",
            num_samples=len(X),
            num_features=X.shape[1],
            num_classes=2,
            description="Heart Disease UCI Dataset",
            source="UCI ML Repository"
        )
        register_dataset(info)

        logger.info(f"Loaded {info.name}: {X.shape} samples, {X.shape[1]} features, {info.num_classes} classes")
        return (X, y), info

    def load_diabetes(self) -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
        """
        Load Pima Indians Diabetes dataset.

        Binary classification: Diabetes prediction
        8 features, 768 samples

        Returns:
            ((features, labels), dataset_info)
        """
        try:
            from sklearn.datasets import fetch_openml
        except ImportError:
            raise ImportError("scikit-learn required. Install with: pip install scikit-learn")

        # Fetch from OpenML
        data = fetch_openml('diabetes', version=1, as_frame=False, parser='auto')
        X = data.data.astype(np.float32)
        y = (data.target == 'tested_positive').astype(np.int64)

        X = self._normalize_data(X)

        info = DatasetInfo(
            name="diabetes",
            domain="health",
            num_samples=len(X),
            num_features=X.shape[1],
            num_classes=2,
            description="Pima Indians Diabetes Dataset",
            source="NIH/NKI"
        )
        register_dataset(info)

        logger.info(f"Loaded {info.name}: {X.shape} samples, {X.shape[1]} features, {info.num_classes} classes")
        return (X, y), info

    def load_iris(self) -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
        """
        Load Iris dataset.

        Multi-class classification: 3 iris species
        4 features, 150 samples

        Returns:
            ((features, labels), dataset_info)
        """
        try:
            from sklearn.datasets import load_iris
        except ImportError:
            raise ImportError("scikit-learn required. Install with: pip install scikit-learn")

        data = load_iris()
        X = data.data.astype(np.float32)
        y = data.target.astype(np.int64)

        X = self._normalize_data(X)

        info = DatasetInfo(
            name="iris",
            domain="general",
            num_samples=len(X),
            num_features=X.shape[1],
            num_classes=3,
            description="Iris Plant Dataset",
            source="scikit-learn"
        )
        register_dataset(info)

        logger.info(f"Loaded {info.name}: {X.shape} samples, {X.shape[1]} features, {info.num_classes} classes")
        return (X, y), info

    def load_wine(self) -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
        """
        load Wine Quality dataset.

        Multi-class classification: Wine quality scores
        11 features, 1599 samples (red wine)

        Returns:
            ((features, labels), dataset_info)
        """
        try:
            from sklearn.datasets import fetch_openml
        except ImportError:
            raise ImportError("scikit-learn required. Install with: pip install scikit-learn")

        # Fetch wine quality dataset
        data = fetch_openml('wine-quality-red', version=1, as_frame=False, parser='auto')
        X = data.data.astype(np.float32)
        y = data.target.astype(np.int64)

        # Adjust labels to be 0-indexed
        y = y - y.min()

        X = self._normalize_data(X)

        info = DatasetInfo(
            name="wine_quality",
            domain="agriculture",
            num_samples=len(X),
            num_features=X.shape[1],
            num_classes=len(np.unique(y)),
            description="Wine Quality Dataset (Red)",
            source="UCI ML Repository"
        )
        register_dataset(info)

        logger.info(f"Loaded {info.name}: {X.shape} samples, {X.shape[1]} features, {info.num_classes} classes")
        return (X, y), info

    def load_bank_marketing(self, max_samples: int = 10000) -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
        """
        Load Bank Marketing dataset.

        Binary classification: Term deposit subscription
        20 features, ~45K samples (can be limited)

        Args:
            max_samples: Maximum number of samples to load

        Returns:
            ((features, labels), dataset_info)
        """
        try:
            from sklearn.datasets import fetch_openml
        except ImportError:
            raise ImportError("scikit-learn required. Install with: pip install scikit-learn")

        data = fetch_openml('bank-marketing', version=1, as_frame=False, parser='auto')
        X = data.data.astype(np.float32)
        y = (data.target == 'yes').astype(np.int64)

        # Limit samples if requested
        if max_samples and len(X) > max_samples:
            indices = np.random.choice(len(X), max_samples, replace=False)
            X = X[indices]
            y = y[indices]

        X = self._normalize_data(X)

        info = DatasetInfo(
            name="bank_marketing",
            domain="finance",
            num_samples=len(X),
            num_features=X.shape[1],
            num_classes=2,
            description=f"Bank Marketing Dataset ({max_samples} samples)",
            source="UCI ML Repository"
        )
        register_dataset(info)

        logger.info(f"Loaded {info.name}: {X.shape} samples, {X.shape[1]} features, {info.num_classes} classes")
        return (X, y), info

    def load_by_name(self, name: str, **kwargs) -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
        """
        Load dataset by name.

        Args:
            name: Dataset name
            **kwargs: Additional arguments for specific loaders

        Returns:
            ((features, labels), dataset_info)
        """
        loaders = {
            'breast_cancer': self.load_breast_cancer,
            'heart_disease': self.load_heart_disease,
            'diabetes': self.load_diabetes,
            'iris': self.load_iris,
            'wine_quality': self.load_wine,
            'bank_marketing': lambda: self.load_bank_marketing(**kwargs),
        }

        if name not in loaders:
            available = ', '.join(loaders.keys())
            raise ValueError(f"Unknown dataset: {name}. Available: {available}")

        return loaders[name]()


class FederatedDataSplitter:
    """
    Splits data across nodes for federated/gossip learning scenarios.

    Supports:
    - IID splits: Random distribution of samples
    - Non-IID splits: Skewed distribution (simulate real-world)
    - Label distribution: Each node gets specific labels
    """

    def __init__(self, seed: int = 42):
        """
        Initialize splitter.

        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        np.random.seed(seed)

    def create_iid_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        num_nodes: int,
        samples_per_node: Optional[int] = None
    ) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
        """
        Create IID (Independent and Identically Distributed) splits.

        Each node gets a random subset of the data.

        Args:
            X: Features
            y: Labels
            num_nodes: Number of nodes
            samples_per_node: Samples per node (None for equal split)

        Returns:
            Dict mapping node_id to (X, y) tuple
        """
        num_samples = len(X)
        indices = np.random.permutation(num_samples)

        if samples_per_node is None:
            samples_per_node = num_samples // num_nodes

        splits = {}
        start = 0

        for node_id in range(num_nodes):
            end = min(start + samples_per_node, num_samples)
            node_indices = indices[start:end]

            splits[node_id] = (X[node_indices], y[node_indices])
            start = end

        logger.info(
            f"Created IID split: {num_nodes} nodes, "
            f"{samples_per_node} samples per node"
        )

        return splits

    def create_non_iid_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        num_nodes: int,
        alpha: float = 0.5
    ) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
        """
        Create non-IID splits using Dirichlet distribution.

        Simulates real-world scenarios where data is not evenly distributed.

        Args:
            X: Features
            y: Labels
            num_nodes: Number of nodes
            alpha: Dirichlet concentration parameter
                   - Lower values = more skewed
                   - Higher values = more balanced (alpha -> infinity = IID)

        Returns:
            Dict mapping node_id to (X, y) tuple
        """
        num_classes = len(np.unique(y))
        num_samples = len(X)

        # Generate Dirichlet distribution for proportions
        proportions = np.random.dirichlet([alpha] * num_nodes, size=num_classes)

        # Split each class among nodes
        splits = {i: ([], []) for i in range(num_nodes)}

        for class_idx in range(num_classes):
            class_indices = np.where(y == class_idx)[0]
            np.random.shuffle(class_indices)

            # Distribute this class's samples among nodes
            start_idx = 0
            for node_id in range(num_nodes):
                # Number of samples from this class for this node
                n_samples = int(len(class_indices) * proportions[class_idx, node_id])

                end_idx = min(start_idx + n_samples, len(class_indices))
                selected_indices = class_indices[start_idx:end_idx]

                splits[node_id][0].extend(X[selected_indices])
                splits[node_id][1].extend(y[selected_indices])

                start_idx = end_idx

        # Convert to numpy arrays
        for node_id in splits:
            splits[node_id] = (
                np.array(splits[node_id][0], dtype=np.float32),
                np.array(splits[node_id][1], dtype=np.int64)
            )

        logger.info(
            f"Created non-IID split (alpha={alpha}): {num_nodes} nodes"
        )

        return splits

    def create_label_skewed_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        num_nodes: int,
        labels_per_node: int = 2
    ) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
        """
        Create label-skewed splits where each node primarily sees certain labels.

        Args:
            X: Features
            y: Labels
            num_nodes: Number of nodes
            labels_per_node: Number of main labels per node

        Returns:
            Dict mapping node_id to (X, y) tuple
        """
        num_classes = len(np.unique(y))

        if labels_per_node * num_nodes > num_classes * 2:
            logger.warning(
                f"labels_per_node ({labels_per_node}) * num_nodes ({num_nodes}) "
                f"exceeds available classes. Some overlap will occur."
            )

        splits = {}

        for node_id in range(num_nodes):
            # Assign primary labels to this node
            start_label = (node_id * labels_per_node) % num_classes
            node_labels = [
                (start_label + i) % num_classes
                for i in range(labels_per_node)
            ]

            # Get samples for these labels (plus some noise from other labels)
            mask = np.isin(y, node_labels)
            node_X = X[mask]
            node_y = y[mask]

            # Add 10% random samples from other labels
            other_mask = ~mask
            other_indices = np.where(other_mask)[0]
            if len(other_indices) > 0:
                n_noise = max(1, len(node_X) // 10)
                noise_indices = np.random.choice(
                    other_indices,
                    min(n_noise, len(other_indices)),
                    replace=False
                )
                node_X = np.vstack([node_X, X[noise_indices]])
                node_y = np.concatenate([node_y, y[noise_indices]])

            splits[node_id] = (node_X, node_y)

        logger.info(
            f"Created label-skewed split: {num_nodes} nodes, "
            f"{labels_per_node} labels per node"
        )

        return splits

    def create_quantity_skewed_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        num_nodes: int,
        skew_factor: float = 0.3
    ) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
        """
        Create splits where nodes have different amounts of data.

        Args:
            X: Features
            y: Labels
            num_nodes: Number of nodes
            skew_factor: How much to skew (0-1)
                        - 0 = perfectly balanced
                        - 1 = highly imbalanced

        Returns:
            Dict mapping node_id to (X, y) tuple
        """
        num_samples = len(X)
        indices = np.random.permutation(num_samples)

        # Generate increasing sample counts
        base_size = num_samples // num_nodes

        # Skew: some nodes get more, some get less
        sizes = []
        for i in range(num_nodes):
            # Linearly scale from (1 - skew) to (1 + skew)
            factor = 1 + skew_factor * (2 * i / (num_nodes - 1) - 1)
            sizes.append(int(base_size * factor))

        # Normalize to total samples
        sizes = np.array(sizes)
        sizes = (sizes * num_samples / sizes.sum()).astype(int)

        # Assign data
        splits = {}
        start = 0
        for node_id in range(num_nodes):
            end = start + sizes[node_id]
            node_indices = indices[start:end]
            splits[node_id] = (X[node_indices], y[node_indices])
            start = end

        logger.info(
            f"Created quantity-skewed split: sizes={sizes}"
        )

        return splits


# Convenience functions

def load_dataset(name: str, normalize: bool = True, **kwargs) -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
    """
    Load a dataset by name.

    Args:
        name: Dataset name (breast_cancer, heart_disease, diabetes, iris, wine_quality, bank_marketing)
        normalize: Whether to normalize features
        **kwargs: Additional arguments for specific datasets

    Returns:
        ((features, labels), dataset_info)

    Example:
        >>> (X, y), info = load_dataset('breast_cancer')
        >>> print(f"Loaded {info.name}: {X.shape}")
    """
    loader = DatasetLoader(normalize=normalize)
    return loader.load_by_name(name, **kwargs)


def list_datasets() -> List[DatasetInfo]:
    """List all available datasets."""
    # Pre-load some datasets to populate registry
    return [
        DatasetInfo("breast_cancer", "health", 569, 30, 2, "Breast Cancer Wisconsin Dataset"),
        DatasetInfo("heart_disease", "health", 303, 13, 2, "Heart Disease UCI Dataset"),
        DatasetInfo("diabetes", "health", 768, 8, 2, "Pima Indians Diabetes Dataset"),
        DatasetInfo("iris", "general", 150, 4, 3, "Iris Plant Dataset"),
        DatasetInfo("wine_quality", "agriculture", 1599, 11, 6, "Wine Quality Dataset"),
        DatasetInfo("bank_marketing", "finance", 45211, 20, 2, "Bank Marketing Dataset"),
    ]


def create_federated_splits(
    data: Tuple[np.ndarray, np.ndarray],
    num_nodes: int,
    split_type: str = "iid",
    **kwargs
) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
    """
    Create federated data splits for multiple nodes.

    Args:
        data: (X, y) tuple
        num_nodes: Number of nodes
        split_type: Type of split ('iid', 'non_iid', 'label_skewed', 'quantity_skewed')
        **kwargs: Additional arguments for split type

    Returns:
        Dict mapping node_id to (X, y) tuple

    Example:
        >>> splits = create_federated_splits(data, num_nodes=3, split_type='iid')
        >>> for node_id, (X, y) in splits.items():
        ...     print(f"Node {node_id}: {len(X)} samples")
    """
    X, y = data
    splitter = FederatedDataSplitter()

    if split_type == "iid":
        return splitter.create_iid_split(X, y, num_nodes, **kwargs)
    elif split_type == "non_iid":
        return splitter.create_non_iid_split(X, y, num_nodes, **kwargs)
    elif split_type == "label_skewed":
        return splitter.create_label_skewed_split(X, y, num_nodes, **kwargs)
    elif split_type == "quantity_skewed":
        return splitter.create_quantity_skewed_split(X, y, num_nodes, **kwargs)
    else:
        raise ValueError(f"Unknown split_type: {split_type}")


def load_cifar10(data_dir: str = "./data") -> Tuple[Tuple[np.ndarray, np.ndarray], DatasetInfo]:
    """
    Load CIFAR-10 dataset from local files.

    Expects the CIFAR-10 Python format in data_dir/cifar-10-batches-py/

    Args:
        data_dir: Base directory containing cifar-10-batches-py folder

    Returns:
        ((features, labels), dataset_info)

    The images are flattened to 3072 features (32*32*3) for MLP models.
    For CNN models, reshape to (32, 32, 3) in your model.
    """
    import os
    import pickle

    cifar_dir = os.path.join(data_dir, "cifar-10-batches-py")

    if not os.path.exists(cifar_dir):
        raise FileNotFoundError(
            f"CIFAR-10 data not found at {cifar_dir}. "
            f"Please download CIFAR-10 and extract to {cifar_dir}"
        )

    def load_batch(filename):
        """Load a single batch."""
        with open(os.path.join(cifar_dir, filename), 'rb') as f:
            batch = pickle.load(f, encoding='bytes')
        return batch

    # Meta data
    meta = load_batch("batches.meta")
    label_names = [s.decode('utf-8') for s in meta[b'label_names']]

    # Load training batches
    train_batches = [f"data_batch_{i}" for i in range(1, 6)]
    train_data = []
    train_labels = []

    for batch_name in train_batches:
        batch = load_batch(batch_name)
        train_data.append(batch[b'data'])
        train_labels.append(batch[b'labels'])

    X_train = np.concatenate(train_data, axis=0).astype(np.float32)
    y_train = np.concatenate(train_labels, axis=0).astype(np.int64)

    # Load test batch
    test_batch = load_batch("test_batch")
    X_test = test_batch[b'data'].astype(np.float32)
    y_test = np.array(test_batch[b'labels'], dtype=np.int64)

    info = DatasetInfo(
        name="cifar10",
        domain="vision",
        num_samples=len(X_train),
        num_features=3072,  # 32 * 32 * 3
        num_classes=10,
        description=f"CIFAR-10 Image Classification ({len(label_names)} classes)",
        source="https://www.cs.toronto.edu/~kriz/cifar.html"
    )
    register_dataset(info)

    logger.info(
        f"Loaded CIFAR-10: {len(X_train)} train samples, "
        f"{len(X_test)} test samples, {info.num_classes} classes"
    )

    # Return combined data (train + test) for splitting
    # Splitting should be done by create_federated_splits
    X = np.concatenate([X_train, X_test], axis=0)
    y = np.concatenate([y_train, y_test], axis=0)

    return (X, y), info


def create_cifar10_splits(
    data_dir: str = "./data",
    num_nodes: int = 10,
    train_ratio: float = 0.9,
    split_type: str = "iid",
    seed: int = 42
) -> Dict[str, Dict[str, Tuple[np.ndarray, np.ndarray]]]:
    """
    Create federated splits for CIFAR-10 dataset.

    Splits both train and test data across nodes.

    Args:
        data_dir: Base directory containing cifar-10-batches-py folder
        num_nodes: Number of nodes to split across
        train_ratio: Ratio of training data (0-1)
        split_type: Type of split ('iid', 'non_iid')
        seed: Random seed

    Returns:
        Dict with keys 'train' and 'test', each containing
        Dict mapping node_id to (X, y) tuple

    Example:
        >>> splits = create_cifar10_splits(num_nodes=10)
        >>> train_data = splits['train'][0]  # Node 0's training data
        >>> test_data = splits['test'][0]    # Node 0's test data
    """
    np.random.seed(seed)

    # Load CIFAR-10
    (X, y), info = load_cifar10(data_dir)

    num_samples = len(X)
    train_size = int(num_samples * train_ratio)

    # Shuffle and split into train/test
    indices = np.random.permutation(num_samples)
    train_indices = indices[:train_size]
    test_indices = indices[train_size:]

    X_train, y_train = X[train_indices], y[train_indices]
    X_test, y_test = X[test_indices], y[test_indices]

    logger.info(
        f"CIFAR-10 split: {len(X_train)} train, {len(X_test)} test samples"
    )

    # Create federated splits for train
    splitter = FederatedDataSplitter(seed=seed)

    if split_type == "iid":
        train_splits = splitter.create_iid_split(X_train, y_train, num_nodes)
    elif split_type == "non_iid":
        train_splits = splitter.create_non_iid_split(X_train, y_train, num_nodes)
    else:
        raise ValueError(f"Unknown split_type: {split_type}")

    # Create federated splits for test
    if split_type == "iid":
        test_splits = splitter.create_iid_split(X_test, y_test, num_nodes)
    elif split_type == "non_iid":
        test_splits = splitter.create_non_iid_split(X_test, y_test, num_nodes)

    # Combine
    result = {
        'train': train_splits,
        'test': test_splits
    }

    logger.info(
        f"Created federated CIFAR-10 splits for {num_nodes} nodes "
        f"(train: ~{len(X_train)//num_nodes} samples/node, "
        f"test: ~{len(X_test)//num_nodes} samples/node)"
    )

    return result


if __name__ == "__main__":
    # Test dataset loading
    logging.basicConfig(level=logging.INFO)

    loader = DatasetLoader()

    print("\n=== Available Datasets ===")
    for info in list_datasets():
        print(f"  {info.name}: {info.domain} - {info.num_samples} samples, {info.num_classes} classes")

    print("\n=== Loading Breast Cancer Dataset ===")
    (X, y), info = loader.load_breast_cancer()
    print(f"Features shape: {X.shape}")
    print(f"Labels shape: {y.shape}")
    print(f"Class distribution: {np.bincount(y)}")

    print("\n=== Creating Federated Splits ===")
    splits = create_federated_splits((X, y), num_nodes=3, split_type="iid")
    for node_id, (node_X, node_y) in splits.items():
        print(f"Node {node_id}: {len(node_X)} samples, class dist: {np.bincount(node_y)}")
