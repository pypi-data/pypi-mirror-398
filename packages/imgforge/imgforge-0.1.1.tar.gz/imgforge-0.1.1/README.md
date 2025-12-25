# newlib: High-Performance Python Image Processing

**newlib** is a modular, production-grade image processing library designed to sit comfortably between OpenCV and modern ML frameworks. It prioritizes clean APIs, pipeline-based processing, and seamless interoperability.

## 🚀 Key Features

*   **Fluent Image API**: Wrapper around NumPy arrays with method chaining (`img.resize().to_gray()`).
*   **Pipeline Engine**: Lazy execution, serialization (YAML/JSON), and benchmarking.
*   **Machine Learning Ready**:
    *   Seamless `to_torch()` and `from_torch()` bridges.
    *   Augmentations like `ColorJitter`, `RandomRotate`.
    *   ML normalization tools.
*   **Developer Friendly**:
    *   `imgforge` CLI tool.
    *   Visual debugging (`show`, `compare`).
    *   Built-in sample data loader (`get_sample("lenna")`).
*   **Web-Ready IO**: Automatic caching of images loaded from URLs.

## 📦 Installation

```bash
pip install -e .
# Optional dependencies
pip install -e .[ml]   # For PyTorch/TensorFlow support
pip install -e .[dev]  # For testing/development
```

## ⚡ Quick Start

### Python API

```python
from newlib.core.image import Image
from newlib.core.pipeline import Pipeline
from newlib.transforms import geometric, color, filtering
from newlib.utils.data import get_sample

# 1. Load an image (auto-downloads sample)
img = get_sample("lenna")

# 2. Method Chaining
processed = img.resize(256, 256).to_gray()
processed.save("output_fast.jpg")

# 3. Pipeline API (Recommended for reproducible workflows)
pipe = Pipeline([
    geometric.Resize(224, 224),
    filtering.GaussianBlur(kernel_size=5),
    color.ToGray()
])

result = pipe(img)
print(f"Execution time: {pipe.benchmark()}")
```

### CLI Tool (`imgforge`)

**Resize an image:**
```bash
imgforge resize input.jpg 512 512 output.jpg
```

**Inspect image metadata & quality:**
```bash
imgforge inspect https://example.com/image.jpg
```

**Run a Pipeline from YAML:**
```yaml
# pipeline.yaml
pipeline:
  - name: Resize
    params:
      width: 256
      height: 256
  - name: ToGray
```
```bash
imgforge pipeline pipeline.yaml input.jpg output.jpg
```

## 🛠️ Modules Overview

| Module | Description | Key Classes/Functions |
| :--- | :--- | :--- |
| **`core`** | Foundations | `Image`, `Pipeline`, `IO`, `interop` |
| **`transforms`** | Image manipulation | `Resize`, `Rotate`, `Crop`, `ToGray`, `GaussianBlur` |
| **`vision`** | Computer Vision | `Canny`, `Sobel`, `find_contours`, `ORB`, `FAST` |
| **`analysis`** | Metrics & Stats | `inspect`, `get_stats`, `estimate_blur`, `mse`, `psnr` |
| **`utils`** | Developer Tools | `show`, `compare`, `get_sample` |

## 🤝 ML Integration

Stop fighting with NumPy/Tensor conversions.

```python
from newlib.core.interop import to_torch

img = Image.open("dataset/001.jpg")

# Automatically converts to (C, H, W) float tensor
tensor = to_torch(img.data, device="cuda") 
```

## 🧪 Running Tests

```bash
python -m pytest tests/
```

## 📄 License

MIT License. See `LICENSE` for details.
