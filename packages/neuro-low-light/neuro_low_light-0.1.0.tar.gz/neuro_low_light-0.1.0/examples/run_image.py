"""
Example: Enhance a low-light image

Usage: python run_image.py input.jpg output.jpg
"""

import sys
from pathlib import Path
from neuro_low_light import EnhanceModel


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_image.py <input_image> <output_image>")
        print("Example: python run_image.py dark_photo.jpg bright_photo.jpg")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Check if input exists
    if not Path(input_path).exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Initialize model
    print("Initializing model...")
    model = EnhanceModel(device="auto")
    
    # Enhance image
    print(f"Enhancing: {input_path}")
    model.enhance_image(input_path, output_path)
    
    print(f"✓ Done! Enhanced image saved to: {output_path}")


if __name__ == '__main__':
    main()
