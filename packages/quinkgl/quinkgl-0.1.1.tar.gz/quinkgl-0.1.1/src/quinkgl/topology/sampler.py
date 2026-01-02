"""
Peer Sampler for Partial View Management.

Manages a fixed-size list of peers (Partial View) for Random Peer Sampling protocols like Cyclon.
"""

import random
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime

from quinkgl.topology.base import PeerInfo

logger = logging.getLogger(__name__)


class PeerSampler:
    """
    Manages a partial view of the network.
    
    Attributes:
        view_size (int): Maximum number of peers to keep in view.
        view (Dict[str, PeerInfo]): Current active view {peer_id: PeerInfo}.
    """

    def __init__(self, view_size: int = 20, seed: int = None):
        """
        Initialize PeerSampler.

        Args:
            view_size: Maximum size of the partial view.
            seed: Random seed for reproducibility.
        """
        self.view_size = view_size
        self.view: Dict[str, PeerInfo] = {}  # peer_id -> PeerInfo
        self.rng = random.Random(seed)

    def add_peer(self, peer: PeerInfo):
        """
        Add a peer to the view. If view is full, evict the oldest peer (placeholder strategy).
        
        Args:
            peer: PeerInfo object to add.
        """
        if peer.peer_id in self.view:
            # Update existing peer info
            self.view[peer.peer_id] = peer
            return

        if len(self.view) >= self.view_size:
            self._evict_peer()

        self.view[peer.peer_id] = peer

    def remove_peer(self, peer_id: str):
        """Remove a peer from the view."""
        if peer_id in self.view:
            del self.view[peer_id]

    def select_random_peers(self, count: int, exclude: List[str] = None) -> List[PeerInfo]:
        """
        Select random peers from the view.

        Args:
            count: Number of peers to select.
            exclude: List of peer IDs to exclude.

        Returns:
            List of selected PeerInfo objects.
        """
        candidates = list(self.view.values())
        if exclude:
            candidates = [p for p in candidates if p.peer_id not in exclude]

        if not candidates:
            return []

        sample_size = min(count, len(candidates))
        return self.rng.sample(candidates, sample_size)

    def get_view(self) -> List[PeerInfo]:
        """Return the current view as a list."""
        return list(self.view.values())

    def merge_view(self, new_peers: List[PeerInfo]):
        """
        Merge a list of new peers into the current view (Cyclon-style merge logic placeholder).
        
        In a full Cyclon implementation, this would involve age-based priority.
        For now, we simply add them and rely on add_peer's eviction.
        """
        for peer in new_peers:
            self.add_peer(peer)

    def _evict_peer(self):
        """Evict a peer to make space. Strategy: Remove random (simple) or oldest (better)."""
        # For now, remove a random peer to keep it simple, or oldest?
        # Let's remove the one with the oldest 'last_seen' if available, otherwise random
        if not self.view:
            return

        # Simple random eviction for robustness against churn in basic version
        key_to_remove = self.rng.choice(list(self.view.keys()))
        del self.view[key_to_remove]
