#!/usr/bin/env python3
"""
AIG to BENCH converter
Converts .aig files to .bench format using ABC tool
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional


class AigToBenchConverter:
    """Convert AIG files to BENCH format using ABC"""

    def __init__(self, abc_path: Optional[str] = None, bench_format: str = "auto"):
        """
        Initialize converter

        Args:
            abc_path: Path to ABC executable. If None, uses default location
            bench_format: Desired BENCH output mode: "auto" | "gate" | "lut"
        """
        if abc_path is None:
            # Try to find ABC in project directory first (prefer abc over yosys-abc)
            project_root = Path(__file__).parent.parent.parent
            default_abc = project_root / "bin" / "abc"
            if default_abc.exists():
                self.abc_path = str(default_abc)
            else:
                # Fallback to system ABC
                self.abc_path = "abc"
        else:
            self.abc_path = abc_path

        mode = (bench_format or "auto").strip().lower()
        if mode not in {"auto", "gate", "lut"}:
            mode = "auto"
        self.bench_format = mode

    @staticmethod
    def _is_lut_bench(bench_file: str) -> bool:
        """Lightweight detection of LUT-style BENCH output."""
        try:
            with open(bench_file, "r", errors="ignore") as f:
                # Read a small prefix; enough to detect LUT lines
                text = f.read(8192)
            return "LUT " in text or "LUT(" in text
        except Exception:
            return False

    def _bench_cmd_candidates(self, aig_file: str, bench_file: str) -> list[str]:
        """
        Generate write_bench command candidates.
        Note: in some yosys-abc builds, '-l' toggles LUT mode; defaults vary by build.
        """
        base = f"read_aiger {aig_file}; short_names;"
        plain = f"{base} write_bench {bench_file}; quit"
        with_l = f"{base} write_bench -l {bench_file}; quit"

        if self.bench_format == "gate":
            # Prefer non-LUT output; try both to handle toggle ambiguity.
            return [plain, with_l]
        if self.bench_format == "lut":
            return [with_l, plain]
        # auto
        return [plain, with_l]

    def convert(self, aig_file: str, bench_file: str, timeout: int = 60) -> Tuple[bool, str]:
        """
        Convert a single AIG file to BENCH format

        Args:
            aig_file: Path to input .aig file
            bench_file: Path to output .bench file
            timeout: Timeout in seconds

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(bench_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        try:
            last_error = ""
            for abc_cmd in self._bench_cmd_candidates(aig_file, bench_file):
                result = subprocess.run(
                    [self.abc_path, '-c', abc_cmd],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                if result.returncode != 0 or not os.path.exists(bench_file):
                    last_error = result.stderr if result.stderr else result.stdout
                    continue

                is_lut = self._is_lut_bench(bench_file)
                if self.bench_format == "gate" and is_lut:
                    last_error = "Generated LUT-style BENCH while gate-level was requested"
                    continue
                if self.bench_format == "lut" and not is_lut:
                    last_error = "Generated gate-level BENCH while LUT-style was requested"
                    continue

                size = os.path.getsize(bench_file)
                mode = "LUT" if is_lut else "gate"
                return True, f"Success ({size} bytes, mode={mode})"

            return False, f"ABC error: {last_error[:200] if last_error else 'write_bench failed'}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout (>{timeout}s)"
        except FileNotFoundError:
            return False, f"ABC tool not found at: {self.abc_path}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def convert_batch(self, input_dir: str, output_dir: str,
                     recursive: bool = True, timeout: int = 60) -> dict:
        """
        Convert all AIG files in a directory

        Args:
            input_dir: Input directory containing .aig files
            output_dir: Output directory for .bench files
            recursive: Whether to search subdirectories
            timeout: Timeout per file in seconds

        Returns:
            Dictionary with conversion statistics
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # Find all AIG files
        if recursive:
            aig_files = list(input_path.rglob("*.aig"))
        else:
            aig_files = list(input_path.glob("*.aig"))

        stats = {
            'total': len(aig_files),
            'success': 0,
            'failed': 0,
            'failed_files': []
        }

        for aig_file in aig_files:
            # Preserve directory structure
            rel_path = aig_file.relative_to(input_path)
            bench_file = output_path / rel_path.with_suffix('.bench')

            # Convert
            success, message = self.convert(str(aig_file), str(bench_file), timeout)

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_files'].append({
                    'file': str(aig_file),
                    'error': message
                })

        return stats


def convert_aig_to_bench(aig_file: str, bench_file: str,
                        abc_path: Optional[str] = None,
                        bench_format: str = "auto") -> Tuple[bool, str]:
    """
    Convenience function to convert a single AIG file to BENCH

    Args:
        aig_file: Path to input .aig file
        bench_file: Path to output .bench file
        abc_path: Optional path to ABC executable

    Returns:
        Tuple of (success: bool, message: str)
    """
    converter = AigToBenchConverter(abc_path, bench_format=bench_format)
    return converter.convert(aig_file, bench_file)
