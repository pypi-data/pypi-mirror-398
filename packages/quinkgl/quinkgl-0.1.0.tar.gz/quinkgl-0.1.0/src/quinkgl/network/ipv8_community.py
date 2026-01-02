"""
QuinkGL Community - IPv8 Overlay for P2P Chat

Implements chat messaging over IPv8 with NAT traversal.
"""

import time
import logging
from typing import Optional, Callable

from ipv8.community import Community
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload import Payload
from ipv8.peer import Peer

logger = logging.getLogger(__name__)


class ChatMessagePayload(Payload):
    """
    Payload for chat messages.
    
    Format:
    - sender_id: str (node ID)
    - text: str (message content)
    - timestamp: int (Unix timestamp in milliseconds)
    """
    
    msg_id = 1  # Unique message ID for this payload type
    format_list = ['varlenH', 'varlenH', 'Q']
    
    def __init__(self, sender_id: str, text: str, timestamp: int):
        super().__init__()
        self.sender_id = sender_id
        self.text = text
        self.timestamp = timestamp
    
    def to_pack_list(self):
        return [
            ('varlenH', self.sender_id.encode('utf-8')),
            ('varlenH', self.text.encode('utf-8')),
            ('Q', self.timestamp)
        ]
    
    @classmethod
    def from_unpack_list(cls, *args):
        sender_id = args[0].decode('utf-8')
        text = args[1].decode('utf-8')
        timestamp = args[2]
        return cls(sender_id, text, timestamp)


class PeerInfoPayload(Payload):
    """
    Payload for peer information exchange.
    
    Contains node_id for peer identification.
    """
    
    msg_id = 2  # Unique message ID for this payload type
    format_list = ['varlenH']
    
    def __init__(self, node_id: str):
        super().__init__()
        self.node_id = node_id
    
    def to_pack_list(self):
        return [('varlenH', self.node_id.encode('utf-8'))]
    
    @classmethod
    def from_unpack_list(cls, *args):
        return cls(args[0].decode('utf-8'))


class QuinkGLCommunity(Community):
    """
    QuinkGL P2P Chat Community.
    
    Features:
    - Direct P2P chat messaging
    - Peer discovery via DHT
    - Stochastic UDP hole punching (automatic via IPv8)
    - Node ID tracking for peer identification
    """
    
    community_id = b'QuinkGL-Chat-v1\x00\x00\x00\x00\x00'  # Exactly 22 bytes (required by IPv8)
    
    def __init__(self, *args, node_id: str = "unknown", **kwargs):
        """
        Initialize QuinkGL community.
        
        Args:
            node_id: Unique identifier for this node (will be set later by IPv8Manager)
        """
        super().__init__(*args, **kwargs)
        
        self.node_id = node_id
        self.peer_node_ids = {}  # Peer -> node_id mapping
        
        # Message handlers
        self.add_message_handler(ChatMessagePayload, self.on_chat_message)
        self.add_message_handler(PeerInfoPayload, self.on_peer_info)
        
        # Callbacks
        self.on_chat_callback: Optional[Callable] = None
        
        logger.info(f"QuinkGLCommunity initialized for node '{node_id}'")
    
    def started(self):
        """Called when community is started."""
        logger.info(f"🚀 QuinkGL community STARTED for node '{self.node_id}'")
        logger.info(f"   - Community ID: {self.community_id.hex()}")
        logger.info(f"   - My peer: {self.my_peer.address}")
        
        # Start peer discovery via peer info exchange
        self.register_task("announce_peer_info", 
                          self._announce_peer_info, 
                          interval=10.0,  # Every 10 seconds
                          delay=0)
        
        # Announce to DHT for global discovery
        self.register_task("announce_to_dht",
                          self._announce_to_dht,
                          interval=30.0,  # Every 30 seconds
                          delay=5)
        
        logger.info("✅ QuinkGL community tasks registered")
    
    async def _announce_to_dht(self):
        """Announce our presence to DHT for peer discovery."""
        try:
            # Get DHT community if available
            for overlay in self.get_ipv8().overlays:
                if overlay.__class__.__name__ == 'DHTDiscoveryCommunity':
                    # Store our node_id in DHT
                    key = f"quinkgl_{self.node_id}".encode()
                    value = f"{self.my_peer.address[0]}:{self.my_peer.address[1]}".encode()
                    await overlay.store_value(key, value)
                    logger.debug(f"Announced to DHT: {self.node_id}")
                    break
        except Exception as e:
            logger.debug(f"DHT announcement failed: {e}")
    
    async def unload(self):
        """Called when community is being unloaded."""
        await super().unload()
        logger.info("QuinkGL community unloaded")
    
    async def _announce_peer_info(self):
        """Announce our node_id to all peers."""
        for peer in self.get_peers():
            self.ez_send(peer, PeerInfoPayload(self.node_id))
    
    def introduce_peer(self, peer_address: tuple):
        """
        Introduce a peer by address (from tunnel server).
        
        This helps bootstrap peer discovery when peers are on different networks.
        """
        # Walk to this address to discover the peer
        self.walk_to(peer_address)
    
    @lazy_wrapper(PeerInfoPayload)
    async def on_peer_info(self, peer: Peer, payload: PeerInfoPayload):
        """
        Handle peer info message.
        
        Stores node_id for peer identification.
        """
        self.peer_node_ids[peer] = payload.node_id
        logger.debug(f"Learned peer node_id: {peer.address} = {payload.node_id}")
    
    def send_chat(self, peer: Peer, text: str):
        """
        Send chat message to peer.
        
        Args:
            peer: Target peer
            text: Message text
        """
        payload = ChatMessagePayload(
            sender_id=self.node_id,
            text=text,
            timestamp=int(time.time() * 1000)
        )
        
        self.ez_send(peer, payload)
        logger.debug(f"Sent chat to {peer.address}: {text[:50]}...")
    
    @lazy_wrapper(ChatMessagePayload)
    async def on_chat_message(self, peer: Peer, payload: ChatMessagePayload):
        """
        Handle incoming chat message.
        
        Args:
            peer: Sender peer
            payload: Chat message payload
        """
        logger.info(f"Received chat from {payload.sender_id}: {payload.text[:50]}...")
        
        # Store sender's node_id
        self.peer_node_ids[peer] = payload.sender_id
        
        # Call callback if registered
        if self.on_chat_callback:
            await self.on_chat_callback(payload.sender_id, payload.text, payload.timestamp)
    
    def find_peer_by_node_id(self, node_id: str) -> Optional[Peer]:
        """
        Find peer by node ID.
        
        Args:
            node_id: Node ID to search for
            
        Returns:
            Peer object or None
        """
        for peer, peer_node_id in self.peer_node_ids.items():
            if peer_node_id == node_id:
                return peer
        
        return None
    
    def get_peer_node_ids(self) -> dict:
        """
        Get mapping of peers to node IDs.
        
        Returns:
            Dictionary {Peer: node_id}
        """
        return self.peer_node_ids.copy()
    
    def get_online_peers(self) -> list:
        """
        Get list of online peers with their node IDs.
        
        Returns:
            List of (peer, node_id) tuples
        """
        return [(peer, node_id) for peer, node_id in self.peer_node_ids.items()]
