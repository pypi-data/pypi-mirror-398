import io
import numpy as np
from typing import List

def serialize(weights: List[np.ndarray]) -> bytes:
    """
    Serialize list of numpy arrays using np.savez.
    This is more robust across numpy versions and safer than pickle.
    """
    buffer = io.BytesIO()
    # Use savez_compressed to save bandwidth
    np.savez_compressed(buffer, *weights)
    return buffer.getvalue()

def deserialize(data: bytes) -> List[np.ndarray]:
    """Deserialize bytes back to list of numpy arrays."""
    buffer = io.BytesIO(data)
    # allow_pickle=False ensures we only load arrays, preventing code execution attacks
    with np.load(buffer, allow_pickle=False) as loaded_data:
        # Files are stored as arr_0, arr_1, ... in order
        return [loaded_data[key] for key in sorted(loaded_data.files)]
