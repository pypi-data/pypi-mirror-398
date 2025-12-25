import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
from ..core.image import Image
from ..transforms.geometric import BaseTransform

def find_contours(image: Image, mode: int = cv2.RETR_EXTERNAL, method: int = cv2.CHAIN_APPROX_SIMPLE) -> List[np.ndarray]:
    """
    Find contours in an image.
    
    Args:
        image: Input image (will be converted to gray/binary if needed).
        mode: Contour retrieval mode.
        method: Contour approximation method.
        
    Returns:
        List of contours (numpy arrays).
    """
    if image.channels > 1:
        gray = image.to_gray().data
    else:
        gray = image.data
        
    # Usually need thresholding first, but let's assume user handled that or we do basic auto-threshold
    # Auto-threshold for robust finding
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(binary, mode, method)
    return list(contours)

class DrawContours(BaseTransform):
    """
    Pipeline transform to find and draw contours on the image.
    """
    def __init__(self, color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2):
        self.color = color
        self.thickness = thickness
        
    def __call__(self, image: Image) -> Image:
        contours = find_contours(image)
        
        # Draw on a copy of the original image (likely RGB)
        output_data = image.data.copy()
        
        # Ensure we can draw color on it
        if image.color_space == "GRAY":
            output_data = cv2.cvtColor(output_data, cv2.COLOR_GRAY2RGB)
            
        cv2.drawContours(output_data, contours, -1, self.color, self.thickness)
        
        return Image(output_data, "RGB" if image.color_space == "GRAY" else image.color_space)

    def get_config(self) -> Dict[str, Any]:
        return {"color": self.color, "thickness": self.thickness}
