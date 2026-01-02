from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union
import numpy as np

class AbstractModel(ABC):
    """
    Abstract base class for Machine Learning models in QuinkGL.
    This interface ensures that the framework remains agnostic to the underlying
    ML library (PyTorch, TensorFlow, Scikit-learn, etc.).
    """

    @abstractmethod
    def get_weights(self) -> List[np.ndarray]:
        """
        Retrieve the current model weights.
        
        Returns:
            List[np.ndarray]: A list of numpy arrays representing the model parameters.
        """
        pass

    @abstractmethod
    def set_weights(self, weights: List[np.ndarray]) -> None:
        """
        Update the model weights with new values.
        
        Args:
            weights (List[np.ndarray]): The new weights to apply.
        """
        pass

    @abstractmethod
    def train(self, data: Any, epochs: int = 1) -> Dict[str, float]:
        """
        Train the model on the provided local data.
        
        Args:
            data (Any): The training data (format depends on the specific implementation).
            epochs (int): Number of local training epochs.
            
        Returns:
            Dict[str, float]: Training metrics (e.g., {'loss': 0.5, 'accuracy': 0.8}).
        """
        pass

    @abstractmethod
    def evaluate(self, data: Any) -> Dict[str, float]:
        """
        Evaluate the model on the provided data.
        
        Args:
            data (Any): The evaluation data.
            
        Returns:
            Dict[str, float]: Evaluation metrics.
        """
        pass
