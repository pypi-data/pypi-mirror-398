"""
High-level compression API with preset configurations.
"""

from typing import Optional
from .core import SplayPrefixCoder, bwt_transform, bwt_inverse, mtf_encode, mtf_decode


class SplayCompressor:
    """
    High-level compression API with preset configurations.
    
    Presets:
    - 'fast': Optimized for speed (splay_every=8, target_depth=2)
    - 'balanced': Balanced speed/ratio (splay_every=4, target_depth=1)
    - 'best_ratio': Best compression ratio (splay_every=1, target_depth=0)
    """
    
    PRESETS = {
        'fast': {
            'splay_every': 8,
            'depth_threshold': None,
            'target_depth': 2,
            'reset_block_bytes': None,
        },
        'balanced': {
            'splay_every': 4,
            'depth_threshold': 10,
            'target_depth': 1,
            'reset_block_bytes': 64 * 1024,
        },
        'best_ratio': {
            'splay_every': 1,
            'depth_threshold': None,
            'target_depth': 0,
            'reset_block_bytes': None,
        },
    }
    
    def __init__(self, preset: str = 'balanced', use_bwt: bool = True, use_mtf: bool = True, block_size: int = 2048, **kwargs):
        """
        Initialize compressor with preset or custom parameters.
        
        Args:
            preset: One of 'fast', 'balanced', 'best_ratio'
            use_bwt: Use BWT transform (default True). Set to False to disable.
            use_mtf: Use MTF encoding (default True). Set to False to disable.
            block_size: Block size for BWT (default 2048)
            **kwargs: Override preset parameters:
                - alphabet_size: int (default 256)
                - splay_every: int (default from preset)
                - depth_threshold: Optional[int] (default from preset)
                - target_depth: int (default from preset)
                - reset_block_bytes: Optional[int] (default from preset)
        """
        if preset not in self.PRESETS:
            raise ValueError(f"Unknown preset: {preset}. Choose from {list(self.PRESETS.keys())}")
        
        config = self.PRESETS[preset].copy()
        config.update(kwargs)
        
        self.coder = SplayPrefixCoder(**config)
        self.preset = preset
        self.config = config
        self.use_bwt = use_bwt
        self.use_mtf = use_mtf
        self.block_size = block_size
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress data using selected pipeline.
        
        Pipeline options:
        - If use_bwt=False and use_mtf=False: Splay only
        - If use_bwt=True and use_mtf=False: BWT+Splay
        - If use_bwt=True and use_mtf=True: BWT+MTF+Splay (default)
        """
        if not self.use_bwt:
            # Splay only - add pipeline header
            pipeline_header = bytearray([0x00, 0x00])  # flags: no BWT, no MTF
            compressed = self.coder.compress(data)
            return bytes(pipeline_header + compressed)
        
        # Apply BWT (blockwise)
        headers = bytearray()
        transformed = bytearray()
        i = 0
        while i < len(data):
            block = data[i:i + self.block_size]
            last, primary = bwt_transform(block)
            
            # Apply MTF if enabled
            if self.use_mtf:
                last = mtf_encode(last)
            
            headers += len(block).to_bytes(2, 'big') + primary.to_bytes(2, 'big')
            transformed += last
            i += self.block_size
        
        # Add terminator
        stream = bytes(headers + b'\x00\x00\x00\x00' + transformed)
        
        # Compress with Splay
        compressed = self.coder.compress(stream)
        
        # Add pipeline header: [use_bwt (1 byte), use_mtf (1 byte)]
        pipeline_header = bytearray([0x01 if self.use_bwt else 0x00, 0x01 if self.use_mtf else 0x00])
        return bytes(pipeline_header + compressed)
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data using selected pipeline.
        Pipeline info is read from header.
        """
        # Read pipeline header (2 bytes: use_bwt, use_mtf)
        if len(data) < 2:
            raise ValueError("Invalid compressed data: too short")
        
        use_bwt_flag = data[0]
        use_mtf_flag = data[1]
        use_bwt = use_bwt_flag != 0
        use_mtf = use_mtf_flag != 0
        
        # Decompress with Splay
        stream = self.coder.decompress(data[2:])
        
        if not use_bwt:
            # Splay only
            return stream
        
        # Parse BWT headers
        pos = 0
        blocks = []
        while True:
            bl = int.from_bytes(stream[pos:pos + 2], 'big')
            pr = int.from_bytes(stream[pos + 2:pos + 4], 'big')
            pos += 4
            if bl == 0 and pr == 0:
                break
            blocks.append((bl, pr))
        
        transformed = stream[pos:]
        out = bytearray()
        tpos = 0
        
        for bl, pr in blocks:
            block = transformed[tpos:tpos + bl]
            tpos += bl
            
            # Apply MTF decode if enabled
            if use_mtf:
                block = mtf_decode(block)
            
            # Apply BWT inverse
            out += bwt_inverse(block, pr)
        
        return bytes(out)
    
    @classmethod
    def create_custom(cls,
                      alphabet_size: int = 256,
                      splay_every: int = 1,
                      depth_threshold: Optional[int] = None,
                      target_depth: int = 0,
                      reset_block_bytes: Optional[int] = None,
                      use_bwt: bool = True,
                      use_mtf: bool = True,
                      block_size: int = 2048):
        """
        Create compressor with custom parameters.
        
        Args:
            alphabet_size: Size of alphabet (2-256)
            splay_every: Splay every k symbols (k>=1)
            depth_threshold: Splay when depth > threshold (None = disabled)
            target_depth: Target depth for semi-splay (0 = full splay)
            reset_block_bytes: Reset tree every N bytes (None = disabled)
            use_bwt: Use BWT transform (default True)
            use_mtf: Use MTF encoding (default True)
            block_size: Block size for BWT (default 2048)
            
        Returns:
            SplayCompressor instance
        """
        compressor = cls.__new__(cls)
        compressor.coder = SplayPrefixCoder(
            alphabet_size=alphabet_size,
            splay_every=splay_every,
            depth_threshold=depth_threshold,
            target_depth=target_depth,
            reset_block_bytes=reset_block_bytes,
        )
        compressor.preset = 'custom'
        compressor.config = {
            'alphabet_size': alphabet_size,
            'splay_every': splay_every,
            'depth_threshold': depth_threshold,
            'target_depth': target_depth,
            'reset_block_bytes': reset_block_bytes,
        }
        compressor.use_bwt = use_bwt
        compressor.use_mtf = use_mtf
        compressor.block_size = block_size
        return compressor

