"""
Core compression engine: Bit I/O and Splay Tree prefix coder.
"""

from typing import List, Dict, Optional, Tuple


class BitWriter:
    """Fast bit-level writer with byte-flush mechanism."""
    __slots__ = ("buf", "cur", "nbits")

    def __init__(self):
        self.buf = bytearray()
        self.cur = 0   # left-aligned bit accumulator (MSB-first)
        self.nbits = 0  # number of valid bits in cur (0..7)

    def write_bits(self, x: int, n: int):
        """Write n bits of x (MSB-first)."""
        if n <= 0:
            return
        while n:
            take = 8 - self.nbits
            if take > n:
                take = n
            shift = n - take
            chunk = (x >> shift) & ((1 << take) - 1)
            self.cur = (self.cur << take) | chunk
            self.nbits += take
            n -= take
            if self.nbits == 8:
                # 0xFF là số hex = 255 (nhị phân: 8 bit 1), dùng để giữ lại đúng 8 bit thấp nhất của self.cur.
                # Khi flush 1 byte vào buf, self.cur có thể chứa nhiều bit hơn 8 bit do tích lũy;
                # Việc & 0xFF sẽ loại bỏ các bit ngoài byte thấp nhất, chỉ lấy phần 8 bit ít ý nghĩa nhất.
                self.buf.append(self.cur & 0xFF)
                self.cur = 0
                self.nbits = 0

    def write_u8(self, x: int):
        """Write 8-bit unsigned integer."""
        self.write_bits(x & 0xFF, 8)

    def write_u16(self, x: int):
        """Write 16-bit unsigned integer."""
        self.write_bits(x & 0xFFFF, 16)

    def write_u32(self, x: int):
        """Write 32-bit unsigned integer."""
        self.write_bits(x & 0xFFFFFFFF, 32)

    def write_bit(self, b: int):
        """Write single bit."""
        self.write_bits(b & 1, 1)

    def get_bytes(self) -> bytes:
        """Get all written bytes, flushing any remaining bits."""
        if self.nbits:
            self.buf.append((self.cur << (8 - self.nbits)) & 0xFF)
            self.cur = 0
            self.nbits = 0
        return bytes(self.buf)


class BitReader:
    """Fast bit-level reader."""
    __slots__ = ("data", "i", "cur", "nbits")

    def __init__(self, data: bytes):
        self.data = data
        self.i = 0
        self.cur = 0
        self.nbits = 0

    def read_bit(self) -> int:
        """Read single bit."""
        if self.nbits == 0:
            if self.i >= len(self.data):
                raise EOFError("End of data")
            self.cur = self.data[self.i]
            self.i += 1
            self.nbits = 8
        self.nbits -= 1
        return (self.cur >> self.nbits) & 1

    def read_bits(self, n: int) -> int:
        """Read n bits and return as integer."""
        x = 0
        for _ in range(n):
            x = (x << 1) | self.read_bit()
        return x

    def read_u8(self) -> int:
        """Read 8-bit unsigned integer."""
        return self.read_bits(8)

    def read_u16(self) -> int:
        """Read 16-bit unsigned integer."""
        return self.read_bits(16)

    def read_u32(self) -> int:
        """Read 32-bit unsigned integer."""
        return self.read_bits(32)


class SplayPrefixCoder:
    """
    Splay Tree-based adaptive prefix coder (Array-based implementation).

    Features:
    - Semi-splaying: bring node to "near root" (target_depth >= 0)
      target_depth=0 -> full splay to root
      target_depth=1 -> stop when node is 1 edge under root, etc.
    - Block reset: reset tree every N bytes (reset_block_bytes)
    - Optional: splay_every, depth_threshold

    Stream header includes parameters so decompress doesn't rely on caller settings.
    """
    MAGIC = b"SP52"

    def __init__(self,
                 alphabet_size: int = 256,
                 splay_every: int = 1,
                 depth_threshold: Optional[int] = None,
                 target_depth: int = 0,
                 reset_block_bytes: Optional[int] = None):
        """
        Initialize Splay Tree prefix coder.

        Args:
            alphabet_size: Size of alphabet (2-256, default 256 for bytes)
            splay_every: Splay every k symbols (k>=1, default 1 = always splay)
            depth_threshold: Splay when depth > threshold (None = disabled)
            target_depth: Target depth for semi-splay (0 = full splay to root)
            reset_block_bytes: Reset tree every N bytes (None = disabled)
        """
        if alphabet_size < 2 or alphabet_size > 256:
            raise ValueError(
                "alphabet_size must be in [2..256] for byte streams.")
        if splay_every < 1:
            raise ValueError("splay_every must be >= 1")
        if target_depth < 0:
            raise ValueError("target_depth must be >= 0")

        self.alphabet_size = alphabet_size
        self.splay_every = splay_every
        self.depth_threshold = depth_threshold
        self.target_depth = target_depth
        self.reset_block_bytes = reset_block_bytes if (
            reset_block_bytes and reset_block_bytes > 0) else None

        self.left: List[int] = []
        self.right: List[int] = []
        self.parent: List[int] = []
        self.sym: List[int] = []  # self.sym[i] = symbol value (for leaf nodes), -1 for internal nodes
        self.sym2leaf: Dict[int, int] = {}  # self.sym2leaf[sym] = node index of the leaf node holding symbol 'sym'

        self.root = self._build_complete_tree()
        self._snapshot = self._take_snapshot()

    # ---- tree build / reset ----
    def _new_node(self, left=-1, right=-1, parent=-1, sym=-1) -> int:
        """Create new node and return its index."""
        i = len(self.left)
        self.left.append(left)
        self.right.append(right)
        self.parent.append(parent)
        self.sym.append(sym)
        return i

    def _build_complete_tree(self) -> int:
        """Build complete binary tree with alphabet_size leaves."""
        nleaf = self.alphabet_size
        pow2 = 1
        while pow2 < nleaf:
            pow2 <<= 1
        total_leaves = pow2

        leaves = []
        for s in range(total_leaves):
            sym = s if s < nleaf else -1
            nid = self._new_node(sym=sym)
            if sym >= 0:
                self.sym2leaf[sym] = nid
            leaves.append(nid)

        level = leaves
        while len(level) > 1:
            nxt = []
            for i in range(0, len(level), 2):
                l = level[i]
                r = level[i + 1]
                nid = self._new_node(left=l, right=r, sym=-1)
                self.parent[l] = nid
                self.parent[r] = nid
                nxt.append(nid)
            level = nxt
        return level[0]

    def _take_snapshot(self) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], int]:
        """Take snapshot of tree state for reset."""
        return (tuple(self.left), tuple(self.right), tuple(self.parent), tuple(self.sym), self.root)

    def _reset_tree(self):
        """Reset tree to initial state."""
        left, right, parent, sym, root = self._snapshot
        self.left[:] = left
        self.right[:] = right
        self.parent[:] = parent
        self.sym[:] = sym
        self.root = root

    # ---- rotations / semi-splay ----
    def _rotate_up(self, x: int):
        """Rotate node x up one level."""
        p = self.parent[x]
        if p == -1:
            self.root = x
            return
        g = self.parent[p]

        if self.left[p] == x:
            b = self.right[x]
            self.right[x] = p
            self.parent[p] = x
            self.left[p] = b
            if b != -1:
                self.parent[b] = p
        else:
            b = self.left[x]
            self.left[x] = p
            self.parent[p] = x
            self.right[p] = b
            if b != -1:
                self.parent[b] = p

        self.parent[x] = g
        if g == -1:
            self.root = x
        else:
            if self.left[g] == p:
                self.left[g] = x
            else:
                self.right[g] = x

    def _depth_of_node(self, x: int) -> int:
        """Calculate depth of node x from root."""
        d = 0
        while x != self.root:
            x = self.parent[x]
            d += 1
        return d

    def _splay_to_depth(self, x: int, target_depth: int):
        """Bring x upwards until its depth == target_depth (or it becomes root)."""
        if x == -1:
            return
        if target_depth <= 0:
            while self.parent[x] != -1:
                self._rotate_up(x)
            return

        d = self._depth_of_node(x)
        while d > target_depth and self.parent[x] != -1:
            self._rotate_up(x)
            d -= 1

    # ---- path encoding (no list allocation) ----
    def _encode_path_bits_root_to_leaf(self, leaf: int):
        """Encode path from root to leaf as integer (no list allocation)."""
        rev = 0
        n = 0
        x = leaf
        root = self.root
        left = self.left
        parent = self.parent

        while x != root:
            p = parent[x]
            bit = 0 if left[p] == x else 1
            rev = (rev << 1) | bit
            n += 1
            x = p

        code = 0
        for _ in range(n):
            code = (code << 1) | (rev & 1)
            rev >>= 1
        return code, n  # n is depth of leaf

    def _should_splay(self, idx1_based: int, depth: int) -> bool:
        """Determine if we should splay based on strategies."""
        if (idx1_based % self.splay_every) == 0:
            return True
        if self.depth_threshold is not None and depth > self.depth_threshold:
            return True
        return False

    def _maybe_reset(self, i0_based: int):
        """Reset tree at block boundaries if enabled."""
        if self.reset_block_bytes is None:
            return
        if i0_based > 0 and (i0_based % self.reset_block_bytes) == 0:
            self._reset_tree()

    # ---- header ----
    @staticmethod
    def _encode_dt(depth_threshold: Optional[int]) -> int:
        """Encode depth_threshold (None -> 0xFFFF)."""
        return 0xFFFF if depth_threshold is None else max(0, min(0xFFFE, int(depth_threshold)))

    @staticmethod
    def _decode_dt(v: int) -> Optional[int]:
        """Decode depth_threshold (0xFFFF -> None)."""
        return None if v == 0xFFFF else int(v)

    def _write_header(self, bw: BitWriter, orig_len: int):
        """Write stream header with all parameters."""
        # MAGIC (32 bits)
        for b in self.MAGIC:
            bw.write_u8(b)
        bw.write_u32(orig_len)
        bw.write_u16(self.alphabet_size)
        bw.write_u16(self.splay_every)
        bw.write_u16(self._encode_dt(self.depth_threshold))
        bw.write_u8(self.target_depth & 0xFF)
        bw.write_u32(0 if self.reset_block_bytes is None else int(
            self.reset_block_bytes))

    @classmethod
    def _read_header(cls, br: BitReader):
        """Read stream header and return parameters."""
        magic = bytes([br.read_u8(), br.read_u8(), br.read_u8(), br.read_u8()])
        if magic != cls.MAGIC:
            raise ValueError(
                f"Bad magic: expected {cls.MAGIC!r}, got {magic!r}")
        orig_len = br.read_u32()
        alphabet_size = br.read_u16()
        splay_every = br.read_u16()
        depth_threshold = cls._decode_dt(br.read_u16())
        target_depth = br.read_u8()
        reset_block_bytes = br.read_u32()
        if reset_block_bytes == 0:
            reset_block_bytes = None
        return orig_len, alphabet_size, splay_every, depth_threshold, target_depth, reset_block_bytes

    # ---- API ----
    def compress(self, data: bytes) -> bytes:
        """
        Compress data using Splay Tree prefix coding.

        Args:
            data: Input bytes to compress

        Returns:
            Compressed bytes
        """
        bw = BitWriter()
        self._write_header(bw, len(data))

        sym2leaf = self.sym2leaf
        parent = self.parent

        # i0: 0-based index of symbol about to encode
        for i0, b in enumerate(data):
            self._maybe_reset(i0)

            leaf = sym2leaf[b]
            code, leaf_depth = self._encode_path_bits_root_to_leaf(leaf)
            bw.write_bits(code, leaf_depth)

            if self._should_splay(i0 + 1, leaf_depth):
                p = parent[leaf]
                if p != -1:
                    self._splay_to_depth(p, self.target_depth)

        return bw.get_bytes()

    @classmethod
    def decompress(cls, comp: bytes) -> bytes:
        """
        Decompress data using Splay Tree prefix coding.

        Args:
            comp: Compressed bytes

        Returns:
            Decompressed bytes
        """
        br = BitReader(comp)
        (length, alphabet_size, splay_every, depth_threshold,
         target_depth, reset_block_bytes) = cls._read_header(br)

        dec = cls(
            alphabet_size=alphabet_size,
            splay_every=splay_every,
            depth_threshold=depth_threshold,
            target_depth=target_depth,
            reset_block_bytes=reset_block_bytes,
        )

        out = bytearray()
        left = dec.left
        right = dec.right
        sym = dec.sym
        parent = dec.parent

        for i0 in range(length):
            dec._maybe_reset(i0)

            n = dec.root
            depth = 0
            while sym[n] == -1:
                bit = br.read_bit()
                n = left[n] if bit == 0 else right[n]
                depth += 1

            s = sym[n]
            if s < 0:
                raise ValueError("Decoded padding symbol; corrupted stream.")
            out.append(s)

            if dec._should_splay(i0 + 1, depth):
                p = parent[n]
                if p != -1:
                    dec._splay_to_depth(p, dec.target_depth)

        return bytes(out)


# ----------------------------
# BWT (Burrows-Wheeler Transform) + inverse
# ----------------------------
def bwt_transform(block: bytes):
    """
    Apply Burrows-Wheeler Transform to a block.
    
    Args:
        block: Input bytes block
        
    Returns:
        Tuple of (last_column, primary_index)
    """
    n = len(block)
    if n == 0:
        return b"", 0
    rots = [block[i:] + block[:i] for i in range(n)]
    rots_sorted = sorted((rot, i) for i, rot in enumerate(rots))
    last = bytes(rot[-1] for rot, _ in rots_sorted)
    primary = [i for _, i in rots_sorted].index(0)
    return last, primary


def bwt_inverse(last: bytes, primary: int):
    """
    Inverse Burrows-Wheeler Transform.
    
    Args:
        last: Last column from BWT
        primary: Primary index
        
    Returns:
        Original block
    """
    n = len(last)
    if n == 0:
        return b""
    counts = [0] * 256
    for c in last:
        counts[c] += 1
    tots = [0] * 256
    s = 0
    for i in range(256):
        tots[i] = s
        s += counts[i]
    occ = [0] * 256
    lf = [0] * n
    for i, c in enumerate(last):
        lf[i] = tots[c] + occ[c]
        occ[c] += 1
    row = primary
    out = bytearray(n)
    for k in range(n - 1, -1, -1):
        c = last[row]
        out[k] = c
        row = lf[row]
    return bytes(out)


# ----------------------------
# MTF (Move-To-Front)
# ----------------------------
def mtf_encode(data: bytes, alphabet: int = 256):
    """
    Move-To-Front encoding.
    
    Args:
        data: Input bytes
        alphabet: Alphabet size (default 256)
        
    Returns:
        Encoded bytes
    """
    table = list(range(alphabet))
    out = bytearray()
    for b in data:
        idx = table.index(b)
        out.append(idx)
        table.pop(idx)
        table.insert(0, b)
    return bytes(out)


def mtf_decode(data: bytes, alphabet: int = 256):
    """
    Move-To-Front decoding.
    
    Args:
        data: Encoded bytes
        alphabet: Alphabet size (default 256)
        
    Returns:
        Decoded bytes
    """
    table = list(range(alphabet))
    out = bytearray()
    for idx in data:
        b = table[idx]
        out.append(b)
        table.pop(idx)
        table.insert(0, b)
    return bytes(out)