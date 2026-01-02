"""
Topology Strategies Module

This module provides pluggable topology strategies for P2P network formation.
Users can select from built-in strategies or implement custom ones.

Usage:
    from quinkgl.topology import RandomTopology, SmallWorldTopology

    # Use built-in strategy
    topology = SmallWorldTopology(k_neighbors=8)

    # Or implement custom
    from quinkgl.topology.base import TopologyStrategy
    class MyTopology(TopologyStrategy):
        async def select_targets(self, context):
            # Your logic here
            pass
"""

from quinkgl.topology.base import TopologyStrategy, SelectionContext, PeerInfo
from quinkgl.topology.random import RandomTopology
from quinkgl.topology.cyclon import CyclonTopology

# Export main classes
__all__ = [
    "TopologyStrategy",
    "SelectionContext",
    "PeerInfo",
    "RandomTopology",
    "CyclonTopology",
]
