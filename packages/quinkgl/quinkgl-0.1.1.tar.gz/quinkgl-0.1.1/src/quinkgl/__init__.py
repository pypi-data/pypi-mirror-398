"""
QuinkGL: Decentralized Gossip Learning Framework

A Python framework for decentralized machine learning using
gossip-based peer-to-peer communication.

Example:
    from quinkgl import (
        GossipNode,
        PyTorchModel,
        RandomTopology,
        FedAvg,
        TrainingConfig
    )

    model = PyTorchModel(my_pytorch_model)
    node = GossipNode(
        node_id="alice",
        domain="health",
        model=model,
        topology=RandomTopology(),
        aggregation=FedAvg()
    )
    await node.start()
    await node.run_continuous(training_data)
"""

__version__ = "0.1.0"

# =============================================================================
# CORE - Main node class
# =============================================================================
from quinkgl.network.gossip_node import GossipNode

# =============================================================================
# MODELS - Framework-specific model wrappers
# =============================================================================
from quinkgl.models.base import (
    ModelWrapper,
    TrainingConfig,
    TrainingResult
)
from quinkgl.models.pytorch import PyTorchModel

# TensorFlow is optional - only import if available
try:
    from quinkgl.models.tensorflow import TensorFlowModel
    _tensorflow_available = True
except ImportError:
    _tensorflow_available = False
    TensorFlowModel = None  # type: ignore

# =============================================================================
# TOPOLOGY - Peer selection strategies
# =============================================================================
from quinkgl.topology.base import (
    TopologyStrategy,
    PeerInfo,
    SelectionContext
)
from quinkgl.topology.random import RandomTopology
from quinkgl.topology.cyclon import CyclonTopology

# =============================================================================
# AGGREGATION - Model combining strategies
# =============================================================================
from quinkgl.aggregation.base import (
    AggregationStrategy,
    ModelUpdate,
    AggregatedModel
)
from quinkgl.aggregation.fedavg import FedAvg

# =============================================================================
# GOSSIP - Model aggregation orchestration
# =============================================================================
from quinkgl.gossip.orchestrator import ModelAggregator

# =============================================================================
# DATA - Dataset loading and splitting
# =============================================================================
from quinkgl.data.datasets import (
    DatasetLoader,
    FederatedDataSplitter,
    DatasetInfo
)

# =============================================================================
# PUBLIC API
# =============================================================================
__all__ = [
    # Core
    "GossipNode",
    
    # Models
    "ModelWrapper",
    "TrainingConfig",
    "TrainingResult",
    "PyTorchModel",
    "TensorFlowModel",
    
    # Topology
    "TopologyStrategy",
    "RandomTopology",
    "CyclonTopology",
    "PeerInfo",
    "SelectionContext",
    
    # Aggregation
    "AggregationStrategy",
    "FedAvg",
    "ModelUpdate",
    "AggregatedModel",
    
    # Gossip
    "ModelAggregator",
    
    # Data
    "DatasetLoader",
    "FederatedDataSplitter",
    "DatasetInfo",
]
