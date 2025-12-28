"""
Kangaroo Binary Plugin - Wraps JeanLucPons/Kangaroo GPU binary.

This is the REAL GPU acceleration - 1B+ ops/sec.
https://github.com/JeanLucPons/Kangaroo

Install:
  git clone https://github.com/JeanLucPons/Kangaroo
  cd Kangaroo && make gpu=1
  # Binary at ./kangaroo
"""

import os
import subprocess
import tempfile
import re
from pathlib import Path
from typing import List, Tuple, Optional

from ants_worker.plugins.registry import ComputePlugin, register_compute
from ants_worker.core.crypto import Point, JumpTable
from ants_worker.core.worker import WalkResult


def find_kangaroo_binary() -> Optional[str]:
    """Find the Kangaroo binary."""
    # Check common locations
    candidates = [
        os.environ.get("KANGAROO_BIN"),
        "/usr/local/bin/kangaroo",
        os.path.expanduser("~/Kangaroo/kangaroo"),
        os.path.expanduser("~/.local/bin/kangaroo"),
        "./kangaroo",
        "./Kangaroo/kangaroo",
    ]

    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    # Try which
    try:
        result = subprocess.run(
            ["which", "kangaroo"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return None


@register_compute
class KangarooBinaryPlugin(ComputePlugin):
    """
    Wrap the JeanLucPons Kangaroo binary.

    This gives us real GPU performance: 1-4 billion ops/sec.
    """

    def __init__(self, binary_path: Optional[str] = None, use_gpu: bool = True):
        self.binary_path = binary_path or find_kangaroo_binary()
        self.use_gpu = use_gpu
        self._gpu_info: Optional[str] = None

        if self.binary_path:
            self._detect_gpu()

    def _detect_gpu(self):
        """Detect GPU via the binary."""
        try:
            result = subprocess.run(
                [self.binary_path, "-v"],
                capture_output=True, text=True, timeout=10
            )
            self._gpu_info = result.stdout
        except Exception:
            pass

    @property
    def name(self) -> str:
        return "kangaroo"

    @classmethod
    def is_available(cls) -> bool:
        return find_kangaroo_binary() is not None

    @classmethod
    def priority(cls) -> int:
        return 200  # Highest priority - this is the real deal

    def walk(
        self,
        start_point: Point,
        start_distance: int,
        jump_table: JumpTable,
        dp_mask: int,
        max_ops: int,
    ) -> WalkResult:
        """
        Run Kangaroo binary for a walk.

        Note: The binary is designed for full puzzle solving, not short walks.
        For short walks, we use it in a limited way.
        """
        if not self.binary_path:
            raise RuntimeError("Kangaroo binary not found")

        # For integration, we run a short search
        # The binary will output distinguished points to work file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.txt"
            work_file = Path(tmpdir) / "work.dat"

            # Create input file
            # Note: We're adapting the puzzle-solving tool for our walk
            # The range is artificial - we just want it to run for a bit
            range_start = start_distance
            range_end = start_distance + max_ops * 1000  # Approximate

            # Use a dummy public key (we're not actually solving, just generating DPs)
            # In real use, the Queen would send the actual target
            pubkey_hex = start_point.to_bytes(compressed=True).hex()

            input_file.write_text(
                f"{hex(range_start)[2:].upper()}\n"
                f"{hex(range_end)[2:].upper()}\n"
                f"{pubkey_hex.upper()}\n"
            )

            # Build command
            cmd = [self.binary_path]
            if self.use_gpu:
                cmd.append("-gpu")
            cmd.extend([
                "-d", str(dp_mask.bit_length()),  # DP bits
                "-w", str(work_file),  # Save work
                "-t", "0",  # Use all CPU threads too
                str(input_file),
            ])

            # Run with timeout (short run for walk simulation)
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=max_ops // 100000 + 5,  # Rough timeout
                    cwd=tmpdir,
                )
            except subprocess.TimeoutExpired:
                pass  # Expected - we time out short walks

            # Parse output for DPs and stats
            dps = self._parse_output(result.stdout if result else "")
            ops = self._parse_ops(result.stdout if result else "")

        return WalkResult(
            operations=ops or max_ops,
            distinguished_points=dps,
            final_point=start_point,  # We don't track this in binary mode
            final_distance=start_distance + (ops or max_ops),
        )

    def _parse_output(self, output: str) -> List[Tuple[str, int]]:
        """Parse distinguished points from output."""
        dps = []
        # Look for DP lines in output
        for line in output.split('\n'):
            if 'DP' in line or 'distinguished' in line.lower():
                # Extract hex values
                match = re.search(r'([0-9A-Fa-f]{64,})', line)
                if match:
                    dps.append((match.group(1), 0))
        return dps

    def _parse_ops(self, output: str) -> Optional[int]:
        """Parse operation count from output."""
        # Look for speed/ops lines
        for line in output.split('\n'):
            match = re.search(r'(\d+\.?\d*)\s*[GMK]?op', line, re.I)
            if match:
                val = float(match.group(1))
                if 'G' in line:
                    return int(val * 1e9)
                elif 'M' in line:
                    return int(val * 1e6)
                elif 'K' in line:
                    return int(val * 1e3)
                return int(val)
        return None

    def run_search(
        self,
        range_start: int,
        range_end: int,
        pubkey: str,
        work_file: Optional[str] = None,
        dp_bits: int = 20,
    ) -> Optional[str]:
        """
        Run a full puzzle search.

        This is the main use case - give it a range and pubkey,
        let it run until solved.

        Args:
            range_start: Start of key range
            range_end: End of key range
            pubkey: Target public key (compressed hex)
            work_file: Optional work file for resume
            dp_bits: Distinguished point bits

        Returns:
            Private key if found, None otherwise
        """
        if not self.binary_path:
            raise RuntimeError("Kangaroo binary not found")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(f"{hex(range_start)[2:].upper()}\n")
            f.write(f"{hex(range_end)[2:].upper()}\n")
            f.write(f"{pubkey.upper()}\n")
            input_file = f.name

        cmd = [self.binary_path]
        if self.use_gpu:
            cmd.append("-gpu")
        cmd.extend(["-d", str(dp_bits)])
        if work_file:
            cmd.extend(["-w", work_file])
        cmd.append(input_file)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Look for solved key in output
            for line in result.stdout.split('\n'):
                if 'Priv:' in line:
                    match = re.search(r'Priv:\s*0x([0-9A-Fa-f]+)', line)
                    if match:
                        return match.group(1)
        finally:
            os.unlink(input_file)

        return None

    def info(self) -> dict:
        return {
            "name": self.name,
            "binary": self.binary_path,
            "available": self.binary_path is not None,
            "gpu": self.use_gpu,
            "priority": self.priority(),
        }
