from newlib.core.image import Image
import numpy as np
import pytest

def test_image_init(sample_image_np):
    img = Image(sample_image_np, "RGB")
    assert img.width == 100
    assert img.height == 100
    assert img.channels == 3
    assert img.color_space == "RGB"
    assert img.shape == (100, 100, 3)

def test_image_from_numpy(sample_image_np):
    img = Image.from_numpy(sample_image_np)
    assert np.array_equal(img.data, sample_image_np)

def test_image_open(temp_image_path):
    img = Image.open(temp_image_path)
    # OpenCV loads BGR, Image converts to RGB
    assert img.color_space == "RGB"
    assert img.shape == (100, 100, 3)

def test_image_conversion(sample_image):
    gray = sample_image.to_gray()
    assert gray.color_space == "GRAY"
    assert gray.channels == 1
    assert gray.data.ndim == 2

def test_resize(sample_image):
    resized = sample_image.resize(50, 50)
    assert resized.width == 50
    assert resized.height == 50
