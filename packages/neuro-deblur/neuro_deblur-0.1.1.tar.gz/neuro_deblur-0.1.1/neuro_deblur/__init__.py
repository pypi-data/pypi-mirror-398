"""
neuro-deblur: Professional image and video deblurring using NAFNet

A production-ready Python package for motion deblurring using the NAFNet architecture.
Supports both images and videos with CUDA acceleration.

Example:
    >>> from neuro_deblur import DeblurModel
    >>> model = DeblurModel(device="cuda")
    >>> model.deblur_image("blurry.jpg", "sharp.jpg")
    >>> model.deblur_video("blurry.mp4", "sharp.mp4")
"""

from .inference import DeblurModel
from .model import NAFNet
from .utils import load_image, save_image, tensor_to_image
from .download import get_model_path, get_cache_dir

__version__ = "0.1.1"
__author__ = "Parshva Shah"
__all__ = ["DeblurModel", "NAFNet", "load_image", "save_image", "tensor_to_image", "get_model_path", "get_cache_dir"]
