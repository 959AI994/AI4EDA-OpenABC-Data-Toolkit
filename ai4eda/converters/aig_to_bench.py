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

    def __init__(self, abc_path: Optional[str] = None):
        """
        Initialize converter

        Args:
            abc_path: Path to ABC executable. If None, uses default location
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

        # ABC command: read AIG, apply short_names, write BENCH
        abc_cmd = f'read_aiger {aig_file}; short_names; write_bench {bench_file}; quit'

        try:
            result = subprocess.run(
                [self.abc_path, '-c', abc_cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0 and os.path.exists(bench_file):
                # Get file size for reporting
                size = os.path.getsize(bench_file)
                return True, f"Success ({size} bytes)"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"ABC error: {error_msg[:100]}"

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
                        abc_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Convenience function to convert a single AIG file to BENCH

    Args:
        aig_file: Path to input .aig file
        bench_file: Path to output .bench file
        abc_path: Optional path to ABC executable

    Returns:
        Tuple of (success: bool, message: str)
    """
    converter = AigToBenchConverter(abc_path)
    return converter.convert(aig_file, bench_file)
