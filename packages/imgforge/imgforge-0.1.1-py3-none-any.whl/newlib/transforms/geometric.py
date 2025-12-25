import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional
from ..core.image import Image

class BaseTransform:
    """Base class for all transforms."""
    def __call__(self, image: Image) -> Image:
        raise NotImplementedError

    def get_config(self) -> Dict[str, Any]:
        """Return parameters for serialization."""
        return {}

class Resize(BaseTransform):
    def __init__(self, width: int, height: int, interpolation: int = cv2.INTER_LINEAR):
        self.width = width
        self.height = height
        self.interpolation = interpolation

    def __call__(self, image: Image) -> Image:
        # If already size, skip? Good optimization for later.
        resized_data = cv2.resize(image.data, (self.width, self.height), interpolation=self.interpolation)
        return Image(resized_data, image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"width": self.width, "height": self.height, "interpolation": self.interpolation}

class Rotate(BaseTransform):
    def __init__(self, angle: float, keep_size: bool = False):
        """
        Rotate the image by an angle.
        
        Args:
            angle: Angle in degrees (counter-clockwise).
            keep_size: If True, crops the result to keep original size. 
                       If False (default), expands canvas to fit rotated image.
        """
        self.angle = angle
        self.keep_size = keep_size

    def __call__(self, image: Image) -> Image:
        h, w = image.height, image.width
        center = (w // 2, h // 2)
        
        # Rotation Matrix
        M = cv2.getRotationMatrix2D(center, self.angle, 1.0)
        
        if not self.keep_size:
            # Calculate new bounding box to prevent cutoff
            cos = np.abs(M[0, 0])
            sin = np.abs(M[0, 1])
            new_w = int((h * sin) + (w * cos))
            new_h = int((h * cos) + (w * sin))
            
            # Adjust translation
            M[0, 2] += (new_w / 2) - center[0]
            M[1, 2] += (new_h / 2) - center[1]
            size = (new_w, new_h)
        else:
            size = (w, h)
            
        rotated = cv2.warpAffine(image.data, M, size)
        return Image(rotated, image.color_space)
        
    def get_config(self) -> Dict[str, Any]:
        return {"angle": self.angle, "keep_size": self.keep_size}

class Flip(BaseTransform):
    def __init__(self, horizontal: bool = True, vertical: bool = False):
        self.horizontal = horizontal
        self.vertical = vertical

    def __call__(self, image: Image) -> Image:
        code = -1
        if self.horizontal and self.vertical:
            code = -1
        elif self.horizontal:
            code = 1
        elif self.vertical:
            code = 0
        else:
            return image.copy() # No flip

        flipped = cv2.flip(image.data, code)
        return Image(flipped, image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"horizontal": self.horizontal, "vertical": self.vertical}

class Crop(BaseTransform):
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __call__(self, image: Image) -> Image:
        h, w = image.height, image.width
        
        # Bounds checking
        x_start = max(0, self.x)
        y_start = max(0, self.y)
        x_end = min(w, self.x + self.width)
        y_end = min(h, self.y + self.height)
        
        cropped = image.data[y_start:y_end, x_start:x_end]
        return Image(cropped, image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}
