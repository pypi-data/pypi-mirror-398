"""
ModelAggregator (formerly GossipOrchestrator)

Orchestrates the continuous gossip learning loop including
training, peer selection, model exchange, and aggregation.
"""

import asyncio
import logging
from typing import List, Optional, Callable, Dict
from datetime import datetime

from quinkgl.gossip.protocol import MessageType, GossipMessage, ModelUpdateMessage
from quinkgl.topology.base import TopologyStrategy, SelectionContext, PeerInfo
from quinkgl.aggregation.base import AggregationStrategy, ModelUpdate, AggregatedModel
from quinkgl.models.base import ModelWrapper, TrainingConfig

logger = logging.getLogger(__name__)


class ModelAggregator:
    """
    Orchestrates the continuous gossip learning process.

    Manages the training → gossip → aggregation cycle.
    """

    def __init__(
        self,
        peer_id: str,
        domain: str,
        data_schema_hash: str,
        model: ModelWrapper,
        topology: TopologyStrategy,
        aggregator: AggregationStrategy,
        gossip_interval: float = 60.0,
        training_config: Optional[TrainingConfig] = None
    ):
        """
        Initialize the gossip orchestrator.

        Args:
            peer_id: Unique identifier for this peer
            domain: Domain identifier (e.g., "health", "agriculture")
            data_schema_hash: Hash of data schema for compatibility
            model: Model wrapper for training
            topology: Topology strategy for peer selection
            aggregator: Aggregation strategy for model combining
            gossip_interval: Seconds between gossip rounds
            training_config: Configuration for local training
        """
        self.peer_id = peer_id
        self.domain = domain
        self.data_schema_hash = data_schema_hash
        self.model = model
        self.topology = topology
        self.aggregator = aggregator
        self.gossip_interval = gossip_interval
        self.training_config = training_config or TrainingConfig()

        # State
        self.running = False
        self.current_round = 0
        self.known_peers: Dict[str, PeerInfo] = {}
        self.pending_updates: List[ModelUpdate] = []
        self._aggregation_event = asyncio.Event()
        self.metrics: Dict[str, float] = {} # Store latest training metrics
        self.metrics_history: List[Dict] = [] # History for plotting
        self.comm_log: List[Dict] = [] # Log of outgoing messages

        # Network callbacks (to be set by transport layer)
        self.send_message_callback: Optional[Callable] = None
        self.broadcast_callback: Optional[Callable] = None

        # Metrics callback (to be set by transport layer)
        self.metrics_callback: Optional[Callable] = None

        # Lifecycle hooks
        self.hooks = {
            "before_train": [],
            "after_train": [],
            "before_send": [],
            "after_receive": [],
            "before_aggregate": [],
            "after_aggregate": [],
        }

    def register_hook(self, hook_name: str, callback: Callable):
        """Register a lifecycle hook callback."""
        if hook_name in self.hooks:
            self.hooks[hook_name].append(callback)
        else:
            raise ValueError(f"Unknown hook: {hook_name}")

    async def _execute_hooks(self, hook_name: str, *args, **kwargs):
        """Execute all callbacks for a hook."""
        for callback in self.hooks.get(hook_name, []):
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)

    def add_peer(self, peer_info: PeerInfo):
        """Add a newly discovered peer."""
        if peer_info.peer_id not in self.known_peers:
            logger.info(f"Discovered new peer: {peer_info.peer_id}")
            self.known_peers[peer_info.peer_id] = peer_info

            # Notify topology strategy with error handling
            async def _notify_topology():
                try:
                    await self.topology.on_new_peer_discovered(peer_info)
                except Exception as e:
                    logger.error(f"Error notifying topology about new peer {peer_info.peer_id}: {e}")

            asyncio.create_task(_notify_topology())

    async def remove_peer(self, peer_id: str):
        """Remove a disconnected peer."""
        if peer_id in self.known_peers:
            logger.info(f"Removing peer: {peer_id}")
            del self.known_peers[peer_id]
            
            # Notify topology strategy
            await self.topology.on_peer_disconnected(peer_id)
            logger.info(f"Removed peer: {peer_id}")

    async def handle_incoming_message(self, message: GossipMessage):
        """
        Handle an incoming message from a peer.

        Args:
            message: The received message
        """
        if message.msg_type == MessageType.MODEL_UPDATE:
            await self._handle_model_update(message)
        elif message.msg_type == MessageType.HEARTBEAT:
            # Update peer last_seen
            if message.sender_id in self.known_peers:
                self.known_peers[message.sender_id].last_seen = datetime.now()
        elif message.msg_type == MessageType.DISCOVERY_ANNOUNCE:
            await self._handle_discovery_announce(message)

    async def _handle_model_update(self, message: ModelUpdateMessage):
        """Handle an incoming model update."""
        await self._execute_hooks("after_receive", message)

        # Create ModelUpdate from message
        update = ModelUpdate(
            peer_id=message.sender_id,
            weights=message.weights,
            sample_count=message.sample_count,
            loss=message.loss,
            accuracy=message.accuracy,
            round_number=message.round_number
        )

        self.pending_updates.append(update)
        logger.info(f"Received model update from {message.sender_id}")

        # Trigger aggregation event to notify the main loop
        self._aggregation_event.set()

    async def _handle_discovery_announce(self, message: GossipMessage):
        """Handle a discovery announcement."""
        # Check compatibility
        if (message.payload.get("domain") == self.domain and
            message.payload.get("data_schema_hash") == self.data_schema_hash):
            # Add peer
            peer_info = PeerInfo(
                peer_id=message.sender_id,
                domain=message.payload["domain"],
                data_schema_hash=message.payload["data_schema_hash"],
                model_version=message.payload.get("model_version", "1.0.0")
            )
            self.add_peer(peer_info)

    async def _train_local(self, data) -> tuple:
        """Perform local training. Returns (loss, accuracy) tuple."""
        await self._execute_hooks("before_train")

        result = await self.model.train(data, self.training_config)

        await self._execute_hooks("after_train", result)

        loss = result.final_loss if result.final_loss is not None else 0.0
        acc = result.final_accuracy if result.final_accuracy is not None else 0.0

        acc_str = f"{acc:.4f}" if result.final_accuracy is not None else "N/A"
        logger.info(
            f"Local training round {self.current_round} complete: "
            f"loss={loss:.4f}, acc={acc_str}"
        )

        # Update metrics if callback is registered
        if self.metrics_callback:
            self.metrics_callback(loss=loss, accuracy=acc, round_num=self.current_round)

        return loss, acc

    async def _send_model(self, target_peers: List[str], loss: float = None, accuracy: float = None) -> None:
        """Send current model to target peers."""
        weights = self.model.get_weights()

        await self._execute_hooks("before_send", weights)

        model_message = ModelUpdateMessage.create(
            sender_id=self.peer_id,
            weights=weights,
            sample_count=self.training_config.batch_size,  # Approximate
            round_number=self.current_round,
            loss=loss,
            accuracy=accuracy
        )

        for peer_id in target_peers:
            if self.send_message_callback:
                await self.send_message_callback(peer_id, model_message)
                logger.info(f"Sent model update to {peer_id}")
                
                # Log communication
                self.comm_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "target": peer_id,
                    "round": self.current_round
                })
                # Keep log size manageable
                if len(self.comm_log) > 50:
                    self.comm_log.pop(0)

    async def _aggregate_models(self) -> Optional[AggregatedModel]:
        """Aggregate pending model updates."""
        if not self.pending_updates:
            return None

        await self._execute_hooks("before_aggregate", self.pending_updates)

        # Include own model in aggregation
        # Use batch_size as sample_count (or compute from actual training data if available)
        own_sample_count = self.training_config.batch_size
        if own_sample_count <= 0:
            # Fallback to average of peer sample counts if own is unknown
            peer_counts = [u.sample_count for u in self.pending_updates if u.sample_count > 0]
            own_sample_count = sum(peer_counts) // len(peer_counts) if peer_counts else 32

        own_update = ModelUpdate(
            peer_id=self.peer_id,
            weights=self.model.get_weights(),
            sample_count=own_sample_count,
            round_number=self.current_round
        )

        all_updates = [own_update] + self.pending_updates
        aggregated = await self.aggregator.aggregate(all_updates)

        await self._execute_hooks("after_aggregate", aggregated)

        # Update model with aggregated weights
        self.model.set_weights(aggregated.weights)

        # Clear pending updates and aggregation event
        self.pending_updates.clear()
        self._aggregation_event.clear()

        logger.info(
            f"Aggregated models from {len(aggregated.contributing_peers)} peers "
            f"(total_samples={aggregated.total_samples})"
        )

        return aggregated

    async def run_continuous(self, data_provider=None):
        """
        Run the continuous gossip learning loop.

        Args:
            data_provider: Callable that returns training data for each round
        """
        self.running = True
        logger.info("Starting continuous gossip learning loop")

        consecutive_errors = 0
        max_consecutive_errors = 5

        try:
            while self.running:
                round_start_time = datetime.now()

                try:
                    self.current_round += 1

                    loss, acc = 0.0, 0.0

                    # 1. Local training
                    if data_provider:
                        train_data = data_provider() if callable(data_provider) else data_provider
                        loss, acc = await self._train_local(train_data)

                        # Apply EMA smoothing (alpha=0.2) to reduce jitter from small batches
                        alpha = 0.2
                        if not self.metrics:
                            self.metrics = {"loss": loss, "accuracy": acc}
                        else:
                            self.metrics = {
                                "loss": alpha * loss + (1 - alpha) * self.metrics.get("loss", loss),
                                "accuracy": alpha * acc + (1 - alpha) * self.metrics.get("accuracy", acc)
                            }

                        # Log Metrics History
                        self.metrics_history.append({
                            "round": self.current_round,
                            "loss": self.metrics["loss"],
                            "accuracy": self.metrics["accuracy"],
                            "timestamp": datetime.now().isoformat()
                        })
                        if len(self.metrics_history) > 100:
                            self.metrics_history.pop(0)

                    # 2. Select gossip targets
                    context = SelectionContext(
                        my_peer_id=self.peer_id,
                        my_domain=self.domain,
                        my_data_schema_hash=self.data_schema_hash,
                        known_peers=list(self.known_peers.values()),
                        current_round=self.current_round
                    )
                    targets = await self.topology.select_targets(context, count=3)

                    # 3. Send model to targets (with metrics)
                    if targets:
                        await self._send_model(targets, loss=loss, accuracy=acc)

                    # 4. Topology Maintenance (e.g. Shuffle)
                    await self.topology.periodic_maintenance(context)

                    # 5. Wait for incoming models & aggregation trigger
                    # We wait for the gossip interval, but allow interruption for earlier aggregation
                    try:
                        await asyncio.wait_for(self._aggregation_event.wait(), timeout=self.gossip_interval)
                    except asyncio.TimeoutError:
                        pass  # Timeout is normal, just proceed to next round

                    # 6. Aggregate received models
                    await self._aggregate_models()

                    # Reset error counter on successful round
                    consecutive_errors = 0

                    round_duration = (datetime.now() - round_start_time).total_seconds()
                    logger.debug(f"Round {self.current_round} completed in {round_duration:.2f}s")

                except asyncio.CancelledError:
                    logger.info("Gossip loop cancelled")
                    break
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(
                        f"Error in round {self.current_round}: {e.__class__.__name__}: {e}"
                    )

                    # Check if we've had too many consecutive errors
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(
                            f"Too many consecutive errors ({consecutive_errors}). "
                            f"Stopping gossip loop."
                        )
                        raise RuntimeError(
                            f"Gossip loop stopped after {consecutive_errors} consecutive errors"
                        ) from e

                    # Clear aggregation event and continue to next round
                    self._aggregation_event.clear()

                    # Wait a bit before retrying
                    await asyncio.sleep(min(2 ** consecutive_errors, 30))

        finally:
            self.running = False
            logger.info(f"Gossip learning loop stopped (completed {self.current_round} rounds)")

    def increment_round(self):
        """Manually increment the current round number."""
        self.current_round += 1
        logger.debug(f"Round incremented to {self.current_round}")

    def stop(self):
        """Stop the gossip learning loop."""
        self.running = False
        logger.info("Stopping continuous gossip learning loop")


# Backward compatibility alias (deprecated)
GossipOrchestrator = ModelAggregator
