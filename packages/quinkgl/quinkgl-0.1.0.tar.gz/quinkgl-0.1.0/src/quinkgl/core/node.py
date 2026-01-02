"""
GLNode - Main Node Class for Gossip Learning

The primary interface for users to participate in gossip learning.
"""

import logging
import asyncio
from typing import Optional, Any, Callable
from pathlib import Path

from quinkgl.models.base import ModelWrapper, TrainingConfig
from quinkgl.topology.base import TopologyStrategy, SelectionContext
from quinkgl.aggregation.base import AggregationStrategy
from quinkgl.gossip.orchestrator import ModelAggregator
from quinkgl.storage.model_store import ModelStore

logger = logging.getLogger(__name__)


class GLNode:
    """
    Main node class for Gossip Learning Framework.

    This is the primary interface for users to participate in
    decentralized gossip learning.

    Example:
        ```python
        from quinkgl import GLNode, PyTorchModel, RandomTopology, FedAvg

        # Wrap your model
        model = PyTorchModel(my_pytorch_model)

        # Create node
        node = GLNode(
            peer_id="my-peer-1",
            domain="health",
            model=model,
            topology=RandomTopology(),
            aggregation=FedAvg()
        )

        # Join and run
        await node.join()
        await node.run_continuous(training_data)
        ```
    """

    def __init__(
        self,
        peer_id: str,
        domain: str,
        model: ModelWrapper,
        topology: TopologyStrategy,
        aggregation: AggregationStrategy,
        data_schema_hash: Optional[str] = None,
        storage_dir: Optional[str] = None,
        gossip_interval: float = 60.0,
        training_config: Optional[TrainingConfig] = None
    ):
        """
        Initialize a GLNode.

        Args:
            peer_id: Unique identifier for this node
            domain: Domain identifier (e.g., "health", "agriculture")
            model: Wrapped model (PyTorchModel, TensorFlowModel, or custom)
            topology: Topology strategy for peer selection
            aggregation: Aggregation strategy for combining models
            data_schema_hash: Optional schema hash (auto-generated if None)
            storage_dir: Optional directory for model checkpoints
            gossip_interval: Seconds between gossip rounds
            training_config: Configuration for local training
        """
        self.peer_id = peer_id
        self.domain = domain

        # Model
        self.model = model

        # Auto-generate schema hash if not provided
        if data_schema_hash is None:
            data_schema_hash = model.get_data_schema_hash()
        self.data_schema_hash = data_schema_hash

        # Strategies
        self.topology = topology
        self.aggregation = aggregation

        # Storage
        self.model_store = ModelStore(storage_dir=storage_dir) if storage_dir else None

        # Create aggregator (manages training→gossip→aggregation cycle)
        self.orchestrator = ModelAggregator(
            peer_id=peer_id,
            domain=domain,
            data_schema_hash=data_schema_hash,
            model=model,
            topology=topology,
            aggregator=aggregation,
            gossip_interval=gossip_interval,
            training_config=training_config
        )

        # Network layer (to be connected)
        self._network_layer = None
        self._joined = False

        logger.info(
            f"GLNode initialized: peer_id={peer_id}, domain={domain}, "
            f"schema={data_schema_hash}"
        )

    async def join(self, bootstrap_peers: Optional[list] = None):
        """
        Join the P2P network.

        Args:
            bootstrap_peers: List of bootstrap peer addresses
        """
        if self._joined:
            logger.warning("Node already joined")
            return

        # This would connect to IPv8 community
        # For now, mark as joined
        self._joined = True
        logger.info(f"Node {self.peer_id} joined domain '{self.domain}'")

    async def leave(self):
        """Leave the P2P network."""
        if not self._joined:
            return

        self.orchestrator.stop()
        self._joined = False
        logger.info(f"Node {self.peer_id} left the network")

    async def run_continuous(self, data=None, data_provider: Optional[Callable] = None):
        """
        Run continuous gossip learning.

        Args:
            data: Training data (single dataset)
            data_provider: Callable that returns training data per round

        Either `data` or `data_provider` should be provided.
        If `data_provider` is given, it's called each round to get fresh data.
        """
        if not self._joined:
            raise RuntimeError("Node must join() before running")

        logger.info(f"Starting continuous gossip learning for node {self.peer_id}")

        await self.orchestrator.run_continuous(
            data_provider=data_provider or data
        )

    def stop(self):
        """Stop the gossip learning loop."""
        self.orchestrator.stop()

    def register_hook(self, hook_name: str, callback: Callable):
        """
        Register a lifecycle hook.

        Args:
            hook_name: Name of the hook ("before_train", "after_train", etc.)
            callback: Async or sync function to call

        Available hooks:
            - before_train: Called before local training
            - after_train: Called after local training (receives TrainingResult)
            - before_send: Called before sending model (receives weights)
            - after_receive: Called after receiving model update
            - before_aggregate: Called before aggregation (receives pending updates)
            - after_aggregate: Called after aggregation (receives AggregatedModel)
        """
        self.orchestrator.register_hook(hook_name, callback)

    async def save_checkpoint(self, metrics: Optional[dict] = None):
        """
        Save current model as a checkpoint.

        Args:
            metrics: Optional metrics dict (loss, accuracy, etc.)
        """
        if self.model_store:
            self.model_store.save_checkpoint(
                round_number=self.model.current_round,
                weights=self.model.get_weights(),
                metrics=metrics
            )
        else:
            logger.warning("No model store configured, checkpoint not saved")

    def get_model(self) -> ModelWrapper:
        """Get the underlying model wrapper."""
        return self.model

    def get_peers(self) -> list:
        """Get list of known peers."""
        return self.orchestrator.known_peers

    @property
    def current_round(self) -> int:
        """Get current training round number."""
        return self.orchestrator.current_round

    def increment_round(self):
        """Manually increment the current round number."""
        self.orchestrator.increment_round()

    @property
    def is_running(self) -> bool:
        """Check if gossip loop is running."""
        return self.orchestrator.running

    # Network integration methods (to be used by transport layer)

    async def _handle_network_message(self, message):
        """
        Handle an incoming message from the network layer.

        This is called by the transport layer when a message arrives.
        """
        await self.orchestrator.handle_incoming_message(message)

    def _set_network_layer(self, network_layer):
        """
        Set the network layer for sending messages.

        This is called by the transport layer during initialization.
        """
        self._network_layer = network_layer
        self.orchestrator.send_message_callback = network_layer.send_message
        self.orchestrator.broadcast_callback = network_layer.broadcast_message
