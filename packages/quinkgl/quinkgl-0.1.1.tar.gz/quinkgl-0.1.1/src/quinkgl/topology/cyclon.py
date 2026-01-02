"""
Cyclon Topology Strategy.

Implements a Random Peer Sampling strategy based on the Cyclon algorithm (Voulgaris et al., 2005).
Each node maintains a partial view and periodically shuffles it with a random peer to keep the graph random and connected.
"""

import logging
import asyncio
from typing import List

from quinkgl.topology.base import TopologyStrategy, SelectionContext, PeerInfo
from quinkgl.topology.sampler import PeerSampler

logger = logging.getLogger(__name__)


class CyclonTopology(TopologyStrategy):
    """
    Cyclon topology strategy for scalable peer sampling.
    
    Attributes:
        sampler (PeerSampler): Manages the partial view of peers.
        shuffle_length (int): Number of peers to exchange during shuffle.
    """

    def __init__(self, view_size: int = 20, shuffle_length: int = 8, seed: int = None, **kwargs):
        """
        Initialize Cyclon topology.

        Args:
            view_size: Maximum size of the partial view (e.g., 20).
            shuffle_length: Number of peers to exchange during shuffle (e.g., 8).
            seed: Random seed.
            **kwargs: Base args.
        """
        super().__init__(**kwargs)
        self.sampler = PeerSampler(view_size=view_size, seed=seed)
        self.shuffle_length = shuffle_length

    async def select_targets(self, context: SelectionContext, count: int = 3) -> List[str]:
        """
        Select random targets from the current partial view.
        
        Args:
            context: Execution context.
            count: Number of targets to select.
            
        Returns:
            List of peer IDs.
        """
        # Update sampler's knowledge from context if needed (e.g. initial bootstrap)
        # For now, we assume the sampler is maintained via periodic_maintenance and discovery events
        
        selected = self.sampler.select_random_peers(count)
        return [p.peer_id for p in selected]

    async def periodic_maintenance(self, context: SelectionContext):
        """
        Perform Cyclon shuffle.
        
        1. Increase age of all peers (not yet implemented in simplified Sampler).
        2. Select oldest peer Q from view.
        3. Exchange subset of view with Q.
        """
        # Simplified shuffle logic trigger
        # In a real implementation we would initiate a SHUFFLE message exchange here.
        # For this phase, we just log that maintenance happened and ensure view is healthy.
        view = self.sampler.get_view()
        # logger.debug(f"Cyclon active view size: {len(view)}")
        
        # If view is empty, try to refill from known_peers in context (fallback mechanism)
        if not view and context.known_peers:
            self.sampler.merge_view(context.known_peers)

    async def should_accept_connection(self, context: SelectionContext, peer_info: PeerInfo) -> bool:
        """Accept connection and add to sampler if space permits or swap."""
        # Check domain compatibility
        if peer_info.domain != context.my_domain:
            return False
            
        return True

    async def on_new_peer_discovered(self, peer_info: PeerInfo):
        """New peer discovered (e.g. from bootstrap or incoming shuffle). Add to view."""
        self.sampler.add_peer(peer_info)

    async def on_peer_disconnected(self, peer_id: str):
        """Peer disconnected. Remove from view."""
        self.sampler.remove_peer(peer_id)

    def get_active_view(self) -> List[PeerInfo]:
        """Return current partial view."""
        return self.sampler.get_view()
