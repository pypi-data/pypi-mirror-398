"""
Splay Tree Compression - Lossless text compression using adaptive Splay Tree prefix coding.

This package implements an optimized Splay Tree-based compression algorithm
with various performance improvements including:
- Array-based storage for better cache locality
- Semi-splaying strategies
- Block reset mechanisms
- Configurable splay frequency
- BWT (Burrows-Wheeler Transform) support
- MTF (Move-To-Front) encoding support
- Pipeline: BWT+MTF+Splay for best compression ratio

Main classes:
    - SplayCompressor: High-level compression API with BWT+MTF pipeline
    - SplayPrefixCoder: Low-level compression engine
"""

__version__ = "2.0.0"
__author__ = "Splay Tree Compression Team"

from .core import (
    SplayPrefixCoder, BitWriter, BitReader,
    bwt_transform, bwt_inverse,
    mtf_encode, mtf_decode
)
from .compressor import SplayCompressor

__all__ = [
    "SplayPrefixCoder",
    "SplayCompressor",
    "BitWriter",
    "BitReader",
    "bwt_transform",
    "bwt_inverse",
    "mtf_encode",
    "mtf_decode",
]

