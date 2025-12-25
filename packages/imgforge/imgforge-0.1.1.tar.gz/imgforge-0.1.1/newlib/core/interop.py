from __future__ import annotations
import numpy as np
from typing import Optional, Any, Union

# Optional imports
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import tensorflow as tf
    HAS_TF = True
except ImportError:
    HAS_TF = False

def to_torch(data: np.ndarray, device: Optional[Union[str, 'torch.device']] = None) -> 'torch.Tensor':
    """
    Convert a NumPy array to a PyTorch tensor.
    
    Automatically handles HWC -> CHW conversion if input is 3D (standard image),
    which is the standard for PyTorch Vision models.
    
    Args:
        data: Input numpy array (H, W, C) or (H, W).
        device: Target device (cpu, cuda, etc.).
        
    Returns:
        torch.Tensor: (C, H, W) float32 tensor normalized to [0, 1] if requested? 
                      Current impl: keeps dtype, just permutes dimensions.
    """
    if not HAS_TORCH:
        raise ImportError("PyTorch is not installed. Install it with `pip install torch`.")

    tensor = torch.from_numpy(data)
    
    # If 3D (H, W, C), permute to (C, H, W)
    if data.ndim == 3:
        tensor = tensor.permute(2, 0, 1)
    
    if device:
        tensor = tensor.to(device)
        
    return tensor

def from_torch(tensor: 'torch.Tensor', to_numpy: bool = True) -> Union[np.ndarray, 'torch.Tensor']:
    """
    Convert a PyTorch tensor back to a NumPy array (H, W, C).
    
    Args:
        tensor: Input tensor (C, H, W) or (N, C, H, W).
        to_numpy: If True, returns np.ndarray. If False, returns cpu tensor in HWC.
    
    Returns:
        np.ndarray: (H, W, C) array.
    """
    if not HAS_TORCH:
        raise ImportError("PyTorch is not installed.")

    if tensor.ndim == 4:
        # Batch mode, take first or squeeze? Let's assume single image for now 
        # or warn. For robust lib, handle batch.
        # For now: Squeeze if N=1
        if tensor.shape[0] == 1:
            tensor = tensor.squeeze(0)
        else:
            raise ValueError("Batch processing not fully supported in from_torch yet.")

    if tensor.ndim == 3:
        # CHW -> HWC
        tensor = tensor.permute(1, 2, 0)
        
    if to_numpy:
        return tensor.detach().cpu().numpy()
    return tensor

def to_tf(data: np.ndarray) -> 'tf.Tensor':
    """
    Convert a NumPy array to a TensorFlow tensor.
    
    TF typically expects (H, W, C), so no permutation needed usually.
    """
    if not HAS_TF:
        raise ImportError("TensorFlow is not installed.")
    
    return tf.convert_to_tensor(data)

def from_tf(tensor: 'tf.Tensor') -> np.ndarray:
    """Convert a TF tensor back to NumPy."""
    if not HAS_TF:
        raise ImportError("TensorFlow is not installed.")
        
    return tensor.numpy()
