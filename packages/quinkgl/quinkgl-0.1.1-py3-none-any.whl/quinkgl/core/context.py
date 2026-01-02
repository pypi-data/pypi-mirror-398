"""
Execution Context

Context information for gossip learning execution.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class ExecutionContext:
    """
    Execution context for a gossip learning node.

    Contains all contextual information needed during execution,
    including configuration, state, and metadata.
    """

    # Node identification
    peer_id: str
    domain: str
    data_schema_hash: str

    # Training state
    current_round: int = 0
    total_samples_trained: int = 0

    # Performance metrics
    current_loss: Optional[float] = None
    current_accuracy: Optional[float] = None
    best_accuracy: float = 0.0

    # Network state
    connected_peer_count: int = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0

    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    last_gossip_time: Optional[datetime] = None
    last_training_time: Optional[datetime] = None

    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "peer_id": self.peer_id,
            "domain": self.domain,
            "data_schema_hash": self.data_schema_hash,
            "current_round": self.current_round,
            "total_samples_trained": self.total_samples_trained,
            "current_loss": self.current_loss,
            "current_accuracy": self.current_accuracy,
            "best_accuracy": self.best_accuracy,
            "connected_peer_count": self.connected_peer_count,
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received,
            "start_time": self.start_time.isoformat(),
            "last_gossip_time": self.last_gossip_time.isoformat() if self.last_gossip_time else None,
            "last_training_time": self.last_training_time.isoformat() if self.last_training_time else None,
            "metadata": self.metadata,
        }

    def update_metrics(self, loss: float = None, accuracy: float = None):
        """
        Update performance metrics.

        Args:
            loss: Current training loss
            accuracy: Current training accuracy
        """
        if loss is not None:
            self.current_loss = loss
        if accuracy is not None:
            self.current_accuracy = accuracy
            if accuracy > self.best_accuracy:
                self.best_accuracy = accuracy

    def increment_round(self):
        """Increment the round counter."""
        self.current_round += 1

    def add_metadata(self, key: str, value: Any):
        """Add custom metadata."""
        self.metadata[key] = value

    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
