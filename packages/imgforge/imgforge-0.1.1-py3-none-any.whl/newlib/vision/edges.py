import cv2
import numpy as np
from typing import Dict, Any
from ..core.image import Image
from ..transforms.geometric import BaseTransform

class Canny(BaseTransform):
    def __init__(self, threshold1: float = 100, threshold2: float = 200):
        self.threshold1 = threshold1
        self.threshold2 = threshold2

    def __call__(self, image: Image) -> Image:
        # Canny works on grayscale usually, but CV2 handles conversion internally or we force it
        # If RGB, Canny uses intensity.
        edges = cv2.Canny(image.data, self.threshold1, self.threshold2)
        return Image(edges, "GRAY")

    def get_config(self) -> Dict[str, Any]:
        return {"threshold1": self.threshold1, "threshold2": self.threshold2}

class Sobel(BaseTransform):
    def __init__(self, dx: int = 1, dy: int = 1, ksize: int = 3):
        self.dx = dx
        self.dy = dy
        self.ksize = ksize

    def __call__(self, image: Image) -> Image:
        # Sobel typically on grayscale
        gray = image.to_gray().data
        sobel = cv2.Sobel(gray, cv2.CV_64F, self.dx, self.dy, ksize=self.ksize)
        
        # Convert back to uint8 absolute
        sobel_abs = cv2.convertScaleAbs(sobel)
        return Image(sobel_abs, "GRAY")

    def get_config(self) -> Dict[str, Any]:
        return {"dx": self.dx, "dy": self.dy, "ksize": self.ksize}
