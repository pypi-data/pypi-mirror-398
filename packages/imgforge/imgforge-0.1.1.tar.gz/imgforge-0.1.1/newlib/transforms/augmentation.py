import random
from typing import Dict, Any, Tuple
from ..core.image import Image
from .geometric import Rotate, Flip, Crop, BaseTransform

class RandomRotate(BaseTransform):
    def __init__(self, limit: Tuple[int, int] = (-90, 90), p: float = 0.5):
        self.limit = limit
        self.p = p

    def __call__(self, image: Image) -> Image:
        if random.random() < self.p:
            angle = random.uniform(self.limit[0], self.limit[1])
            return Rotate(angle, keep_size=False)(image)
        return image

    def get_config(self) -> Dict[str, Any]:
        return {"limit": self.limit, "p": self.p}

class RandomFlip(BaseTransform):
    def __init__(self, horizontal: bool = True, vertical: bool = False, p: float = 0.5):
        self.horizontal = horizontal
        self.vertical = vertical
        self.p = p

    def __call__(self, image: Image) -> Image:
        if random.random() < self.p:
            return Flip(self.horizontal, self.vertical)(image)
        return image

    def get_config(self) -> Dict[str, Any]:
        return {"horizontal": self.horizontal, "vertical": self.vertical, "p": self.p}

class ColorJitter(BaseTransform):
    def __init__(self, brightness: float = 0, contrast: float = 0, saturation: float = 0, hue: float = 0):
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self.hue = hue

    def __call__(self, image: Image) -> Image:
        # Implementation relying on CV2/NumPy
        import cv2
        import numpy as np
        
        data = image.data.astype(np.float32)
        
        # Brightness
        if self.brightness > 0:
            factor = 1.0 + random.uniform(-self.brightness, self.brightness)
            data *= factor
            
        # Contrast
        if self.contrast > 0:
            factor = 1.0 + random.uniform(-self.contrast, self.contrast)
            mean = np.mean(data, axis=(0, 1), keepdims=True)
            data = (data - mean) * factor + mean
            
        data = np.clip(data, 0, 255).astype(np.uint8)
        
        # Saturation/Hue need HSV
        if (self.saturation > 0 or self.hue > 0) and image.channels == 3:
             # Convert usually RGB -> HSV
             hsv = cv2.cvtColor(data, cv2.COLOR_RGB2HSV).astype(np.float32)
             
             if self.saturation > 0:
                 s_factor = 1.0 + random.uniform(-self.saturation, self.saturation)
                 hsv[:,:,1] *= s_factor
                 
             if self.hue > 0:
                 h_factor = random.uniform(-self.hue, self.hue)
                 hsv[:,:,0] += (h_factor * 179.0) # approx hue range usually 0-179 in cv2
                 
             hsv[:,:,1] = np.clip(hsv[:,:,1], 0, 255)
             hsv[:,:,0] = np.clip(hsv[:,:,0], 0, 179)
             
             data = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
             
        return Image(data, image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"brightness": self.brightness, "contrast": self.contrast, "saturation": self.saturation, "hue": self.hue}

