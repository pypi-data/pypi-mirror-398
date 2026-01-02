"""
Network Module - IPv8 P2P Networking

Provides IPv8-based P2P networking for gossip learning.
"""

from quinkgl.network.ipv8_manager import IPv8Manager
from quinkgl.network.gossip_community import GossipLearningCommunity, PeerInfo, generate_community_id
from quinkgl.network.gossip_node import GossipNode
from quinkgl.network.model_serializer import serialize_model, deserialize_model, get_model_size_info

__all__ = [
    "IPv8Manager",
    "GossipLearningCommunity",
    "PeerInfo",
    "GossipNode",
    "generate_community_id",
    "serialize_model",
    "deserialize_model",
    "get_model_size_info",
]
