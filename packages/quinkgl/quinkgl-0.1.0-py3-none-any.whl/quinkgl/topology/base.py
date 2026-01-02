"""
Base Topology Strategy

Abstract base class for all topology strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Any, Dict
from datetime import datetime


@dataclass
class PeerInfo:
    """Information about a peer in the network."""
    peer_id: str
    domain: str
    data_schema_hash: str
    model_version: str = "0.1.0"
    last_seen: datetime = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.last_seen is None:
            self.last_seen = datetime.now()


@dataclass
class SelectionContext:
    """Context provided to topology strategy for target selection."""
    my_peer_id: str
    my_domain: str
    my_data_schema_hash: str
    known_peers: List[PeerInfo]
    current_round: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TopologyStrategy(ABC):
    """
    Abstract base class for topology strategies.

    A topology strategy determines which peers to communicate with
    during the gossip learning process.
    """

    def __init__(self, **kwargs):
        """Initialize the topology strategy with configuration."""
        self.config = kwargs

    @abstractmethod
    async def select_targets(
        self,
        context: SelectionContext,
        count: int = 3
    ) -> List[str]:
        """
        Select peer IDs to send model updates to.

        Args:
            context: Current execution context including known peers
            count: Maximum number of targets to select

        Returns:
            List of peer IDs to send updates to
        """
        pass

    @abstractmethod
    async def should_accept_connection(
        self,
        context: SelectionContext,
        peer_info: PeerInfo
    ) -> bool:
        """
        Decide whether to accept an incoming connection from a peer.

        Args:
            context: Current execution context
            peer_info: Information about the peer requesting connection

        Returns:
            True if connection should be accepted, False otherwise
        """
        pass

    async def periodic_maintenance(self, context: SelectionContext):
        """
        Perform periodic maintenance tasks (e.g., shuffling peer list).
        
        Args:
            context: Current execution context
        """
        pass

    def get_active_view(self) -> List[PeerInfo]:
        """
        Get the current list of active peers (Partial View).
        
        Returns:
            List of PeerInfo objects representing the current active view.
        """
        return []

    async def on_peer_disconnected(self, peer_id: str):
        """
        Called when a peer disconnects.

        Args:
            peer_id: ID of the disconnected peer
        """
        pass

    async def on_new_peer_discovered(self, peer_info: PeerInfo):
        """
        Called when a new peer is discovered.

        Args:
            peer_info: Information about the newly discovered peer
        """
        pass
