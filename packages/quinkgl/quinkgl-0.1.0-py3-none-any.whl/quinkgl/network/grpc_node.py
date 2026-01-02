import asyncio
import logging
import time
import uuid
from typing import List, Dict, Optional
from concurrent import futures
import numpy as np

import grpc
from quinkgl.network import gossip_pb2, gossip_pb2_grpc
from quinkgl.network.tunnel_client import TunnelClient
from quinkgl.core.model_interface import AbstractModel
from quinkgl.utils.serialization import serialize, deserialize
from quinkgl.config import GOSSIP_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

class GossipServicer(gossip_pb2_grpc.GossipServiceServicer):
    """gRPC service implementation for gossip learning."""
    
    def __init__(self, node):
        self.node = node
    
    async def GossipStream(self, request_iterator, context):
        """Bidirectional streaming for weight exchange."""
        peer_addr = context.peer()
        logger.info(f"✓ New gossip stream from {peer_addr}")
        
        # Handle incoming weights in background
        async def handle_incoming():
            try:
                async for weight_update in request_iterator:
                    await self.node.handle_weight_update(weight_update)
            except Exception as e:
                logger.error(f"Error in incoming stream from {peer_addr}: {e}")
        
        # Start background task for incoming
        incoming_task = asyncio.create_task(handle_incoming())
        
        # Send our weights periodically
        try:
            while not context.cancelled():
                weight_update = self.node.create_weight_update()
                yield weight_update
                await asyncio.sleep(GOSSIP_CONFIG["publish_interval"])
        except asyncio.CancelledError:
            logger.info(f"Stream to {peer_addr} cancelled")
        except Exception as e:
            logger.error(f"Error in outgoing stream to {peer_addr}: {e}")
        finally:
            incoming_task.cancel()
    
    async def GetPeerInfo(self, request, context):
        """Return information about this node."""
        return gossip_pb2.PeerInfo(
            node_id=self.node.node_id,
            address=f"{self.node.host}:{self.node.port}",
            num_peers=len(self.node.active_peers),
            uptime=int(time.time() - self.node.start_time)
        )

class GRPCNode:
    """gRPC-based gossip learning node."""
    
    def __init__(
        self,
        host: str,
        port: int,
        model: AbstractModel,
        node_id: Optional[str] = None,
        peer_addresses: List[str] = None,
        peer_ids: List[str] = None,
        tunnel_server: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.model = model
        self.peer_addresses = peer_addresses if peer_addresses else []
        self.peer_ids = peer_ids if peer_ids else []
        self.tunnel_server = tunnel_server
        
        # Generate or use provided node ID
        self.node_id = node_id if node_id else str(uuid.uuid4())[:8]
        
        # Server and connections
        self.server = None
        self.active_peers: Dict[str, grpc.aio.Channel] = {}
        self.tunnel_client: Optional[TunnelClient] = None
        self.tunnel_peers: Dict[str, bool] = {}  # peer_id -> connected
        self.start_time = time.time()
        self.round = 0
        
        logger.info(f"Initialized node {self.node_id}")
        if self.tunnel_server:
            logger.info(f"Tunnel mode enabled via {self.tunnel_server}")
    
    async def start(self):
        """Start the gRPC server and connect to peers."""
        # Start gRPC server
        self.server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),
            ]
        )
        
        gossip_pb2_grpc.add_GossipServiceServicer_to_server(
            GossipServicer(self), self.server
        )
        
        listen_addr = f'{self.host}:{self.port}'
        self.server.add_insecure_port(listen_addr)
        
        await self.server.start()
        logger.info(f"✓ gRPC server started on {listen_addr}")
        logger.info(f"Node ID: {self.node_id}")
        
        # Connect to tunnel server if enabled
        if self.tunnel_server:
            await self.setup_tunnel()
        
        # Connect to direct peers
        if self.peer_addresses:
            await self.connect_to_peers()
        
        # Connect to tunnel peers
        if self.tunnel_client and self.peer_ids:
            for peer_id in self.peer_ids:
                self.tunnel_peers[peer_id] = True
                logger.info(f"Registered tunnel peer: {peer_id}")
        
        # Start gossip loop
        asyncio.create_task(self.gossip_loop())
        
        # Keep server running
        try:
            await self.server.wait_for_termination()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            await self.stop()
    
    async def connect_to_peers(self):
        """Connect to specified peer addresses."""
        for peer_addr in self.peer_addresses:
            try:
                logger.info(f"Connecting to peer {peer_addr}...")
                
                channel = grpc.aio.insecure_channel(
                    peer_addr,
                    options=[
                        ('grpc.max_send_message_length', 50 * 1024 * 1024),
                        ('grpc.max_receive_message_length', 50 * 1024 * 1024),
                    ]
                )
                
                stub = gossip_pb2_grpc.GossipServiceStub(channel)
                
                # Test connection
                peer_info = await stub.GetPeerInfo(gossip_pb2.Empty())
                logger.info(f"✓ Connected to peer {peer_info.node_id} at {peer_addr}")
                
                # Start bidirectional stream
                asyncio.create_task(self.gossip_with_peer(stub, peer_addr))
                
                self.active_peers[peer_addr] = channel
                
            except Exception as e:
                logger.error(f"✗ Failed to connect to {peer_addr}: {e}")
    
    async def gossip_with_peer(self, stub, peer_addr):
        """Maintain bidirectional stream with a peer."""
        try:
            async def request_generator():
                while peer_addr in self.active_peers:
                    yield self.create_weight_update()
                    await asyncio.sleep(GOSSIP_CONFIG["publish_interval"])
            
            async for weight_update in stub.GossipStream(request_generator()):
                await self.handle_weight_update(weight_update)
                
        except Exception as e:
            logger.error(f"Gossip stream with {peer_addr} ended: {e}")
            if peer_addr in self.active_peers:
                del self.active_peers[peer_addr]
    
    def create_weight_update(self) -> gossip_pb2.WeightUpdate:
        """Create a weight update message from current model."""
        weights = self.model.get_weights()
        
        layers = []
        for i, weight_array in enumerate(weights):
            layer = gossip_pb2.Layer(
                name=f"layer_{i}",
                weights=weight_array.flatten().tolist(),
                shape=list(weight_array.shape)
            )
            layers.append(layer)
        
        return gossip_pb2.WeightUpdate(
            node_id=self.node_id,
            timestamp=int(time.time() * 1000),
            layers=layers,
            round=self.round
        )
    
    async def handle_weight_update(self, update: gossip_pb2.WeightUpdate):
        """Process received weight update."""
        if update.node_id == self.node_id:
            return  # Ignore own messages
        
        try:
            # Reconstruct numpy arrays from protobuf
            received_weights = []
            for layer in update.layers:
                weight_array = np.array(layer.weights).reshape(layer.shape)
                received_weights.append(weight_array)
            
            # Merge with local model
            self.merge_weights(received_weights)
            logger.info(f"✓ Received and merged weights from {update.node_id} (round {update.round})")
            
        except Exception as e:
            logger.error(f"Error processing weight update: {e}")
    
    def merge_weights(self, received_weights: List[np.ndarray]):
        """Merge received weights with local model (simple averaging)."""
        current_weights = self.model.get_weights()
        new_weights = []
        
        for local, received in zip(current_weights, received_weights):
            averaged = (local + received) / 2.0
            new_weights.append(averaged)
        
        self.model.set_weights(new_weights)
        self.round += 1
    
    async def setup_tunnel(self):
        """Setup tunnel client connection."""
        try:
            self.tunnel_client = TunnelClient(self.tunnel_server, self.node_id)
            
            # Set callbacks
            self.tunnel_client.on_weight_update = self.handle_weight_update
            self.tunnel_client.on_peer_list = self.handle_tunnel_peer_list
            
            # Connect to tunnel server
            await self.tunnel_client.connect()
            
        except Exception as e:
            logger.error(f"Failed to setup tunnel: {e}")
            self.tunnel_client = None
    
    async def handle_tunnel_peer_list(self, peer_ids: List[str]):
        """Handle peer list update from tunnel server."""
        logger.info(f"Tunnel peer list updated: {peer_ids}")
        # Update tunnel peers
        for peer_id in peer_ids:
            if peer_id not in self.tunnel_peers:
                self.tunnel_peers[peer_id] = True
    
    async def gossip_loop(self):
        """Periodically send weight updates to tunnel peers."""
        while True:
            await asyncio.sleep(GOSSIP_CONFIG["publish_interval"])
            
            if self.tunnel_client and self.tunnel_peers:
                weight_update = self.create_weight_update()
                
                for peer_id in self.tunnel_peers:
                    try:
                        await self.tunnel_client.send_weight_update(peer_id, weight_update)
                    except Exception as e:
                        logger.error(f"Failed to send weight update to {peer_id}: {e}")
    
    async def stop(self):
        """Gracefully stop the node."""
        logger.info("Stopping node...")
        
        # Close tunnel client
        if self.tunnel_client:
            await self.tunnel_client.close()
        
        # Close peer connections
        for channel in self.active_peers.values():
            await channel.close()
        
        # Stop server
        if self.server:
            await self.server.stop(grace=5)
        
        logger.info("Node stopped")
