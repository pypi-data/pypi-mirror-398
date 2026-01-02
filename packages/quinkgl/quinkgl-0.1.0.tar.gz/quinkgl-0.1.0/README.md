# QuinkGL: Gossip Learning Framework

QuinkGL is a decentralized, peer-to-peer (P2P) machine learning framework designed to enable edge intelligence through Gossip Learning algorithms. Unlike traditional Federated Learning, which relies on a central server for aggregation, QuinkGL distributes the training and aggregation process across all participating nodes, making the system more robust, scalable, and resistant to single points of failure.

This framework allows developers to simulate and deploy fully decentralized learning networks where nodes exchange model parameters via gossip protocols over IPv8.

## Key Features

*   **Decentralized Architecture:** Eliminates the need for a central parameter server.
*   **Gossip Learning:** Implements random walk and gossip-based aggregation strategies for model convergence.
*   **IPv8 Networking:** Native peer-to-peer communication with NAT traversal abilities (UDP hole punching).
*   **Scalability:** Designed to handle dynamic networks where nodes can join or leave at any time (churn).
*   **Framework-Agnostic Model Wrappers:** Supports PyTorch and TensorFlow models (extensible for others).
*   **Built-in Simulation & Dashboard:** Tools for simulating network conditions and visualizing training progress in real-time.

## Installation

QuinkGL requires Python 3.9 or higher.

To install the framework for usage in your own projects:

```bash
pip install quinkgl
```

For development or running the examples within this repository:

```bash
https://github.com/aliseyhann/QuinkGL-Gossip-Learning-Framework.git
cd QuinkGL-Gossip-Learning-Framework
pip install -e .
```

## Framework Usage Guide

QuinkGL is designed to be used as a library. The core components are `GossipNode` (the network entity) and `ModelWrapper` (the interface for your machine learning model).

### 1. Define Your Model

Wrap your existing PyTorch or TensorFlow model using the provided wrappers.

```python
import torch
import torch.nn as nn
from quinkgl.models import PyTorchModel

# Define standard PyTorch model
class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 2)

    def forward(self, x):
        return self.fc(x)

# Wrap it for QuinkGL
net = SimpleNet()
model_wrapper = PyTorchModel(net)
```

### 2. Configure the Node

Initialize a `GossipNode`. You must provide a unique ID and a domain name. Nodes within the same `domain` will discover each other.

```python
from quinkgl import GossipNode
from quinkgl import TrainingConfig

# Configuration for local training steps
config = TrainingConfig(
    batch_size=32,
    epochs=1,
    learning_rate=0.01
)

# Initialize the P2P Node
node = GossipNode(
    node_id="node_alice",
    domain="experiment_1",
    model=model_wrapper,
    port=0,  # 0 = Random available port
    training_config=config
)
```

### 3. Start Training

Start the node and providing a data source. The node will automatically discover peers on the network, exchange models, and aggregate weights.

```python
import asyncio

async def main():
    # Start the network layer (IPv8)
    await node.start()

    # Define a data provider (generator or function returning (X, y))
    def data_provider():
        # Return your local training data here
        return train_data, train_labels

    # Run the continuous gossip loop
    # This handles: Training -> Gossiping -> Aggregation
    await node.run_continuous(data_provider=data_provider)

if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture Overview

QuinkGL is built upon three main layers:

1.  **Network Layer (IPv8):** Handles peer discovery, connection management, and UDP message transport. It abstracts the complexity of NAT traversal and overlay management.
2.  **Gossip Protocol Layer:** Implements the logic for peer selection (Topology Randomness), model exchange, and message timing.
3.  **Learning Core:** Manages the local model state, performs Stochastic Gradient Descent (SGD) on local data, and merges incoming models using weighted averaging (FedAvg).

### Topology Management

The framework supports pluggable topology strategies. The default is **Cyclon**, a robust peer sampling algorithm that ensures an unbiased random view of the network graph, which is critical for convergence speed in gossip learning.

## Examples

The `scripts/` directory contains ready-to-use examples for running nodes and simulations.

*   `scripts/run_gossip_node.py`: A CLI script to run a standalone node.
*   `scripts/run_scale_test.sh`: A shell script to spawn multiple nodes for identifying scalability limits.
*   `examples/chat`: A legacy example demonstrating the P2P messaging capabilities of the underlying network stack.

## License

This project is licensed under the MIT License.
