"""
Self-contained secp256k1 elliptic curve operations.

No external dependencies. Pure Python for portability.
GPU backends override these with accelerated versions.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List
import hashlib

# secp256k1 curve parameters
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


@dataclass(frozen=True, slots=True)
class Point:
    """Immutable point on secp256k1."""
    x: Optional[int]
    y: Optional[int]

    @property
    def is_infinity(self) -> bool:
        return self.x is None

    @classmethod
    def infinity(cls) -> Point:
        return cls(None, None)

    def to_bytes(self, compressed: bool = True) -> bytes:
        if self.is_infinity:
            return b'\x00'
        if compressed:
            prefix = 0x02 if self.y % 2 == 0 else 0x03
            return bytes([prefix]) + self.x.to_bytes(32, 'big')
        return b'\x04' + self.x.to_bytes(32, 'big') + self.y.to_bytes(32, 'big')

    def to_hex(self) -> str:
        if self.is_infinity:
            return "infinity"
        return self.to_bytes(compressed=True).hex()

    @classmethod
    def from_hex(cls, h: str) -> Point:
        if h == "infinity":
            return cls.infinity()
        data = bytes.fromhex(h)
        return cls.from_bytes(data)

    @classmethod
    def from_bytes(cls, data: bytes) -> Point:
        if len(data) == 33:
            prefix = data[0]
            x = int.from_bytes(data[1:], 'big')
            y_sq = (pow(x, 3, P) + 7) % P
            y = pow(y_sq, (P + 1) // 4, P)
            if prefix == 0x02:
                y = y if y % 2 == 0 else P - y
            else:
                y = y if y % 2 == 1 else P - y
            return cls(x, y)
        elif len(data) == 65:
            x = int.from_bytes(data[1:33], 'big')
            y = int.from_bytes(data[33:65], 'big')
            return cls(x, y)
        raise ValueError(f"Invalid point: {len(data)} bytes")


# Generator point
G = Point(GX, GY)


def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = _extended_gcd(b % a, a)
    return gcd, y1 - (b // a) * x1, x1


def mod_inv(a: int, m: int = P) -> int:
    if a < 0:
        a = a % m
    _, x, _ = _extended_gcd(a, m)
    return x % m


def add(p1: Point, p2: Point) -> Point:
    """Add two points."""
    if p1.is_infinity:
        return p2
    if p2.is_infinity:
        return p1
    if p1.x == p2.x:
        if p1.y == p2.y:
            return double(p1)
        return Point.infinity()

    s = ((p2.y - p1.y) * mod_inv(p2.x - p1.x)) % P
    x3 = (s * s - p1.x - p2.x) % P
    y3 = (s * (p1.x - x3) - p1.y) % P
    return Point(x3, y3)


def double(p: Point) -> Point:
    """Double a point."""
    if p.is_infinity or p.y == 0:
        return Point.infinity()
    s = (3 * p.x * p.x * mod_inv(2 * p.y)) % P
    x3 = (s * s - 2 * p.x) % P
    y3 = (s * (p.x - x3) - p.y) % P
    return Point(x3, y3)


def multiply(p: Point, k: int) -> Point:
    """Scalar multiplication using double-and-add."""
    if k == 0:
        return Point.infinity()
    if k < 0:
        k = k % ORDER
    if k == 1:
        return p

    result = Point.infinity()
    addend = p

    while k > 0:
        if k & 1:
            result = add(result, addend)
        addend = double(addend)
        k >>= 1

    return result


def is_distinguished(point: Point, mask: int) -> bool:
    """Check if point is distinguished (trailing zeros in x)."""
    if point.is_infinity:
        return False
    return (point.x & mask) == 0


def hash_point(point: Point) -> str:
    """Hash point for collision lookup."""
    if point.is_infinity:
        return "inf"
    data = point.x.to_bytes(32, 'big')
    return hashlib.sha256(data).hexdigest()[:16]


class JumpTable:
    """Pre-computed jump vectors for kangaroo."""

    def __init__(self, num_jumps: int = 32, mean_jump: int = 2**30):
        self.num_jumps = num_jumps
        self.sizes: List[int] = []
        self.points: List[Point] = []

        base = max(1, mean_jump // (2 ** (num_jumps // 2)))
        for i in range(num_jumps):
            size = base * (2 ** i)
            self.sizes.append(size)
            self.points.append(multiply(G, size))

    def get_jump(self, point: Point) -> Tuple[int, Point]:
        """Get deterministic jump based on point."""
        idx = point.x % self.num_jumps
        return self.sizes[idx], self.points[idx]

    def to_list(self) -> List[int]:
        """Serialize jump sizes for transmission."""
        return self.sizes

    @classmethod
    def from_list(cls, sizes: List[int]) -> JumpTable:
        """Deserialize from jump sizes."""
        table = cls.__new__(cls)
        table.num_jumps = len(sizes)
        table.sizes = sizes
        table.points = [multiply(G, s) for s in sizes]
        return table
