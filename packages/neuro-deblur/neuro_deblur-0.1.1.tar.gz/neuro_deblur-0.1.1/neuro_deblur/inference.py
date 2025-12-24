"""
Main inference module for image and video deblurring
"""

import torch
from pathlib import Path
from typing import Union, Optional
from tqdm import tqdm

from .model import NAFNet
from .utils import (
    load_image, save_image, tensor_to_image,
    VideoReader, VideoWriter
)
from .download import get_model_path


class DeblurModel:
    """
    NAFNet-based deblurring model for images and videos
    
    Example:
        >>> model = DeblurModel(device="cuda")
        >>> model.deblur_image("input.jpg", "output.jpg")
        >>> model.deblur_video("input.mp4", "output.mp4")
    """
    
    def __init__(self, 
                 checkpoint_path: Optional[str] = None,
                 device: str = "cuda",
                 width: int = 32):
        """
        Initialize deblurring model
        
        Args:
            checkpoint_path: Path to model checkpoint (uses bundled weights if None)
            device: 'cuda' or 'cpu' (auto-detects if cuda unavailable)
            width: Model width (must match training, default: 32)
        """
        # Setup device
        if device == "cuda" and not torch.cuda.is_available():
            print("Warning: CUDA not available, using CPU")
            device = "cpu"
        
        self.device = torch.device(device)
        
        # Initialize model
        self.model = NAFNet(
            width=width,
            middle_blk_num=12,
            enc_blk_nums=[2, 2, 4, 8],
            dec_blk_nums=[2, 2, 2, 2]
        ).to(self.device)
        
        # Load weights
        if checkpoint_path is None:
            # Auto-download from GitHub Releases
            checkpoint_path = get_model_path('best_model.pth')
        
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        # Store model info
        self.epoch = checkpoint.get('epoch', 'unknown')
        self.psnr = checkpoint.get('best_psnr', checkpoint.get('val_psnr', 'unknown'))
        
        print(f"✓ Loaded NAFNet model")
        print(f"  Device: {self.device}")
        print(f"  Epoch: {self.epoch}")
        if isinstance(self.psnr, float):
            print(f"  PSNR: {self.psnr:.2f} dB")
    
    @torch.no_grad()
    def process_tensor(self, input_tensor: torch.Tensor) -> torch.Tensor:
        """
        Process a single tensor through the model
        
        Args:
            input_tensor: [1, 3, H, W] or [3, H, W] tensor
            
        Returns:
            Deblurred tensor with same shape, clamped to [0, 1]
        """
        if input_tensor.ndim == 3:
            input_tensor = input_tensor.unsqueeze(0)
        
        input_tensor = input_tensor.to(self.device)
        
        # Forward pass
        output = self.model(input_tensor)
        
        # Clamp to valid range
        output = torch.clamp(output, 0, 1)
        
        return output
    
    def deblur_image(self, 
                     input_path: Union[str, Path],
                     save_path: Optional[Union[str, Path]] = None) -> torch.Tensor:
        """
        Deblur a single image
        
        Args:
            input_path: Path to input blurry image
            save_path: Path to save output (optional)
            
        Returns:
            Deblurred tensor [1, 3, H, W]
        """
        # Load image
        input_tensor, original_size = load_image(input_path)
        
        # Process
        output_tensor = self.process_tensor(input_tensor)
        
        # Save if requested
        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_image(output_tensor, save_path)
            print(f"✓ Saved: {save_path}")
        
        return output_tensor
    
    def deblur_video(self,
                     input_path: Union[str, Path],
                     output_path: Union[str, Path],
                     show_progress: bool = True):
        """
        Deblur a video file (frame-by-frame processing)
        
        Args:
            input_path: Path to input blurry video
            output_path: Path to save output video
            show_progress: Show progress bar
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Video not found: {input_path}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open video reader
        reader = VideoReader(input_path)
        
        print(f"Processing video: {input_path.name}")
        print(f"  Resolution: {reader.width}x{reader.height}")
        print(f"  FPS: {reader.fps:.2f}")
        print(f"  Total frames: {reader.total_frames}")
        
        # Create video writer
        writer = VideoWriter(
            output_path,
            fps=reader.fps,
            width=reader.width,
            height=reader.height
        )
        
        # Process frames
        try:
            iterator = reader
            if show_progress:
                iterator = tqdm(iterator, total=reader.total_frames, desc="Deblurring")
            
            for frame_tensor in iterator:
                # Process frame
                output_tensor = self.process_tensor(frame_tensor)
                
                # Write to output
                writer.write(output_tensor)
        
        finally:
            reader.close()
            writer.close()
        
        print(f"✓ Saved video: {output_path}")
    
    def deblur_folder(self,
                      input_folder: Union[str, Path],
                      output_folder: Union[str, Path],
                      extensions: tuple = ('.jpg', '.jpeg', '.png', '.bmp'),
                      show_progress: bool = True):
        """
        Deblur all images in a folder
        
        Args:
            input_folder: Path to folder containing blurry images
            output_folder: Path to save deblurred images
            extensions: Tuple of valid image extensions
            show_progress: Show progress bar
        """
        input_folder = Path(input_folder)
        output_folder = Path(output_folder)
        
        if not input_folder.exists():
            raise FileNotFoundError(f"Folder not found: {input_folder}")
        
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Get all images
        image_files = []
        for ext in extensions:
            image_files.extend(input_folder.glob(f"*{ext}"))
            image_files.extend(input_folder.glob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"No images found in {input_folder}")
            return
        
        print(f"Processing {len(image_files)} images from {input_folder.name}")
        
        # Process each image
        iterator = image_files
        if show_progress:
            iterator = tqdm(image_files, desc="Deblurring")
        
        for image_path in iterator:
            output_path = output_folder / image_path.name
            self.deblur_image(image_path, output_path)
        
        print(f"✓ Processed {len(image_files)} images")
        print(f"✓ Saved to: {output_folder}")
