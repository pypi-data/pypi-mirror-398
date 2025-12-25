import cv2
import numpy as np
from ..core.image import Image

def estimate_blur(image: Image) -> float:
    """
    Estimate blur using the variance of Laplacian method.
    Higher value means sharper image. Low value (<100) often indicates blur.
    """
    if image.channels > 1:
        gray = image.to_gray().data
    else:
        gray = image.data
        
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    return variance

def estimate_brightness(image: Image) -> float:
    """
    Estimate average brightness.
    """
    if image.color_space == "HSV":
        # Use V channel
        return image.data[:, :, 2].mean()
    elif image.channels > 1:
        # Convert to HSV or just mean of gray
        gray = cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY) if image.color_space == "RGB" else \
               cv2.cvtColor(image.data, cv2.COLOR_BGR2GRAY)
        return gray.mean()
    else:
        return image.data.mean()
