"""
Core Module

Core classes for the Gossip Learning Framework.
"""

from quinkgl.core.node import GLNode
from quinkgl.core.context import ExecutionContext

# Export from existing files
from quinkgl.core.model_interface import AbstractModel
from quinkgl.core.dummy_model import DummyModel

__all__ = [
    "GLNode",
    "ExecutionContext",
    "AbstractModel",
    "DummyModel",
]
