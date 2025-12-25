"""
Setup script for Splay Tree Compression package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="splaytree-compression",
    version="2.0.0",
    author="Splay Tree Compression Team",
    author_email="",
    description="Lossless text compression using adaptive Splay Tree prefix coding",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/splaytree-compression",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: System :: Archiving :: Compression",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "splay-compress=splaytree_compression.cli:main",
        ],
    },
    keywords="compression, splay-tree, lossless, adaptive, prefix-coding",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/splaytree-compression/issues",
        "Source": "https://github.com/yourusername/splaytree-compression",
    },
)

