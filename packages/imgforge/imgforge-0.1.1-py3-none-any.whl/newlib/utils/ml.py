import numpy as np
from typing import Tuple, List, Optional
from ..core.image import Image
from ..core.pipeline import Pipeline
from ..core.interop import to_torch

class Normalizer:
    """
    Standard normalization for ML models (e.g. ImageNet statistics).
    """
    def __init__(self, mean: Tuple[float, float, float] = (0.485, 0.456, 0.406), 
                 std: Tuple[float, float, float] = (0.229, 0.224, 0.225)):
        self.mean = np.array(mean).reshape(1, 1, 3)
        self.std = np.array(std).reshape(1, 1, 3)

    def __call__(self, image: Image) -> Image:
        # Assuming image is 0-255 uint8, convert to 0-1 float usually
        data = image.data.astype(np.float32) / 255.0
        
        # Check channels
        if data.ndim == 2:
            data = np.stack([data]*3, axis=-1) # Force RGB
            
        data = (data - self.mean) / self.std
        
        # Return as image? Image usually wraps numpy. 
        # But this data is float and potentially negative. 
        # Our Image class didn't restrict dtype strictly but CV2 functions might complain.
        return Image(data, "RGB")

# Minimal Dataset Wrapper for PyTorch
try:
    from torch.utils.data import Dataset
    
    class NewlibDataset(Dataset):
        def __init__(self, file_paths: List[str], pipeline: Optional[Pipeline] = None, transform: Optional[Pipeline] = None):
            self.file_paths = file_paths
            # Support both naming conventions
            self.pipeline = pipeline or transform
            
        def __len__(self):
            return len(self.file_paths)
            
        def __getitem__(self, idx):
            path = self.file_paths[idx]
            image = Image.open(path)
            
            if self.pipeline:
                image = self.pipeline(image)
                
            # Convert to torch tensor at the end standardly
            return to_torch(image.data)
            
except ImportError:
    pass
