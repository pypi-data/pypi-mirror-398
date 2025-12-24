"""
Utility functions for image and video processing
"""

import cv2
import numpy as np
from PIL import Image
import torch
import torchvision.transforms.functional as TF
from pathlib import Path
from typing import Union, Optional, Tuple


def load_image(image_path: Union[str, Path]) -> Tuple[torch.Tensor, Tuple[int, int]]:
    """
    Load image from file and convert to tensor
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (tensor, original_size)
        - tensor: [1, 3, H, W] normalized to [0, 1]
        - original_size: (width, height) tuple
    """
    img = Image.open(image_path).convert('RGB')
    original_size = img.size  # (W, H)
    
    # Convert to tensor [1, 3, H, W]
    tensor = TF.to_tensor(img).unsqueeze(0)
    
    return tensor, original_size


def tensor_to_image(tensor: torch.Tensor) -> Image.Image:
    """
    Convert tensor to PIL Image
    
    Args:
        tensor: [1, 3, H, W] or [3, H, W] tensor in range [0, 1]
        
    Returns:
        PIL Image
    """
    if tensor.ndim == 4:
        tensor = tensor.squeeze(0)
    
    # Ensure values are in [0, 1]
    tensor = torch.clamp(tensor, 0, 1)
    
    # Convert to numpy and transpose to [H, W, 3]
    arr = tensor.cpu().numpy().transpose(1, 2, 0)
    arr = (arr * 255).astype(np.uint8)
    
    return Image.fromarray(arr)


def save_image(tensor: torch.Tensor, save_path: Union[str, Path]):
    """
    Save tensor as image file
    
    Args:
        tensor: [1, 3, H, W] or [3, H, W] tensor
        save_path: Output file path
    """
    img = tensor_to_image(tensor)
    img.save(save_path)


class VideoReader:
    """Simple video reader using OpenCV"""
    
    def __init__(self, video_path: Union[str, Path]):
        self.video_path = str(video_path)
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    def __iter__(self):
        return self
    
    def __next__(self) -> torch.Tensor:
        ret, frame = self.cap.read()
        if not ret:
            raise StopIteration
        
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to tensor [1, 3, H, W]
        tensor = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0
        tensor = tensor.unsqueeze(0)
        
        return tensor
    
    def close(self):
        self.cap.release()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class VideoWriter:
    """Simple video writer using OpenCV"""
    
    def __init__(self, output_path: Union[str, Path], fps: float, 
                 width: int, height: int, codec: str = 'mp4v'):
        self.output_path = str(output_path)
        self.fps = fps
        self.width = width
        self.height = height
        
        fourcc = cv2.VideoWriter_fourcc(*codec)
        self.writer = cv2.VideoWriter(
            self.output_path, fourcc, fps, (width, height)
        )
        
        if not self.writer.isOpened():
            raise ValueError(f"Cannot create video writer: {output_path}")
    
    def write(self, tensor: torch.Tensor):
        """
        Write tensor as video frame
        
        Args:
            tensor: [1, 3, H, W] or [3, H, W] tensor
        """
        if tensor.ndim == 4:
            tensor = tensor.squeeze(0)
        
        # Clamp to [0, 1]
        tensor = torch.clamp(tensor, 0, 1)
        
        # Convert to numpy [H, W, 3]
        frame = tensor.cpu().numpy().transpose(1, 2, 0)
        frame = (frame * 255).astype(np.uint8)
        
        # Convert RGB to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        self.writer.write(frame)
    
    def close(self):
        self.writer.release()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
