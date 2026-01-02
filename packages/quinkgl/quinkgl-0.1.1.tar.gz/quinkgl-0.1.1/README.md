# QuinkGL: Gossip Learning Framework

[![PyPI version](https://badge.fury.io/py/quinkgl.svg)](https://badge.fury.io/py/quinkgl)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

QuinkGL is a **decentralized, peer-to-peer (P2P) machine learning framework** designed to enable edge intelligence through Gossip Learning algorithms. Unlike traditional Federated Learning, which relies on a central server for aggregation, QuinkGL distributes the training and aggregation process across all participating nodes.

## Key Features

- **Decentralized Architecture** – No central parameter server required
- **Gossip Learning** – Random walk and gossip-based aggregation for model convergence
- **IPv8 Networking** – Native P2P communication with NAT traversal (UDP hole punching)
- **Scalability** – Handles dynamic networks with node churn
- **Framework-Agnostic** – Supports PyTorch and TensorFlow models
- **Built-in Data Splitting** – IID and Non-IID data distribution utilities

## Installation

```bash
pip install quinkgl
```

For development:

```bash
git clone https://github.com/aliseyhann/QuinkGL-Gossip-Learning-Framework.git
cd QuinkGL-Gossip-Learning-Framework
pip install -e .
```

## Quick Start

```python
import asyncio
import torch.nn as nn
from quinkgl import (
    GossipNode,
    PyTorchModel,
    RandomTopology,
    FedAvg,
    TrainingConfig,
    DatasetLoader,
    FederatedDataSplitter
)

# 1. Define your model
class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 10)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.fc2(self.relu(self.fc1(x)))

# 2. Wrap the model
model = PyTorchModel(SimpleNet(), device="cpu")

# 3. Create the gossip node
node = GossipNode(
    node_id="alice",
    domain="mnist-vision",
    model=model,
    topology=RandomTopology(),
    aggregation=FedAvg(weight_by="data_size"),
    training_config=TrainingConfig(epochs=1, batch_size=32)
)

# 4. Load and split data
loader = DatasetLoader()
(X, y), info = loader.load_iris()

splitter = FederatedDataSplitter(seed=42)
splits = splitter.create_iid_split(X, y, num_nodes=5)
my_data = splits[0]  # This node's data partition

# 5. Run gossip learning
async def main():
    await node.start()
    await node.run_continuous(data=my_data)

asyncio.run(main())
```

## Public API

### Core

| Class | Description |
|-------|-------------|
| `GossipNode` | Main P2P gossip learning node with IPv8 networking |

### Models

| Class | Description |
|-------|-------------|
| `PyTorchModel` | Wrapper for PyTorch `nn.Module` |
| `TensorFlowModel` | Wrapper for TensorFlow/Keras models |
| `TrainingConfig` | Training configuration (epochs, batch_size, lr) |
| `TrainingResult` | Training result with metrics |

### Topology

| Class | Description |
|-------|-------------|
| `RandomTopology` | Random peer selection strategy |
| `CyclonTopology` | Scalable peer sampling (Cyclon algorithm) |
| `PeerInfo` | Peer information dataclass |

### Aggregation

| Class | Description |
|-------|-------------|
| `FedAvg` | Federated Averaging aggregation |
| `ModelAggregator` | Manages train→gossip→aggregate cycle |
| `ModelUpdate` | Peer model update dataclass |

### Data

| Class | Description |
|-------|-------------|
| `DatasetLoader` | Load common datasets (CIFAR-10, Iris, etc.) |
| `FederatedDataSplitter` | Create IID/Non-IID data splits |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       GossipNode                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ PyTorchModel│  │RandomTopology│  │      FedAvg       │  │
│  │ (or TF)     │  │ (or Cyclon)  │  │  (Aggregation)    │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    ModelAggregator                          │
│              (Train → Gossip → Aggregate)                   │
├─────────────────────────────────────────────────────────────┤
│                     IPv8 Network Layer                      │
│               (P2P, NAT Traversal, UDP)                     │
└─────────────────────────────────────────────────────────────┘
```

## License

MIT License © 2025, 28 December - Ali Seyhan, Baki Turhan
