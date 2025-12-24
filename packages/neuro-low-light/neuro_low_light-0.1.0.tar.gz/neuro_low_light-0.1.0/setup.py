from setuptools import setup, find_packages
from pathlib import Path

# Read README
long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="neuro-low-light",
    version="0.1.0",
    author="Parshva Shah",
    author_email="shahparshva2005@gmail.com",
    description="Professional low-light image enhancement using Zero-DCE++",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Parshva2605/neuro-low-light",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.9",
    install_requires=[
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "opencv-python>=4.5.0",
        "numpy>=1.21.0",
        "pillow>=9.0.0",
        "tqdm>=4.60.0",
    ],
    entry_points={
        'console_scripts': [
            'neuro-low-light=neuro_low_light.inference:main',
        ],
    },
    include_package_data=True,
    package_data={
        'neuro_low_light': ['weights/*.pth'],
    },
)
