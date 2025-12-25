import cv2
import numpy as np
import requests
import hashlib
import tempfile
from pathlib import Path
from typing import Union, Optional

class IO:
    """
    Unified IO handler for loading and saving images.
    Includes caching for remote images.
    """
    
    _CACHE_DIR = Path(tempfile.gettempdir()) / "newlib_cache"

    @staticmethod
    def _get_cache_path(url: str) -> Path:
        """Generate a cache path based on the URL hash."""
        IO._CACHE_DIR.mkdir(parents=True, exist_ok=True)
        hash_name = hashlib.md5(url.encode()).hexdigest()
        # Simplistic extension guessing or just save as bin
        return IO._CACHE_DIR / hash_name

    @staticmethod
    def from_url(url: str, use_cache: bool = True) -> np.ndarray:
        """
        Load an image from a URL.
        
        Args:
            url: Image URL.
            use_cache: Whether to cache the downloaded image locally.
            
        Returns:
            np.ndarray: Loaded image in RGB format.
        """
        cache_path = IO._get_cache_path(url)
        
        if use_cache and cache_path.exists():
            # Load from cache
            img = cv2.imread(str(cache_path))
            if img is not None:
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
        # Download
        try:
            headers = {"User-Agent": "newlib/0.1.0 (Educational Purpose)"}
            response = requests.get(url, stream=True, timeout=10, headers=headers)
            response.raise_for_status()
            
            # Read bytes
            image_bytes = np.asarray(bytearray(response.content), dtype="uint8")
            img = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError(f"Failed to decode image from URL: {url}")
            
            if use_cache:
                # Save to cache (as png or original bytes? let's save what we decoded to be safe or original bytes)
                # Proper way: write original bytes
                with open(cache_path, "wb") as f:
                    f.write(response.content)
            
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
        except Exception as e:
            raise IOError(f"Failed to load image from URL {url}: {e}")

    @staticmethod
    def load(path: Union[str, Path]) -> np.ndarray:
        """
        Load image from disk.
        """
        path = str(path)
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"Image not found at {path}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @staticmethod
    def save(data: np.ndarray, path: Union[str, Path], params: Optional[list] = None) -> None:
        """
        Save image to disk. Input is expected to be RGB.
        """
        # Convert RGB to BGR for OpenCV
        if data.ndim == 3:
            to_save = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
        else:
            to_save = data
            
        success = cv2.imwrite(str(path), to_save, params)
        if not success:
            raise IOError(f"Failed to save image to {path}")
