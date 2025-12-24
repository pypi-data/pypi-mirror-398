# neuro-deblur 🚀

Professional image and video deblurring using **NAFNet** (Nonlinear Activation Free Network).

A production-ready Python package for motion deblurring with CUDA acceleration support. Perfect for enhancing blurry photos and videos with state-of-the-art deep learning.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/neuro-deblur.svg)](https://badge.fury.io/py/neuro-deblur)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Features

- ✅ **Image Deblurring** - Restore sharp details from blurry images
- ✅ **Video Deblurring** - Process videos frame-by-frame
- ✅ **CUDA Acceleration** - GPU support for fast processing
- ✅ **CPU Fallback** - Works on systems without GPU
- ✅ **Simple API** - 3 lines of code to deblur
- ✅ **Pre-trained Model** - Ready to use out of the box
- ✅ **Production Ready** - Clean, tested, and documented

---

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install neuro-deblur
```

**Note:** Model weights (~334 MB) will be downloaded automatically on first use.

### From Source

```bash
git clone https://github.com/Parshva2605/neuro-deblur.git
cd neuro-deblur
pip install -e .
```

### Requirements

- Python >= 3.9
- PyTorch >= 2.0.0
- CUDA (optional, for GPU acceleration)

### First Use - Automatic Model Download

On first use, the model weights will be downloaded automatically:

```python
from neuro_deblur import DeblurModel

# First time - downloads model (~334 MB, one-time only)
model = DeblurModel(device="cuda")
# Downloading model weights from GitHub...
# best_model.pth: 100% |████████| 334MB/334MB [30s]
# ✓ Model downloaded successfully!

# Later uses - instant (uses cached model)
model = DeblurModel(device="cuda")
# ✓ Using cached model
```

**Cache Location:**
- Windows: `C:\Users\YourName\AppData\Local\neuro_deblur\weights\`
- Linux/Mac: `~/.cache/neuro_deblur/weights/`

---

## 🚀 Quick Start

### Deblur an Image

```python
from neuro_deblur import DeblurModel

# Initialize model (auto-detects CUDA)
model = DeblurModel(device="cuda")

# Deblur image
model.deblur_image("blurry_photo.jpg", "sharp_photo.jpg")
```

### Deblur a Video

```python
from neuro_deblur import DeblurModel

# Initialize model
model = DeblurModel(device="cuda")

# Deblur video (with progress bar)
model.deblur_video("blurry_video.mp4", "sharp_video.mp4")
```

### Process Multiple Images

```python
from neuro_deblur import DeblurModel

# Initialize model
model = DeblurModel(device="cuda")

# Deblur all images in a folder
model.deblur_folder("input_folder/", "output_folder/")
```

---

## 💡 Usage Examples

### Command Line (Using Examples)

#### Image Processing
```bash
cd examples
python run_image.py input.jpg output.jpg
python run_image.py input.jpg output.jpg --device cpu
```

#### Video Processing
```bash
cd examples
python run_video.py input.mp4 output.mp4
python run_video.py input.mp4 output.mp4 --device cuda
```

### Python API

#### Basic Usage
```python
from neuro_deblur import DeblurModel

# Auto-detect device (prefers CUDA)
model = DeblurModel()

# Or specify device explicitly
model = DeblurModel(device="cuda")  # Use GPU
model = DeblurModel(device="cpu")   # Use CPU

# Deblur image
output = model.deblur_image("input.jpg", "output.jpg")
```

#### Advanced Usage
```python
from neuro_deblur import DeblurModel
from pathlib import Path

# Use custom checkpoint
model = DeblurModel(
    checkpoint_path="path/to/custom_model.pth",
    device="cuda"
)

# Process without saving (get tensor)
output_tensor = model.deblur_image("input.jpg")

# Process multiple videos
video_files = Path("videos/").glob("*.mp4")
for video in video_files:
    output = f"deblurred/{video.name}"
    model.deblur_video(video, output)
```

#### Direct Tensor Processing
```python
import torch
from neuro_deblur import DeblurModel

model = DeblurModel(device="cuda")

# Process tensor directly
input_tensor = torch.rand(1, 3, 256, 256)  # [B, C, H, W]
output_tensor = model.process_tensor(input_tensor)
```

---

## 🖥️ GPU Support

### Automatic CUDA Detection

The package automatically detects and uses CUDA if available:

```python
# Auto-detects GPU
model = DeblurModel()  # Uses CUDA if available, else CPU

# Force CPU
model = DeblurModel(device="cpu")

# Force GPU (raises error if unavailable)
model = DeblurModel(device="cuda")
```

### Performance Benchmarks

Processing a **1920×1080** video on **RTX 3070**:

| Device | FPS | Speed |
|--------|-----|-------|
| **CUDA** | ~3-5 FPS | 20-30x faster |
| **CPU** | ~0.1-0.2 FPS | Baseline |

**Recommendation**: Use GPU for videos, CPU works fine for images.

---

## 📊 Model Details

### NAFNet Architecture

- **Paper**: [Simple Baselines for Image Restoration](https://arxiv.org/abs/2204.04676)
- **Architecture**: NAFNet (Nonlinear Activation Free Network)
- **Parameters**: ~29M parameters
- **Training**: GoPro dataset (motion deblurring)
- **Performance**: 30.33 dB PSNR on validation set

### Model Configuration

```python
NAFNet(
    width=32,
    middle_blk_num=12,
    enc_blk_nums=[2, 2, 4, 8],
    dec_blk_nums=[2, 2, 2, 2]
)
```

---

## 📁 Project Structure

```
neuro_deblur/
├── neuro_deblur/
│   ├── __init__.py       # Public API
│   ├── model.py          # NAFNet architecture
│   ├── inference.py      # DeblurModel class
│   ├── utils.py          # Image/video utilities
│   └── weights/
│       └── best_model.pth  # Pre-trained weights
├── examples/
│   ├── run_image.py      # Image deblurring example
│   └── run_video.py      # Video deblurring example
├── setup.py              # Package setup
├── pyproject.toml        # Build configuration
├── requirements.txt      # Dependencies
├── MANIFEST.in           # Include data files
├── README.md             # This file
└── LICENSE               # MIT License
```

---

## 🛠️ Development

### Install in Development Mode

```bash
git clone https://github.com/yourusername/neuro-deblur.git
cd neuro-deblur
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black neuro_deblur/
flake8 neuro_deblur/
```

---

## 📝 API Reference

### `DeblurModel`

Main class for deblurring operations.

#### Constructor

```python
DeblurModel(checkpoint_path=None, device="cuda", width=32)
```

**Parameters**:
- `checkpoint_path` (str, optional): Path to custom checkpoint. Uses bundled weights if None.
- `device` (str): Device to use ("cuda" or "cpu"). Auto-detects if CUDA unavailable.
- `width` (int): Model width (must match training, default: 32).

#### Methods

##### `deblur_image(input_path, save_path=None)`

Deblur a single image.

**Parameters**:
- `input_path` (str): Path to blurry image
- `save_path` (str, optional): Path to save output

**Returns**: `torch.Tensor` - Deblurred image tensor [1, 3, H, W]

##### `deblur_video(input_path, output_path, show_progress=True)`

Deblur a video file.

**Parameters**:
- `input_path` (str): Path to blurry video
- `output_path` (str): Path to save output
- `show_progress` (bool): Show progress bar

##### `deblur_folder(input_folder, output_folder, extensions=(...), show_progress=True)`

Deblur all images in a folder.

**Parameters**:
- `input_folder` (str): Input folder path
- `output_folder` (str): Output folder path
- `extensions` (tuple): Valid image extensions
- `show_progress` (bool): Show progress bar

##### `process_tensor(input_tensor)`

Process a tensor directly.

**Parameters**:
- `input_tensor` (torch.Tensor): Input tensor [1, 3, H, W] or [3, H, W]

**Returns**: `torch.Tensor` - Deblurred tensor, clamped to [0, 1]

---

## 🎯 Use Cases

- **Photography**: Restore blurry photos (motion blur, camera shake)
- **Video Enhancement**: Stabilize and sharpen video footage
- **Security Footage**: Enhance low-quality surveillance videos
- **Medical Imaging**: Improve clarity of medical scans
- **Autonomous Vehicles**: Preprocess camera feeds
- **Sports Analytics**: Enhance fast-motion sports footage

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository at [github.com/Parshva2605/neuro-deblur](https://github.com/Parshva2605/neuro-deblur)
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **NAFNet**: [Simple Baselines for Image Restoration](https://arxiv.org/abs/2204.04676)
- **GoPro Dataset**: Motion deblurring benchmark dataset
- **PyTorch**: Deep learning framework

---

## 📧 Contact

**Parshva Shah** - shahparshva2005@gmail.com

Project Link: [https://github.com/Parshva2605/neuro-deblur](https://github.com/Parshva2605/neuro-deblur)

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Made with ❤️ for the computer vision community**
