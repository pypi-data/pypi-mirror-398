import numpy as np
from typing import List, Dict, Any
from quinkgl.core.model_interface import AbstractModel

class DummyModel(AbstractModel):
    def __init__(self, size: int = 10):
        # Initialize random weights
        self.weights = [np.random.rand(size)]

    def get_weights(self) -> List[np.ndarray]:
        return self.weights

    def set_weights(self, weights: List[np.ndarray]) -> None:
        self.weights = weights

    def train(self, data: Any, epochs: int = 1) -> Dict[str, float]:
        # Simulate training by slightly modifying weights
        self.weights = [w + np.random.normal(0, 0.01, w.shape) for w in self.weights]
        return {'loss': np.random.random()}

    def evaluate(self, data: Any) -> Dict[str, float]:
        return {'accuracy': np.random.random()}
