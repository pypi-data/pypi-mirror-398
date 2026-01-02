"""
Random Topology Strategy

Simplest topology strategy: randomly select k peers from known peers.
"""

import random
from typing import List

from quinkgl.topology.base import TopologyStrategy, SelectionContext, PeerInfo


class RandomTopology(TopologyStrategy):
    """
    Random topology strategy.

    Selects k random peers from the list of known compatible peers.
    Compatible peers are those with matching domain and data schema.
    """

    def __init__(self, seed: int = None, **kwargs):
        """
        Initialize random topology strategy.

        Args:
            seed: Random seed for reproducibility (None = random)
            **kwargs: Additional configuration parameters
        """
        super().__init__(**kwargs)
        self.rng = random.Random(seed)

    def _get_compatible_peers(
        self,
        context: SelectionContext
    ) -> List[PeerInfo]:
        """
        Get list of compatible peers.

        Compatible peers have the same domain and data schema.

        Args:
            context: Current execution context

        Returns:
            List of compatible PeerInfo objects
        """
        compatible = []
        for peer in context.known_peers:
            # Skip self
            if peer.peer_id == context.my_peer_id:
                continue
            # Check compatibility
            if (peer.domain == context.my_domain and
                peer.data_schema_hash == context.my_data_schema_hash):
                compatible.append(peer)
        return compatible

    async def select_targets(
        self,
        context: SelectionContext,
        count: int = 3
    ) -> List[str]:
        """
        Select random compatible peers as targets.

        Args:
            context: Current execution context
            count: Maximum number of targets to select

        Returns:
            List of peer IDs to send updates to
        """
        compatible_peers = self._get_compatible_peers(context)

        if not compatible_peers:
            return []

        # Select up to count random peers
        selected_count = min(count, len(compatible_peers))
        selected_peers = self.rng.sample(compatible_peers, selected_count)

        return [p.peer_id for p in selected_peers]

    async def should_accept_connection(
        self,
        context: SelectionContext,
        peer_info: PeerInfo
    ) -> bool:
        """
        Accept connection if peer is compatible.

        Args:
            context: Current execution context
            peer_info: Information about the peer

        Returns:
            True if peer has compatible domain and schema
        """
        return (
            peer_info.domain == context.my_domain and
            peer_info.data_schema_hash == context.my_data_schema_hash
        )
