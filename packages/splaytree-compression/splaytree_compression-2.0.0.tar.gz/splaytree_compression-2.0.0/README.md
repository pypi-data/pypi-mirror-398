# Splay Tree Compression

Lossless text compression using adaptive Splay Tree prefix coding.

This package implements an optimized Splay Tree-based compression algorithm with various performance improvements including:
- Array-based storage for better cache locality
- Semi-splaying strategies to reduce rotation overhead
- Block reset mechanisms for multi-domain data
- Configurable splay frequency

## Installation

### From local source

```bash
# Navigate to package directory
cd package

# Install in development mode (editable)
pip install -e .

# Or install normally
pip install .
```

### From PyPI (if published)

```bash
pip install splaytree-compression
```

## Quick Start

### Command Line Interface

```bash
# Compress a file
splay-compress compress input.txt -o output.splay

# Compress with preset
splay-compress compress input.txt --preset fast

# Decompress
splay-compress decompress output.splay -o input.txt
```

### Python API

```python
from splaytree_compression import SplayCompressor

# Using preset
compressor = SplayCompressor(preset='balanced')
compressed = compressor.compress(data)
decompressed = compressor.decompress(compressed)

# Custom parameters
compressor = SplayCompressor.create_custom(
    splay_every=4,
    depth_threshold=10,
    target_depth=1,
    reset_block_bytes=64*1024
)
compressed = compressor.compress(data)
```

### Low-level API

```python
from splaytree_compression import SplayPrefixCoder

# Create coder
coder = SplayPrefixCoder(
    alphabet_size=256,
    splay_every=4,
    depth_threshold=10,
    target_depth=1,
    reset_block_bytes=64*1024
)

# Compress
compressed = coder.compress(data)

# Decompress (parameters are stored in header)
decompressed = SplayPrefixCoder.decompress(compressed)
```

## Compression Presets

- **`fast`**: Optimized for speed
  - `splay_every=8`, `target_depth=2`
  - Best for large files where speed matters
  
- **`balanced`**: Balanced speed/ratio (default)
  - `splay_every=4`, `depth_threshold=10`, `target_depth=1`, `reset_block_bytes=64KB`
  - Good general-purpose setting
  
- **`best_ratio`**: Best compression ratio
  - `splay_every=1`, `target_depth=0` (full splay)
  - Best compression but slower

## Parameters

- **`alphabet_size`** (int, default 256): Size of alphabet (2-256)
- **`splay_every`** (int, default 1): Splay every k symbols (k>=1)
- **`depth_threshold`** (int, optional): Splay when depth > threshold
- **`target_depth`** (int, default 0): Target depth for semi-splay (0 = full splay to root)
- **`reset_block_bytes`** (int, optional): Reset tree every N bytes

## Performance

Based on benchmarks, the optimized version achieves:
- **~3.75x speedup** compared to baseline
- Compression ratio: ~0.75-0.78 (depending on data)
- Suitable for educational/research purposes

Note: This algorithm is not intended to compete with industrial compression algorithms like zlib or LZMA, but rather serves as a research tool to understand adaptive prefix coding with Splay Trees.

## Documentation

- `INSTALL.md`: Detailed installation instructions
- `PACKAGE_USAGE.md`: Usage guide with examples
- `PUBLISH.md`: Guide for publishing to PyPI

## Examples

### Compress with custom parameters

```bash
splay-compress compress input.txt \
    --splay-every 8 \
    --target-depth 2 \
    -o output.splay
```

### Batch compression

```python
from pathlib import Path
from splaytree_compression import SplayCompressor

compressor = SplayCompressor(preset='balanced')

for file in Path('data').glob('*.txt'):
    with open(file, 'rb') as f:
        data = f.read()
    
    compressed = compressor.compress(data)
    
    with open(file.with_suffix('.splay'), 'wb') as f:
        f.write(compressed)
    
    print(f"Compressed {file}: {len(data)} -> {len(compressed)} bytes")
```

## Development

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
python test_package.py

# Format code
black splaytree_compression/

# Type checking
mypy splaytree_compression/
```

## License

MIT License

## References

Based on research paper: "Advanced Lossless Text Compression Algorithm Based on Splay Tree Adaptive Methods"

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.