"""
Connection Manager for Hybrid P2P

Manages connections with intelligent fallback:
1. Try STUN P2P (if enabled)
2. Fall back to tunnel relay (guaranteed to work)
"""

import asyncio
import logging
import json
from typing import Optional, Dict
from enum import Enum

from quinkgl.config import TUNNEL_CONFIG
from quinkgl.network.tunnel_client import TunnelClient
from quinkgl.network.ipv8_manager import IPv8Manager
from quinkgl.network.ipv8_community import QuinkGLCommunity
from quinkgl.network import tunnel_pb2

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Type of connection established."""
    IPV8_P2P = "ipv8_p2p"      # Direct P2P via IPv8
    TUNNEL_RELAY = "tunnel"     # Tunnel relay (fallback)


class Connection:
    """Base connection interface."""
    
    def __init__(self, peer_id: str, conn_type: ConnectionType):
        self.peer_id = peer_id
        self.type = conn_type
        self.latency = None
    
    async def send_message(self, text: str):
        """Send chat message to peer."""
        raise NotImplementedError
    
    async def close(self):
        """Close connection."""
        pass


class TunnelConnection(Connection):
    """Connection via tunnel relay (fallback)."""
    
    def __init__(self, tunnel_client: TunnelClient, peer_id: str):
        super().__init__(peer_id, ConnectionType.TUNNEL_RELAY)
        self.tunnel_client = tunnel_client
    
    async def send_message(self, text: str):
        """Send message via tunnel."""
        await self.tunnel_client.send_chat_message(self.peer_id, text)


class IPv8Connection(Connection):
    """Direct P2P connection via IPv8."""
    
    def __init__(self, peer_id: str, peer, community: QuinkGLCommunity):
        super().__init__(peer_id, ConnectionType.IPV8_P2P)
        self.peer = peer  # IPv8 Peer object
        self.community = community
    
    async def send_message(self, text: str):
        """Send message via IPv8 P2P."""
        self.community.send_chat(self.peer, text)


class ConnectionManager:
    """
    Manages peer connections with intelligent fallback.
    
    Strategy:
    1. If STUN enabled: Try STUN P2P
    2. If STUN disabled or failed: Use tunnel relay
    """
    
    def __init__(self, node_id: str, tunnel_server: str):
        """
        Initialize connection manager.
        
        Args:
            node_id: This node's unique ID
            tunnel_server: Tunnel server address (host:port)
        """
        self.node_id = node_id
        self.tunnel_server = tunnel_server
        
        # Modules
        self.ipv8_manager = IPv8Manager(node_id)
        self.tunnel_client = TunnelClient(tunnel_server, node_id)
        
        # Intercept tunnel messages for signaling
        self.tunnel_client.on_chat_message = self._intercept_tunnel_message
        self.tunnel_client.on_peer_list = self._on_peer_list_update
        
        # State
        self.connections: Dict[str, Connection] = {}
        self.negotiating_peers = set() # Peers currently negotiating IPv8
        self.ipv8_enabled = True  # IPv8 enabled by default
        self.app_chat_handler = None # Callback for actual chat messages
        self.on_status_change = None # Callback for connection status changes
        
        # Statistics
        self.stats = {
            "ipv8_attempts": 0,
            "ipv8_success": 0,
            "tunnel_fallback": 0,
        }
    
    async def start(self):
        """Start connection manager."""
        logger.info(f"Starting connection manager for node '{self.node_id}'")
        
        # Connect tunnel client (always needed for fallback)
        await self.tunnel_client.connect()
        logger.info("✅ Tunnel client connected (fallback ready)")
        
        # Start IPv8 if enabled
        if self.ipv8_enabled:
            logger.info("Starting IPv8 P2P...")
            try:
                # Start IPv8 with QuinkGL community
                await self.ipv8_manager.start(QuinkGLCommunity, self.node_id)
                
                # Set chat callback
                if self.ipv8_manager.community:
                    self.ipv8_manager.community.on_chat_callback = self._on_ipv8_chat
                
                logger.info(f"✅ IPv8 started on port {self.ipv8_manager.ipv8.endpoint.get_address()[1]}")
                
                # Broadcast our IPv8 address to any existing peers via tunnel
                await self.broadcast_ipv8_address()
            except Exception as e:
                logger.warning(f"⚠️  IPv8 failed to start: {e}, will use tunnel only")
                self.ipv8_enabled = False
        else:
            logger.info("IPv8 disabled, using tunnel only")
    
    async def broadcast_ipv8_address(self):
        """Broadcast our IPv8 address to all peers via Tunnel."""
        if not self.ipv8_enabled or not self.ipv8_manager.ipv8:
            return
            
        # Get our external address
        my_address = self.ipv8_manager.ipv8.endpoint.get_address()
        ip = my_address[0]
        port = my_address[1]
        
        # If bound to 0.0.0.0, try to get actual LAN IP
        if ip == "0.0.0.0":
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Doesn't need to be reachable
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
            except Exception:
                ip = "127.0.0.1" # Fallback to localhost
        
        payload = {
            "type": "IPV8_ANNOUNCE",
            "node_id": self.node_id,
            "ip": ip,
            "port": port
        }
        
        json_payload = json.dumps(payload)
        # print(f"📢 Broadcasting IPv8 address: {ip}:{port}") # Debug
        
        # We will send to peers as they appear in _on_peer_list_update
        pass 

    async def _on_peer_list_update(self, peer_ids: list):
        """Handle peer list update from tunnel."""
        if self.ipv8_enabled:
            # Get address logic (duplicated for now, should refactor)
            my_address = self.ipv8_manager.ipv8.endpoint.get_address()
            ip = my_address[0]
            port = my_address[1]
            
            if ip == "0.0.0.0":
                try:
                    import socket
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                    s.close()
                except Exception:
                    ip = "127.0.0.1"

            payload = {
                "type": "IPV8_ANNOUNCE",
                "node_id": self.node_id,
                "ip": ip,
                "port": port
            }
            json_payload = json.dumps(payload)
            
            for peer_id in peer_ids:
                if peer_id != self.node_id:
                    # Send announcement (hidden message)
                    # print(f"📢 Sending IPv8 announce to {peer_id}: {ip}:{port}")
                    await self.tunnel_client.send_chat_message(peer_id, json_payload)
        
        # Expose this event to ChatNode
        if hasattr(self, 'on_peer_list'):
             await self.on_peer_list(peer_ids)

    async def _intercept_tunnel_message(self, msg: tunnel_pb2.ChatMessage):
        """
        Intercept incoming tunnel messages.
        """
        try:
            # Try to parse as JSON
            data = json.loads(msg.text)
            
            if isinstance(data, dict) and data.get("type") == "IPV8_ANNOUNCE":
                # It's a signaling message!
                sender_id = data.get("node_id")
                ip = data.get("ip")
                port = data.get("port")
                
                if sender_id and ip and port:
                    # print(f"📨 Received IPv8 announcement from {sender_id}: {ip}:{port}")
                    logger.info(f"📨 Received IPv8 announcement from {sender_id}: {ip}:{port}")
                    
                    # Introduce to IPv8
                    self.introduce_peer_to_ipv8(sender_id, (ip, port))
                return
                
        except json.JSONDecodeError:
            pass
            
        # Forward to app
        if self.app_chat_handler:
            await self.app_chat_handler(msg)

    async def _on_ipv8_chat(self, sender_id: str, text: str, timestamp: int):
        """Handle incoming IPv8 chat message."""
        # This will be called by QuinkGLCommunity
        logger.debug(f"IPv8 chat from {sender_id}: {text[:50]}...")
        
        chat_msg = tunnel_pb2.ChatMessage(
            sender_id=sender_id,
            text=text,
            timestamp=timestamp
        )
        
        if self.app_chat_handler:
            await self.app_chat_handler(chat_msg)
    
    def introduce_peer_to_ipv8(self, peer_id: str, peer_address: tuple):
        """
        Introduce a peer from tunnel server to IPv8.
        
        This helps IPv8 discover peers on different networks.
        """
        if self.ipv8_manager.community and peer_address:
            logger.info(f"🔗 Introducing {peer_id} at {peer_address} to IPv8...")
            self.ipv8_manager.community.introduce_peer(peer_address)
            
            # Mark as negotiating
            self.negotiating_peers.add(peer_id)
            if self.on_status_change:
                asyncio.create_task(self.on_status_change(peer_id, "negotiating"))
            
            # Try to connect with retries (wait for handshake)
            asyncio.create_task(self._wait_and_connect_ipv8(peer_id))

    async def _wait_and_connect_ipv8(self, peer_id: str):
        """Wait for IPv8 discovery and connect."""
        for i in range(10): # Try for 10 seconds
            await asyncio.sleep(1.0)
            conn = await self._try_ipv8_p2p(peer_id)
            if conn:
                logger.info(f"🔄 Upgraded {peer_id} from Tunnel to IPv8 P2P!")
                # print(f"🔄 Upgraded {peer_id} from Tunnel to IPv8 P2P!")
                self.connections[peer_id] = conn
                self.stats["ipv8_success"] += 1
                
                # Negotiation success
                if peer_id in self.negotiating_peers:
                    self.negotiating_peers.remove(peer_id)
                
                if self.on_status_change:
                    await self.on_status_change(peer_id, "ipv8_success")
                return
        
        logger.warning(f"⚠️  IPv8 discovery timed out for {peer_id}")
        
        # Negotiation failed
        if peer_id in self.negotiating_peers:
            self.negotiating_peers.remove(peer_id)
            
        if self.on_status_change:
            await self.on_status_change(peer_id, "ipv8_failed")
    
    async def connect_to_peer(self, peer_id: str) -> Connection:
        """
        Connect to a peer with intelligent fallback.
        
        Args:
            peer_id: Peer's unique ID
        
        Returns:
            Connection object (IPv8 P2P or Tunnel)
        """
        if peer_id in self.connections:
            return self.connections[peer_id]
        
        logger.info(f"Connecting to peer '{peer_id}'...")
        
        # Try IPv8 P2P first
        if self.ipv8_enabled:
            self.stats["ipv8_attempts"] += 1
            
            conn = await self._try_ipv8_p2p(peer_id)
            if conn:
                logger.info(f"✅ IPv8 P2P connection established: {peer_id}")
                self.stats["ipv8_success"] += 1
                self.connections[peer_id] = conn
                return conn
            else:
                logger.info(f"⚠️  IPv8 P2P not available for {peer_id}, falling back to tunnel")
        
        # Fallback: Use tunnel relay
        conn = await self._use_tunnel(peer_id)
        logger.info(f"✅ Tunnel relay connection: {peer_id}")
        self.stats["tunnel_fallback"] += 1
        self.connections[peer_id] = conn
        return conn
    
    async def _try_ipv8_p2p(self, peer_id: str) -> Optional[IPv8Connection]:
        """
        Try to establish IPv8 P2P connection.
        
        IPv8 handles NAT traversal automatically via stochastic UDP hole punching.
        """
        if not self.ipv8_manager.community:
            logger.debug("IPv8 community not available")
            return None
        
        # Debug: Show all discovered peers
        all_peers = self.ipv8_manager.community.get_peers()
        peer_node_ids = self.ipv8_manager.community.get_peer_node_ids()
        
        logger.debug(f"IPv8 discovery status:")
        logger.debug(f"  - Total IPv8 peers discovered: {len(all_peers)}")
        logger.debug(f"  - Peers with node_id: {len(peer_node_ids)}")
        logger.debug(f"  - Looking for peer_id: {peer_id}")
        logger.debug(f"  - Known node_ids: {list(peer_node_ids.values())}")
        
        # Find peer by node_id
        peer = self.ipv8_manager.community.find_peer_by_node_id(peer_id)
        
        if peer:
            logger.info(f"✅ Found IPv8 peer for {peer_id}")
            return IPv8Connection(peer_id, peer, self.ipv8_manager.community)
        
        logger.debug(f"❌ IPv8 peer {peer_id} not discovered yet")
        return None

    async def _use_tunnel(self, peer_id: str) -> TunnelConnection:
        """
        Use tunnel relay (fallback).
        
        This always works!
        """
        return TunnelConnection(self.tunnel_client, peer_id)
    
    async def send_message(self, peer_id: str, text: str):
        """
        Send message to peer.
        
        Args:
            peer_id: Target peer ID
            text: Message text
        """
        if peer_id not in self.connections:
            await self.connect_to_peer(peer_id)
        
        conn = self.connections[peer_id]
        
        # If using tunnel, try to upgrade to IPv8
        if conn.type == ConnectionType.TUNNEL_RELAY and self.ipv8_enabled:
            ipv8_conn = await self._try_ipv8_p2p(peer_id)
            if ipv8_conn:
                logger.info(f"🔄 Upgraded {peer_id} from Tunnel to IPv8 P2P!")
                self.connections[peer_id] = ipv8_conn
                self.stats["ipv8_success"] += 1
                conn = ipv8_conn
        
        await conn.send_message(text)
    
    async def close(self):
        """Close all connections."""
        logger.info("Closing connection manager...")
        
        # Close all peer connections
        for conn in self.connections.values():
            await conn.close()
        
        # Stop IPv8
        if self.ipv8_enabled:
            await self.ipv8_manager.stop()
        
        # Close tunnel client
        await self.tunnel_client.close()
        
        # Print statistics
        self._print_stats()
    
    def _print_stats(self):
        """Print connection statistics."""
        total = self.stats.get("ipv8_attempts", 0)
        if total > 0:
            success_rate = (self.stats["ipv8_success"] / total) * 100
            logger.info("=" * 50)
            logger.info("Connection Statistics:")
            logger.info(f"  IPv8 attempts:    {self.stats['ipv8_attempts']}")
            logger.info(f"  IPv8 success:     {self.stats['ipv8_success']} ({success_rate:.1f}%)")
            logger.info(f"  Tunnel fallback:  {self.stats['tunnel_fallback']}")
            logger.info("=" * 50)
    
    def get_connection_type(self, peer_id: str) -> Optional[ConnectionType]:
        """Get connection type for a peer."""
        if peer_id in self.connections:
            return self.connections[peer_id].type
        return None
