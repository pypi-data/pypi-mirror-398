import cv2
import numpy as np
from typing import Dict, Any, Union
from ..core.image import Image

def get_stats(image: Image) -> Dict[str, Any]:
    """
    Get basic statistics of the image.
    """
    data = image.data
    stats = {
        "mean": data.mean(),
        "std": data.std(),
        "min": data.min(),
        "max": data.max(),
        "shape": image.shape,
        "dtype": str(image.dtype)
    }
    
    # Per-channel stats if color
    if image.channels > 1:
        for i in range(image.channels):
            stats[f"channel_{i}_mean"] = data[:, :, i].mean()
            
    return stats

def calculate_histogram(image: Image, bins: int = 256) -> Dict[str, np.ndarray]:
    """
    Calculate histogram for each channel.
    """
    hists = {}
    if image.channels == 1:
        hist = cv2.calcHist([image.data], [0], None, [bins], [0, 256])
        hists["gray"] = hist.flatten()
    else:
        colors = ('b', 'g', 'r') if image.color_space == "BGR" else ('r', 'g', 'b')
        for i, col in enumerate(colors):
            hist = cv2.calcHist([image.data], [i], None, [bins], [0, 256])
            hists[col] = hist.flatten()
            
    return hists
