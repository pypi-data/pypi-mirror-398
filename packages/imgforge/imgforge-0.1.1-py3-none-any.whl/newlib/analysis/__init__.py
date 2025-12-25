from .stats import get_stats, calculate_histogram
from .quality import estimate_blur, estimate_brightness
from .similarity import mse, psnr
from ..core.image import Image
from typing import Dict, Any

def inspect(image: Image) -> Dict[str, Any]:
    """
    Generate a comprehensive inspection report for the image.
    """
    stats = get_stats(image)
    blur = estimate_blur(image)
    brightness = estimate_brightness(image)
    
    return {
        "basic_stats": stats,
        "quality": {
            "blur_variance": blur,
            "is_likely_blurred": blur < 100,
            "brightness_mean": brightness
        },
        "meta": {
            "resolution": f"{image.width}x{image.height}",
            "channels": image.channels
        }
    }
