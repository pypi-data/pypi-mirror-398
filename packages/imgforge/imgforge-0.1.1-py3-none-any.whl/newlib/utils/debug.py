import matplotlib.pyplot as plt
import numpy as np
import cv2
from typing import Union, List, Optional
from ..core.image import Image

def show(image: Union[Image, np.ndarray], title: str = "Image", figsize: tuple = (8, 8), cmap: str = None) -> None:
    """
    Display an image using matplotlib.
    
    Args:
        image: Image object or numpy array.
        title: Title of the plot.
        figsize: Figure size.
        cmap: Color map (e.g., 'gray' for grayscale).
    """
    if isinstance(image, Image):
        data = image.data
        if image.color_space == "GRAY":
            cmap = "gray"
    elif isinstance(image, np.ndarray):
        data = image
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")

    plt.figure(figsize=figsize)
    # If standard RGB, no cmap needed usually, but if 2D array, default to viridis unless specified
    if data.ndim == 2 and cmap is None:
        cmap = "gray"
        
    plt.imshow(data, cmap=cmap)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.show()

def compare(img1: Union[Image, np.ndarray], img2: Union[Image, np.ndarray], title1: str = "Original", title2: str = "Processed", figsize: tuple = (12, 6)) -> None:
    """
    Compare two images side-by-side.
    """
    # Extract data 1
    if isinstance(img1, Image):
        d1 = img1.data
        cmap1 = "gray" if img1.color_space == "GRAY" else None
    else:
        d1 = img1
        cmap1 = "gray" if d1.ndim == 2 else None
        
    # Extract data 2
    if isinstance(img2, Image):
        d2 = img2.data
        cmap2 = "gray" if img2.color_space == "GRAY" else None
    else:
        d2 = img2
        cmap2 = "gray" if d2.ndim == 2 else None

    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    axes[0].imshow(d1, cmap=cmap1)
    axes[0].set_title(title1)
    axes[0].axis("off")
    
    axes[1].imshow(d2, cmap=cmap2)
    axes[1].set_title(title2)
    axes[1].axis("off")
    
    plt.tight_layout()
    plt.show()

def explore(image: Image) -> None:
    """
    Print a summary of image properties.
    """
    print(f"--- Image Exploration ---")
    print(f"Shape: {image.shape}")
    print(f"Dtype: {image.dtype}")
    print(f"Color Space: {image.color_space}")
    print(f"Min/Max: {image.data.min()} / {image.data.max()}")
    print(f"Mean: {image.data.mean():.2f}")
    if image.channels > 1:
        for i in range(image.channels):
            print(f"  Ch{i} Mean: {image.data[:,:,i].mean():.2f}")
    print("-------------------------")
