"""
Image and Video I/O utilities
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Union


def load_image(image_path: Union[str, Path]) -> np.ndarray:
    """
    Load image from file
    
    Args:
        image_path: Path to image file
        
    Returns:
        numpy array (H, W, 3) in RGB format, range [0, 255]
    """
    img = Image.open(image_path).convert('RGB')
    return np.array(img)


def save_image(image: np.ndarray, output_path: Union[str, Path]):
    """
    Save image to file
    
    Args:
        image: numpy array (H, W, 3) in RGB format, range [0, 255]
        output_path: Path to save image
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    img = Image.fromarray(image.astype(np.uint8))
    img.save(output_path)


def tensor_to_image(tensor) -> np.ndarray:
    """
    Convert PyTorch tensor to numpy image
    
    Args:
        tensor: torch.Tensor (1, 3, H, W) or (3, H, W), range [0, 1]
        
    Returns:
        numpy array (H, W, 3) in RGB format, range [0, 255]
    """
    if tensor.dim() == 4:
        tensor = tensor[0]
    
    img = tensor.cpu().numpy().transpose(1, 2, 0)
    img = np.clip(img, 0, 1) * 255
    return img.astype(np.uint8)


class VideoReader:
    """Read video frames"""
    def __init__(self, video_path: Union[str, Path]):
        self.video_path = str(video_path)
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    def __iter__(self):
        return self
    
    def __next__(self):
        ret, frame = self.cap.read()
        if not ret:
            raise StopIteration
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def __len__(self):
        return self.frame_count
    
    def close(self):
        self.cap.release()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class VideoWriter:
    """Write video frames"""
    def __init__(self, output_path: Union[str, Path], fps: float, width: int, height: int):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.output_path = str(output_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
        
        if not self.writer.isOpened():
            raise ValueError(f"Cannot create video: {output_path}")
    
    def write(self, frame: np.ndarray):
        """Write a frame (RGB format)"""
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        self.writer.write(frame_bgr)
    
    def close(self):
        self.writer.release()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
