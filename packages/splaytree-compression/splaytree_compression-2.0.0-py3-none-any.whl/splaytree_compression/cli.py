"""
Command-line interface for Splay Tree compression.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .compressor import SplayCompressor


def compress_file(input_path: Path, output_path: Optional[Path], preset: str, use_bwt: bool = True, use_mtf: bool = True, block_size: int = 2048, **kwargs):
    """Compress a file."""
    try:
        with open(input_path, 'rb') as f:
            data = f.read()
    except IOError as e:
        print(f"Error reading {input_path}: {e}", file=sys.stderr)
        return 1
    
    try:
        compressor = SplayCompressor(preset=preset, use_bwt=use_bwt, use_mtf=use_mtf, block_size=block_size, **kwargs)
        compressed = compressor.compress(data)
    except Exception as e:
        print(f"Compression error: {e}", file=sys.stderr)
        return 1
    
    if output_path is None:
        output_path = input_path.with_suffix(input_path.suffix + '.splay')
    
    try:
        with open(output_path, 'wb') as f:
            f.write(compressed)
    except IOError as e:
        print(f"Error writing {output_path}: {e}", file=sys.stderr)
        return 1
    
    original_size = len(data)
    compressed_size = len(compressed)
    ratio = original_size / compressed_size if compressed_size > 0 else 0
    
    print(f"Compressed: {input_path} -> {output_path}")
    print(f"  Original size: {original_size:,} bytes")
    print(f"  Compressed size: {compressed_size:,} bytes")
    print(f"  Compression ratio: {ratio:.3f}x")
    
    return 0


def decompress_file(input_path: Path, output_path: Optional[Path]):
    """Decompress a file."""
    try:
        with open(input_path, 'rb') as f:
            compressed = f.read()
    except IOError as e:
        print(f"Error reading {input_path}: {e}", file=sys.stderr)
        return 1
    
    try:
        # Decompress doesn't need preset or pipeline options, all info is in header
        compressor = SplayCompressor(preset='balanced', use_bwt=True, use_mtf=True)  # Dummy, won't be used
        data = compressor.decompress(compressed)
    except Exception as e:
        print(f"Decompression error: {e}", file=sys.stderr)
        return 1
    
    if output_path is None:
        if input_path.suffix == '.splay':
            output_path = input_path.with_suffix('')
        else:
            output_path = input_path.with_suffix(input_path.suffix + '.decompressed')
    
    try:
        with open(output_path, 'wb') as f:
            f.write(data)
    except IOError as e:
        print(f"Error writing {output_path}: {e}", file=sys.stderr)
        return 1
    
    print(f"Decompressed: {input_path} -> {output_path}")
    print(f"  Size: {len(data):,} bytes")
    
    return 0


def main():
    """Main CLI entry point."""
    # Check if called as splay-compress or splay-decompress
    import sys
    prog_name = Path(sys.argv[0]).stem if sys.argv else 'splay-compress'
    
    if 'decompress' in prog_name:
        # Called as splay-decompress
        parser = argparse.ArgumentParser(
            description='Decompress a file compressed with Splay Tree compression',
            prog='splay-decompress'
        )
        parser.add_argument('input', type=Path, help='Input file to decompress')
        parser.add_argument('-o', '--output', type=Path, help='Output file (default: input without .splay)')
        args = parser.parse_args()
        return decompress_file(args.input, args.output)
    
    else:
        # Called as splay-compress or with subcommand
        parser = argparse.ArgumentParser(
            description='Splay Tree Compression - Lossless compression using adaptive Splay Tree',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Compress a file (default: BWT+MTF+Splay)
  splay-compress compress input.txt -o output.splay
  
  # Compress with preset
  splay-compress compress input.txt --preset fast
  
  # Compress without BWT/MTF (Splay only)
  splay-compress compress input.txt --use-bwt -1 --use-mtf -1
  
  # Compress with BWT only (no MTF)
  splay-compress compress input.txt --use-mtf -1
  
  # Decompress
  splay-compress decompress output.splay -o input.txt
  
  # Custom parameters
  splay-compress compress input.txt --splay-every 8 --target-depth 2
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Command to execute', required=True)
        
        # Compress command
        compress_parser = subparsers.add_parser('compress', help='Compress a file')
        compress_parser.add_argument('input', type=Path, help='Input file to compress')
        compress_parser.add_argument('-o', '--output', type=Path, help='Output file (default: input.splay)')
        compress_parser.add_argument('-p', '--preset', choices=['fast', 'balanced', 'best_ratio'],
                                    default='balanced', help='Compression preset (default: balanced)')
        compress_parser.add_argument('--use-bwt', type=int, default=1,
                                    help='Use BWT transform (1=yes, -1=no, default=1)')
        compress_parser.add_argument('--use-mtf', type=int, default=1,
                                    help='Use MTF encoding (1=yes, -1=no, default=1)')
        compress_parser.add_argument('--block-size', type=int, default=2048,
                                    help='Block size for BWT (default: 2048)')
        compress_parser.add_argument('--splay-every', type=int, help='Splay every k symbols')
        compress_parser.add_argument('--depth-threshold', type=int, help='Splay when depth > threshold')
        compress_parser.add_argument('--target-depth', type=int, help='Target depth for semi-splay')
        compress_parser.add_argument('--reset-block-bytes', type=int, help='Reset tree every N bytes')
        
        # Decompress command
        decompress_parser = subparsers.add_parser('decompress', help='Decompress a file')
        decompress_parser.add_argument('input', type=Path, help='Input file to decompress')
        decompress_parser.add_argument('-o', '--output', type=Path, help='Output file (default: input without .splay)')
        
        args = parser.parse_args()
        
        if args.command == 'compress':
            kwargs = {}
            if args.splay_every is not None:
                kwargs['splay_every'] = args.splay_every
            if args.depth_threshold is not None:
                kwargs['depth_threshold'] = args.depth_threshold
            if args.target_depth is not None:
                kwargs['target_depth'] = args.target_depth
            if args.reset_block_bytes is not None:
                kwargs['reset_block_bytes'] = args.reset_block_bytes
            
            # Convert --use-bwt and --use-mtf: -1 means False, otherwise True
            use_bwt = args.use_bwt != -1
            use_mtf = args.use_mtf != -1
            
            return compress_file(args.input, args.output, args.preset, 
                                use_bwt=use_bwt, use_mtf=use_mtf, 
                                block_size=args.block_size, **kwargs)
        
        elif args.command == 'decompress':
            return decompress_file(args.input, args.output)
        
        else:
            parser.print_help()
            return 1


if __name__ == '__main__':
    sys.exit(main())

