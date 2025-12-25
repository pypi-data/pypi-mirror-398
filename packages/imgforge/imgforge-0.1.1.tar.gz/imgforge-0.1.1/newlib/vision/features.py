import cv2
import numpy as np
from typing import Dict, Any, Tuple
from ..core.image import Image
from ..transforms.geometric import BaseTransform

class DrawFeatures(BaseTransform):
    """
    Detects features and draws them on the image.
    """
    def __init__(self, method: str = "ORB", max_features: int = 500, color: Tuple[int, int, int] = (255, 0, 0)):
        self.method = method.upper()
        self.max_features = max_features
        self.color = color # Note: cv2.drawKeypoints handles color oddly sometimes, but we'll try default
        
        if self.method == "ORB":
            self.detector = cv2.ORB_create(nfeatures=max_features)
        elif self.method == "FAST":
            self.detector = cv2.FastFeatureDetector_create()
        else:
            raise ValueError(f"Unknown feature method: {method}")

    def __call__(self, image: Image) -> Image:
        if image.channels > 1:
            gray = image.to_gray().data
        else:
            gray = image.data
            
        keypoints = self.detector.detect(gray, None)
        
        # Draw
        output_data = cv2.drawKeypoints(image.data, keypoints, None, color=self.color, flags=0)
        return Image(output_data, image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"method": self.method, "max_features": self.max_features}
