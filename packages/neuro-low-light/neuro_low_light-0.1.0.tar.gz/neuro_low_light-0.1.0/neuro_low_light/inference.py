"""
Low-Light Image Enhancement Inference
"""

import torch
import torchvision.transforms.functional as TF
from pathlib import Path
from typing import Union, Optional
from tqdm import tqdm

from .model import ZeroDCEPP
from .utils import load_image, save_image, tensor_to_image, VideoReader, VideoWriter


class EnhanceModel:
    """Low-Light Image Enhancement Model"""
    
    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        device: str = "auto",
        num_iterations: int = 8
    ):
        """
        Initialize Enhancement Model
        
        Args:
            checkpoint_path: Path to model checkpoint. If None, uses bundled weights
            device: Device to use ('cuda', 'cpu', or 'auto' for automatic)
            num_iterations: Number of curve iterations (default: 8)
        """
        # Set device
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"Using device: {self.device}")
        
        # Load model
        self.model = ZeroDCEPP(num_iterations=num_iterations).to(self.device)
        
        # Load checkpoint
        if checkpoint_path is None:
            # Use bundled weights
            checkpoint_path = Path(__file__).parent / "weights" / "best_model.pth"
        
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        print(f"Loading model from: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        epoch = checkpoint.get('epoch', 'unknown')
        val_loss = checkpoint.get('val_loss', checkpoint.get('best_val_loss', 'unknown'))
        print(f"✓ Model loaded (Epoch: {epoch}, Val Loss: {val_loss})")
    
    @torch.no_grad()
    def enhance_image(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path]
    ):
        """
        Enhance a low-light image
        
        Args:
            input_path: Path to input image
            output_path: Path to save enhanced image
        """
        # Load image
        img = load_image(input_path)
        
        # Convert to tensor
        input_tensor = TF.to_tensor(img).unsqueeze(0).to(self.device)
        
        # Forward pass
        output, _ = self.model(input_tensor)
        output = torch.clamp(output, 0, 1)
        
        # Convert to image
        output_img = tensor_to_image(output)
        
        # Save
        save_image(output_img, output_path)
        print(f"✓ Enhanced: {input_path} -> {output_path}")
    
    @torch.no_grad()
    def enhance_video(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path]
    ):
        """
        Enhance a low-light video frame-by-frame
        
        Args:
            input_path: Path to input video
            output_path: Path to save enhanced video
        """
        print(f"Enhancing video: {input_path}")
        
        with VideoReader(input_path) as reader:
            with VideoWriter(output_path, reader.fps, reader.width, reader.height) as writer:
                for frame in tqdm(reader, total=len(reader), desc="Processing"):
                    # Convert to tensor
                    input_tensor = TF.to_tensor(frame).unsqueeze(0).to(self.device)
                    
                    # Forward pass
                    output, _ = self.model(input_tensor)
                    output = torch.clamp(output, 0, 1)
                    
                    # Convert to image
                    output_frame = tensor_to_image(output)
                    
                    # Write frame
                    writer.write(output_frame)
        
        print(f"✓ Video enhanced: {output_path}")
    
    @torch.no_grad()
    def enhance_folder(
        self,
        input_folder: Union[str, Path],
        output_folder: Union[str, Path],
        extensions: tuple = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    ):
        """
        Enhance all images in a folder
        
        Args:
            input_folder: Path to input folder
            output_folder: Path to output folder
            extensions: Tuple of image extensions to process
        """
        input_folder = Path(input_folder)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Find all images
        image_files = []
        for ext in extensions:
            image_files.extend(input_folder.glob(f"*{ext}"))
            image_files.extend(input_folder.glob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"No images found in {input_folder}")
            return
        
        print(f"Found {len(image_files)} images")
        
        # Process each image
        for img_path in tqdm(image_files, desc="Processing"):
            output_path = output_folder / img_path.name
            self.enhance_image(img_path, output_path)
        
        print(f"✓ All images enhanced to {output_folder}")


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Low-Light Image Enhancement')
    parser.add_argument('input', help='Input image or video')
    parser.add_argument('output', help='Output path')
    parser.add_argument('--device', default='auto', help='Device (cuda/cpu/auto)')
    parser.add_argument('--checkpoint', help='Path to model checkpoint')
    
    args = parser.parse_args()
    
    # Initialize model
    model = EnhanceModel(
        checkpoint_path=args.checkpoint,
        device=args.device
    )
    
    # Check if input is video
    input_path = Path(args.input)
    if input_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
        model.enhance_video(args.input, args.output)
    else:
        model.enhance_image(args.input, args.output)


if __name__ == '__main__':
    main()
