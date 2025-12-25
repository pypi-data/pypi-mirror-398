"""
Allow running package as: python -m splaytree_compression
"""

from .cli import main

if __name__ == '__main__':
    import sys
    sys.exit(main())

