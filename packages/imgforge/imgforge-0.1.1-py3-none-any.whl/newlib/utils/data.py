from ..core.io import IO
from ..core.image import Image
from typing import Dict

# Dictionary of sample images and their URLs
_SAMPLES: Dict[str, str] = {
    # Lenna is reliable from upload.wikimedia
    "lenna": "https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png",
    # GitHub raw links sometimes flaky without ?raw=true or correct branch. Using stable version tag v0.21.0
    "astronaut": "https://github.com/scikit-image/scikit-image/blob/v0.21.0/skimage/data/astronaut.png?raw=true",
    "coins": "https://github.com/scikit-image/scikit-image/blob/v0.21.0/skimage/data/coins.png?raw=true",
    "camera": "https://github.com/scikit-image/scikit-image/blob/v0.21.0/skimage/data/camera.png?raw=true",
    "horse": "https://github.com/scikit-image/scikit-image/blob/v0.21.0/skimage/data/horse.png?raw=true",
    "coffee": "https://github.com/scikit-image/scikit-image/blob/v0.21.0/skimage/data/coffee.png?raw=true",
}

def get_sample(name: str) -> Image:
    """
    Get a sample image by name.
    
    Args:
        name: Name of the sample (e.g., 'lenna', 'astronaut').
        
    Returns:
        Image: Loaded sample image.
    """
    if name not in _SAMPLES:
        available = ", ".join(_SAMPLES.keys())
        raise ValueError(f"Unknown sample '{name}'. Available: {available}")
        
    url = _SAMPLES[name]
    # Use IO.from_url to handle downloading and caching
    try:
        data_rgb = IO.from_url(url, use_cache=True)
        return Image(data_rgb, color_space="RGB")
    except Exception as e:
        raise IOError(f"Failed to fetch sample '{name}': {e}")

def list_samples() -> list:
    """List available sample names."""
    return list(_SAMPLES.keys())
