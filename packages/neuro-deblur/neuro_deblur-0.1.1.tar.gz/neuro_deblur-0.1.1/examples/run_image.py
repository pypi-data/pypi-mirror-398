"""
Example: Deblur a single image using neuro-deblur

Usage:
    python run_image.py input.jpg output.jpg
    python run_image.py input.jpg output.jpg --device cpu
"""

import argparse
from pathlib import Path
from neuro_deblur import DeblurModel


def main():
    parser = argparse.ArgumentParser(description='Deblur a single image')
    parser.add_argument('input', type=str, help='Path to input blurry image')
    parser.add_argument('output', type=str, help='Path to save deblurred image')
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
    
    # Process image
    print(f"\nProcessing: {args.input}")
    model.deblur_image(args.input, args.output)
    
    print(f"\n✅ Done! Deblurred image saved to: {args.output}")


if __name__ == "__main__":
    main()
