from newlib.transforms import geometric, color, filtering
from newlib.core.image import Image
import numpy as np

def test_rotate(sample_image):
    # Rotate 90 degrees
    rot = geometric.Rotate(90, keep_size=False)(sample_image)
    # 100x100 90deg is still 100x100
    assert rot.shape == (100, 100, 3)

def test_crop(sample_image):
    crop = geometric.Crop(10, 10, 20, 20)(sample_image)
    assert crop.width == 20
    assert crop.height == 20

def test_flip(sample_image):
    flipped = geometric.Flip(horizontal=True)(sample_image)
    assert flipped.shape == sample_image.shape
    # Check if actually flipped (col 0 becomes col 99)
    # sample_image col 0 is red [255,0,0], col 99 is green [0,255,0] (top half)
    # flipped col 0 should be green
    assert np.array_equal(flipped.data[0,0], [0, 255, 0])

def test_blur(sample_image):
    blurred = filtering.GaussianBlur(5)(sample_image)
    assert blurred.shape == sample_image.shape
    # Variance should likely decrease
    assert np.std(blurred.data) <= np.std(sample_image.data)

def test_color_jitter(sample_image):
    # Test that it runs and returns valid image
    from newlib.transforms.augmentation import ColorJitter
    aug = ColorJitter(brightness=0.5, contrast=0.5, saturation=0.5, hue=0.1)
    jittered = aug(sample_image)
    assert jittered.shape == sample_image.shape
    assert jittered.dtype == sample_image.dtype
