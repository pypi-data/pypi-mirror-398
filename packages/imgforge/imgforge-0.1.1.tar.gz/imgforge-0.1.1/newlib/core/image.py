from __future__ import annotations
import numpy as np
import cv2
from typing import Optional, Union, Tuple
from pathlib import Path
import copy

class Image:
    """
    Core Image abstraction for newlib.
    
    Wraps a NumPy array to provide a fluent, pipeline-friendly API.
    By default, operations that modify the image return a new Image instance (immutable-ish).
    """

    def __init__(self, data: np.ndarray, color_space: str = "RGB"):
        """
        Initialize an Image from a NumPy array.
        
        Args:
            data: NumPy array (Hwy, Hwc, etc.).
            color_space: 'RGB', 'BGR', 'GRAY', 'HSV', etc.
        """
        self._data = data
        self._color_space = color_space.upper()
        self._validate()

    def _validate(self):
        """Ensure the internal data is valid."""
        if not isinstance(self._data, np.ndarray):
            raise TypeError(f"Image data must be a numpy array, got {type(self._data)}")
        if self._data.ndim not in (2, 3):
            raise ValueError(f"Image must be 2D or 3D, got shape {self._data.shape}")

    @classmethod
    def from_numpy(cls, arr: np.ndarray, color_space: str = "RGB") -> Image:
        """Create an Image from a NumPy array."""
        return cls(arr.copy(), color_space)

    @classmethod
    def open(cls, path: Union[str, Path]) -> Image:
        """
        Open an image from disk.
        
        Note: OpenCV loads in BGR by default. We convert to RGB for consistency.
        """
        path = str(path)
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"Could not open image at {path}")
        
        # Convert BGR to RGB by default
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return cls(img_rgb, color_space="RGB")

    def save(self, path: Union[str, Path], **kwargs) -> None:
        """
        Save the image to disk.
        
        Automatically handles RGB -> BGR conversion for OpenCV.
        """
        path = str(path)
        to_save = self._data
        
        if self._color_space == "RGB" and self._data.ndim == 3:
            to_save = cv2.cvtColor(self._data, cv2.COLOR_RGB2BGR)
        
        success = cv2.imwrite(path, to_save, [int(k) for k in kwargs.get('params', [])])
        if not success:
            raise IOError(f"Failed to save image to {path}")

    @property
    def data(self) -> np.ndarray:
        """Access the underlying NumPy array (read-only recommended)."""
        return self._data

    @property
    def shape(self) -> Tuple[int, ...]:
        return self._data.shape

    @property
    def dtype(self) -> np.dtype:
        return self._data.dtype

    @property
    def color_space(self) -> str:
        return self._color_space

    @property
    def width(self) -> int:
        return self._data.shape[1]

    @property
    def height(self) -> int:
        return self._data.shape[0]

    @property
    def channels(self) -> int:
        return 1 if self._data.ndim == 2 else self._data.shape[2]

    def to_numpy(self, copy: bool = True) -> np.ndarray:
        """Return the underlying NumPy array."""
        return self._data.copy() if copy else self._data

    def copy(self) -> Image:
        """Return a deep copy of the Image."""
        return Image(self._data.copy(), self._color_space)

    def __repr__(self) -> str:
        return f"Image(shape={self.shape}, dtype={self.dtype}, mode={self._color_space})"
    
    # --- Basic Transformations (Shortcuts) ---
    # These will be delegated to specific transform classes in a real pipeline context,
    # but having proper methods here is convenient for method chaining.
    
    def resize(self, width: int, height: int) -> Image:
        """Resize the image."""
        # Using cv2.resize directly for basic usage, but normally we'd use transforms.
        resized = cv2.resize(self._data, (width, height))
        return Image(resized, self._color_space)

    def to_gray(self) -> Image:
        """Convert to Grayscale."""
        if self._color_space == "GRAY":
            return self.copy()
        
        if self._color_space == "RGB":
            gray = cv2.cvtColor(self._data, cv2.COLOR_RGB2GRAY)
        elif self._color_space == "BGR":
            gray = cv2.cvtColor(self._data, cv2.COLOR_BGR2GRAY)
        else:
            raise NotImplementedError(f"Conversion from {self._color_space} to GRAY not supported yet.")
            
        return Image(gray, "GRAY")

