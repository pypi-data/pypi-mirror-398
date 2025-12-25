import cv2
import numpy as np
from typing import Dict, Any
from ..core.image import Image
from .geometric import BaseTransform

class GaussianBlur(BaseTransform):
    def __init__(self, kernel_size: int = 5, sigma: float = 0):
        if kernel_size % 2 == 0:
            kernel_size += 1 # Kernel must be odd
        self.kernel_size = kernel_size
        self.sigma = sigma

    def __call__(self, image: Image) -> Image:
        blurred = cv2.GaussianBlur(image.data, (self.kernel_size, self.kernel_size), self.sigma)
        return Image(blurred, image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"kernel_size": self.kernel_size, "sigma": self.sigma}

class MedianBlur(BaseTransform):
    def __init__(self, kernel_size: int = 5):
        if kernel_size % 2 == 0:
            kernel_size += 1
        self.kernel_size = kernel_size

    def __call__(self, image: Image) -> Image:
        blurred = cv2.medianBlur(image.data, self.kernel_size)
        return Image(blurred, image.color_space)
    
    def get_config(self) -> Dict[str, Any]:
        return {"kernel_size": self.kernel_size}

class BilateralFilter(BaseTransform):
    def __init__(self, d: int = 9, sigma_color: float = 75, sigma_space: float = 75):
        self.d = d
        self.sigma_color = sigma_color
        self.sigma_space = sigma_space
    
    def __call__(self, image: Image) -> Image:
        filtered = cv2.bilateralFilter(image.data, self.d, self.sigma_color, self.sigma_space)
        return Image(filtered, image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"d": self.d, "sigma_color": self.sigma_color, "sigma_space": self.sigma_space}

class Sharpen(BaseTransform):
    def __init__(self, amount: float = 1.0):
        self.amount = amount
    
    def __call__(self, image: Image) -> Image:
        # Unsharp masking approach
        gaussian = cv2.GaussianBlur(image.data, (0, 0), 3)
        weighted = cv2.addWeighted(image.data, 1.0 + self.amount, gaussian, -self.amount, 0)
        return Image(weighted, image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"amount": self.amount}
