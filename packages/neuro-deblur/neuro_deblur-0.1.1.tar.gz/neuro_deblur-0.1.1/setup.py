"""
Setup script for neuro-deblur package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="neuro-deblur",
    version="0.1.1",
    author="Parshva Shah",
    author_email="shahparshva2005@gmail.com",
    description="Professional image and video deblurring using NAFNet",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Parshva2605/neuro-deblur",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
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
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    include_package_data=True,
    package_data={
        "neuro_deblur": ["weights/*.pth"],
    },
    entry_points={
        "console_scripts": [
            "neuro-deblur=neuro_deblur.inference:main",
        ],
    },
    keywords="deblur, image-processing, video-processing, nafnet, deep-learning, computer-vision",
    project_urls={
        "Bug Reports": "https://github.com/Parshva2605/neuro-deblur/issues",
        "Source": "https://github.com/Parshva2605/neuro-deblur",
    },
)
