#!/usr/bin/env python3
"""
AIG to PyTorch Geometric converter (direct)
Converts .aig files directly to .pt format by chaining conversions
"""

import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional

from .aig_to_bench import AigToBenchConverter
from .bench_to_graphml import BenchToGraphMLConverter
from .graphml_to_pt import GraphMLToPTConverter


class AigToPTConverter:
    """Convert AIG files directly to PyTorch Geometric format"""

    def __init__(self, abc_path: Optional[str] = None):
        """
        Initialize converter

        Args:
            abc_path: Path to ABC executable
        """
        self.aig_to_bench = AigToBenchConverter(abc_path)
        self.bench_to_graphml = BenchToGraphMLConverter()
        self.graphml_to_pt = GraphMLToPTConverter()

    def convert(self, aig_file: str, pt_file: str,
                keep_intermediate: bool = False,
                intermediate_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Convert AIG file directly to PT format

        Args:
            aig_file: Path to input .aig file
            pt_file: Path to output .pt file
            keep_intermediate: Whether to keep intermediate files
            intermediate_dir: Directory for intermediate files (if keep_intermediate)

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(pt_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Set up intermediate file locations
        if keep_intermediate and intermediate_dir:
            os.makedirs(intermediate_dir, exist_ok=True)
            temp_bench = os.path.join(intermediate_dir,
                                     Path(aig_file).stem + ".bench")
            temp_graphml = os.path.join(intermediate_dir,
                                       Path(aig_file).stem + ".graphml")
            use_temp_dir = False
        else:
            use_temp_dir = True

        try:
            if use_temp_dir:
                # Use temporary directory for intermediate files
                with tempfile.TemporaryDirectory() as tmpdir:
                    temp_bench = os.path.join(tmpdir, "temp.bench")
                    temp_graphml = os.path.join(tmpdir, "temp.graphml")
                    return self._do_conversion(aig_file, temp_bench,
                                              temp_graphml, pt_file)
            else:
                # Keep intermediate files
                return self._do_conversion(aig_file, temp_bench,
                                          temp_graphml, pt_file)

        except Exception as e:
            return False, f"Conversion error: {str(e)}"

    def _do_conversion(self, aig_file: str, bench_file: str,
                      graphml_file: str, pt_file: str) -> Tuple[bool, str]:
        """Perform the actual conversion chain"""
        # Step 1: AIG → BENCH
        success, msg = self.aig_to_bench.convert(aig_file, bench_file)
        if not success:
            return False, f"AIG→BENCH failed: {msg}"

        # Step 2: BENCH → GraphML
        success, msg = self.bench_to_graphml.convert(bench_file, graphml_file)
        if not success:
            return False, f"BENCH→GraphML failed: {msg}"

        # Step 3: GraphML → PT
        success, msg = self.graphml_to_pt.convert(graphml_file, pt_file)
        if not success:
            return False, f"GraphML→PT failed: {msg}"

        # Get final file info
        size = os.path.getsize(pt_file)
        return True, f"Success ({size} bytes)"

    def convert_batch(self, input_dir: str, output_dir: str,
                     recursive: bool = True,
                     keep_intermediate: bool = False) -> dict:
        """
        Convert all AIG files in a directory to PT format

        Args:
            input_dir: Input directory containing .aig files
            output_dir: Output directory for .pt files
            recursive: Whether to search subdirectories
            keep_intermediate: Whether to keep intermediate files

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
            pt_file = output_path / rel_path.with_suffix('.pt')

            # Set intermediate directory if keeping files
            if keep_intermediate:
                intermediate_dir = output_path / rel_path.parent / "intermediate"
            else:
                intermediate_dir = None

            # Convert
            success, message = self.convert(
                str(aig_file), str(pt_file),
                keep_intermediate=keep_intermediate,
                intermediate_dir=str(intermediate_dir) if intermediate_dir else None
            )

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_files'].append({
                    'file': str(aig_file),
                    'error': message
                })

        return stats


def convert_aig_to_pt(aig_file: str, pt_file: str,
                     abc_path: Optional[str] = None,
                     keep_intermediate: bool = False) -> Tuple[bool, str]:
    """
    Convenience function to convert AIG directly to PT format

    Args:
        aig_file: Path to input .aig file
        pt_file: Path to output .pt file
        abc_path: Optional path to ABC executable
        keep_intermediate: Whether to keep intermediate files

    Returns:
        Tuple of (success: bool, message: str)
    """
    converter = AigToPTConverter(abc_path)
    return converter.convert(aig_file, pt_file, keep_intermediate)
