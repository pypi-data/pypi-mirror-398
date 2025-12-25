import cv2
import numpy as np
from typing import Dict, Any
from ..core.image import Image
from .geometric import BaseTransform

class ToGray(BaseTransform):
    def __call__(self, image: Image) -> Image:
        return image.to_gray()

    def get_config(self) -> Dict[str, Any]:
        return {}

class ToHSV(BaseTransform):
    def __call__(self, image: Image) -> Image:
        if image.color_space == "HSV":
            return image.copy()
        
        if image.color_space == "RGB":
            hsv = cv2.cvtColor(image.data, cv2.COLOR_RGB2HSV)
        elif image.color_space == "BGR":
            hsv = cv2.cvtColor(image.data, cv2.COLOR_BGR2HSV)
        elif image.color_space == "GRAY":
             # Gray to HSV? Usually typically convert Gray to BGR then HSV, but saturations will be 0
             bgr = cv2.cvtColor(image.data, cv2.COLOR_GRAY2BGR)
             hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        else:
            raise NotImplementedError(f"Conversion from {image.color_space} to HSV not supported.")
            
        return Image(hsv, "HSV")

class ToRGB(BaseTransform):
    def __call__(self, image: Image) -> Image:
        if image.color_space == "RGB":
            return image.copy()
            
        if image.color_space == "BGR":
            rgb = cv2.cvtColor(image.data, cv2.COLOR_BGR2RGB)
        elif image.color_space == "HSV":
            rgb = cv2.cvtColor(image.data, cv2.COLOR_HSV2RGB)
        elif image.color_space == "GRAY":
            rgb = cv2.cvtColor(image.data, cv2.COLOR_GRAY2RGB)
        else:
            raise NotImplementedError
            
        return Image(rgb, "RGB")

class ToBGR(BaseTransform):
    def __call__(self, image: Image) -> Image:
        if image.color_space == "BGR":
            return image.copy()
            
        if image.color_space == "RGB":
            bgr = cv2.cvtColor(image.data, cv2.COLOR_RGB2BGR)
        elif image.color_space == "HSV":
            bgr = cv2.cvtColor(image.data, cv2.COLOR_HSV2BGR)
        elif image.color_space == "GRAY":
            bgr = cv2.cvtColor(image.data, cv2.COLOR_GRAY2BGR)
        else:
             raise NotImplementedError

        return Image(bgr, "BGR")
