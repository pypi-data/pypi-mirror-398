"""
Example: Enhance a low-light video

Usage: python run_video.py input.mp4 output.mp4
"""

import sys
from pathlib import Path
from neuro_low_light import EnhanceModel


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_video.py <input_video> <output_video>")
        print("Example: python run_video.py dark_video.mp4 bright_video.mp4")
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
    
    # Enhance video
    print(f"Enhancing video: {input_path}")
    print("This may take a while...")
    model.enhance_video(input_path, output_path)
    
    print(f"✓ Done! Enhanced video saved to: {output_path}")


if __name__ == '__main__':
    main()
