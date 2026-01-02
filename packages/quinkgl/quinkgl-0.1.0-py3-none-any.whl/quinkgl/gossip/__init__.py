"""
Gossip Protocol Module

Continuous gossip protocol for decentralized model exchange.
Handles the communication loop between peers.

Usage:
    from quinkgl.gossip import ModelAggregator

    aggregator = ModelAggregator(node, topology, aggregation)
    await aggregator.start()
"""

from quinkgl.gossip.protocol import GossipProtocol, MessageType
from quinkgl.gossip.orchestrator import ModelAggregator, GossipOrchestrator

__all__ = [
    "GossipProtocol",
    "MessageType",
    "ModelAggregator",
    "GossipOrchestrator",  # Deprecated alias
]
