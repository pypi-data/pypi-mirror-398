"""
Example: Deblur a video file using neuro-deblur

Usage:
    python run_video.py input.mp4 output.mp4
    python run_video.py input.mp4 output.mp4 --device cpu
"""

import argparse
from pathlib import Path
from neuro_deblur import DeblurModel


def main():
    parser = argparse.ArgumentParser(description='Deblur a video file')
    parser.add_argument('input', type=str, help='Path to input blurry video')
    parser.add_argument('output', type=str, help='Path to save deblurred video')
    parser.add_argument('--device', type=str, default='cuda', 
                        choices=['cuda', 'cpu'],
                        help='Device to use (cuda or cpu)')
    parser.add_argument('--checkpoint', type=str, default=None,
                        help='Path to custom checkpoint (optional)')
    
    args = parser.parse_args()
    
    # Check input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return
    
    # Initialize model
    print("Loading deblurring model...")
    model = DeblurModel(
        checkpoint_path=args.checkpoint,
        device=args.device
    )
    
    # Process video
    print(f"\nProcessing video: {args.input}")
    model.deblur_video(args.input, args.output, show_progress=True)
    
    print(f"\n✅ Done! Deblurred video saved to: {args.output}")


if __name__ == "__main__":
    main()
