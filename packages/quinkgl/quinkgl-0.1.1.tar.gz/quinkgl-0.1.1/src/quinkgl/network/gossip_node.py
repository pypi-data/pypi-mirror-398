"""
Gossip Learning Node with IPv8 Integration

Combines GLNode with GossipLearningCommunity for full P2P gossip learning.
"""

import asyncio
import logging
import time
from typing import Optional, Any, Callable

from quinkgl.core.node import GLNode
from quinkgl.models.base import ModelWrapper, TrainingConfig
from quinkgl.topology.base import TopologyStrategy, PeerInfo
from quinkgl.aggregation.base import AggregationStrategy
from quinkgl.network.ipv8_manager import IPv8Manager
from quinkgl.network.gossip_community import generate_community_id
from quinkgl.network.gossip_community import GossipLearningCommunity

logger = logging.getLogger(__name__)


class GossipNode:
    """
    Complete Gossip Learning Node with IPv8 networking.

    This class combines the GLNode framework with IPv8 P2P networking
    for full decentralized gossip learning.

    Example:
        ```python
        from quinkgl.network import GossipNode
        from quinkgl.models import PyTorchModel

        # Wrap your model
        model = PyTorchModel(my_pytorch_model)

        # Create node
        node = GossipNode(
            node_id="alice",
            domain="health",
            model=model,
            port=7000
        )

        # Start and run
        await node.start()
        await node.run_continuous(training_data)
        ```
    """

    def __init__(
        self,
        node_id: str,
        domain: str,
        model: ModelWrapper,
        port: int = 0,
        topology: Optional[TopologyStrategy] = None,
        aggregation: Optional[AggregationStrategy] = None,
        gossip_interval: float = 60.0,
        training_config: Optional[TrainingConfig] = None,
        auto_discovery: bool = True
    ):
        """
        Initialize GossipNode.

        Args:
            node_id: Unique identifier for this node
            domain: Domain identifier (e.g., "health", "agriculture")
            model: Wrapped model (PyTorchModel, TensorFlowModel, or custom)
            port: UDP port for IPv8 (0 for random)
            topology: Topology strategy (defaults to RandomTopology)
            aggregation: Aggregation strategy (defaults to FedAvg)
            gossip_interval: Seconds between gossip rounds
            training_config: Configuration for local training
            auto_discovery: Enable automatic peer discovery
        """
        self.node_id = node_id
        self.domain = domain
        self.port = port

        # Get data schema hash from model
        self.data_schema_hash = model.get_data_schema_hash()

        # Import default strategies if not provided
        if topology is None:
            from quinkgl.topology import RandomTopology
            topology = RandomTopology()

        if aggregation is None:
            from quinkgl.aggregation import FedAvg
            aggregation = FedAvg()

        # Create the framework GLNode
        self.gl_node = GLNode(
            peer_id=node_id,
            domain=domain,
            model=model,
            topology=topology,
            aggregation=aggregation,
            data_schema_hash=self.data_schema_hash,
            gossip_interval=gossip_interval,
            training_config=training_config
        )

        # IPv8 manager
        self.ipv8_manager = IPv8Manager(node_id=node_id, port=port)
        # Pass domain and schema to ipv8_manager for overlay initialization
        self.ipv8_manager.domain = domain
        self.ipv8_manager.data_schema_hash = self.data_schema_hash

        # Community (set after IPv8 starts)
        self.community: Optional[GossipLearningCommunity] = None

        # Auto-discovery flag
        self.auto_discovery = auto_discovery

        # State
        self.running = False

        logger.info(
            f"GossipNode initialized: node_id={node_id}, domain={domain}, "
            f"schema={self.data_schema_hash[:8]}..."
        )

    async def start(self):
        """Start the node and join the P2P network."""
        if self.running:
            logger.warning("Node already running")
            return

        logger.info(f"Starting GossipNode '{self.node_id}'...")

        # Start IPv8 with GossipLearningCommunity
        await self.ipv8_manager.start(
            community_class=GossipLearningCommunity,
            node_id_param=self.node_id
        )

        # Get community reference
        self.community = self.ipv8_manager.community

        # Update community with our specific info
        self.community.domain = self.domain
        self.community.data_schema_hash = self.data_schema_hash
        # CRITICAL: Regenerate community_id with correct domain/schema
        self.community._instance_community_id = generate_community_id(self.domain, self.data_schema_hash)
        type(self.community).community_id = self.community._instance_community_id
        logger.info(f"✅ Updated community_id to: {self.community._instance_community_id.hex()}")

        # Setup callbacks
        self._setup_callbacks()

        # Update GLNode with known peers
        self._sync_known_peers()

        # Mark GLNode as joined
        self.gl_node._joined = True

        # Mark as running
        self.running = True



        logger.info(f"✅ GossipNode '{self.node_id}' started on port {self.ipv8_manager.ipv8.endpoint.get_address()[1]}")

    def _setup_callbacks(self):
        """Setup callbacks between community and GLNode."""
        # When model update received
        async def on_model_update(
            sender_id: str,
            weights: Any,
            sample_count: int,
            round_number: int,
            loss: float,
            accuracy: float
        ):
            # Create a mock message for the orchestrator
            from quinkgl.gossip.protocol import ModelUpdateMessage

            message = ModelUpdateMessage.create(
                sender_id=sender_id,
                weights=weights,
                sample_count=sample_count,
                loss=loss,
                accuracy=accuracy,
                round_number=round_number
            )

            await self.gl_node._handle_network_message(message)
            logger.debug(f"Processed model update from {sender_id}")

        self.community.on_model_update_callback = on_model_update

        # When peer discovered
        async def on_peer_discovered(peer_info):
            # Add to GLNode's known peers
            from quinkgl.topology.base import PeerInfo as FrameworkPeerInfo

            framework_peer_info = FrameworkPeerInfo(
                peer_id=peer_info.node_id,
                domain=peer_info.domain,
                data_schema_hash=peer_info.data_schema_hash,
                model_version=peer_info.model_version
            )

            self.gl_node.orchestrator.add_peer(framework_peer_info)
            logger.info(f"Added peer {peer_info.node_id} to orchestrator")



        self.community.on_peer_discovered_callback = on_peer_discovered

        # When peer leaves
        async def on_peer_left(node_id: str):
            self.gl_node.orchestrator.remove_peer(node_id)
            logger.info(f"Removed peer {node_id} from orchestrator")

        self.community.on_peer_left_callback = on_peer_left

    def _sync_known_peers(self):
        """Sync known peers from community to GLNode."""
        from quinkgl.topology.base import PeerInfo as FrameworkPeerInfo

        connected_peer_ids = []
        for peer_info in self.community.get_compatible_peers():
            framework_peer_info = FrameworkPeerInfo(
                peer_id=peer_info.node_id,
                domain=peer_info.domain,
                data_schema_hash=peer_info.data_schema_hash,
                model_version=peer_info.model_version
            )
            self.gl_node.orchestrator.add_peer(framework_peer_info)
            connected_peer_ids.append(peer_info.node_id)



        logger.info(
            f"Synced {self.community.get_peer_count()} peers to orchestrator"
        )

    async def run_continuous(self, data=None, data_provider=None):
        """
        Run continuous gossip learning.

        Args:
            data: Training data (single dataset)
            data_provider: Callable that returns training data per round
        """
        if not self.running:
            raise RuntimeError("Node must be started before running")

        # Override the send callback to use IPv8 community
        async def send_to_peer(peer_id: str, message):
            """Send message to a specific peer via IPv8."""
            weights = message.weights
            self.community.send_model_update(
                target_node_id=peer_id,
                weights=weights,
                sample_count=message.sample_count,
                round_number=message.round_number,
                loss=message.loss,
                accuracy=message.accuracy
            )

        self.gl_node.orchestrator.send_message_callback = send_to_peer

        # Sync peers before starting
        self._sync_known_peers()

        # Run the gossip loop
        await self.gl_node.run_continuous(data_provider=data_provider or data)

    def stop(self):
        """Stop the node."""
        if not self.running:
            return

        logger.info(f"Stopping GossipNode '{self.node_id}'...")

        self.gl_node.stop()
        self.running = False

    async def shutdown(self):
        """Full shutdown including IPv8."""
        self.stop()
        await self.ipv8_manager.stop()
        logger.info(f"GossipNode '{self.node_id}' shutdown complete")

    def get_stats(self) -> dict:
        """Get node statistics."""
        ipv8_stats = self.ipv8_manager.get_stats()

        return {
            "node_id": self.node_id,
            "domain": self.domain,
            "data_schema_hash": self.data_schema_hash,
            "running": self.running,
            "current_round": self.gl_node.current_round,
            "connected_peers": self.community.get_peer_count() if self.community else 0,
            "ipv8_port": ipv8_stats.get("port"),
            "known_peers": [p.node_id for p in self.community.get_compatible_peers()] if self.community else []
        }

    def get_model(self) -> ModelWrapper:
        """Get the underlying model wrapper."""
        return self.gl_node.get_model()
