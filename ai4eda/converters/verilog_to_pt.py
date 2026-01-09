#!/usr/bin/env python3
"""
Verilog to PyTorch Geometric converter (direct)
Converts .v files directly to .pt format by chaining conversions
"""

import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional

from .verilog_to_aig import VerilogToAigConverter
from .aig_to_bench import AigToBenchConverter
from .bench_to_graphml import BenchToGraphMLConverter
from .graphml_to_pt import GraphMLToPTConverter


class VerilogToPTConverter:
    """Convert Verilog files directly to PyTorch Geometric format"""

    def __init__(self, yosys_abc_path: Optional[str] = None,
                 abc_path: Optional[str] = None):
        """
        Initialize converter

        Args:
            yosys_abc_path: Path to yosys-abc executable
            abc_path: Path to ABC executable
        """
        self.verilog_to_aig = VerilogToAigConverter(yosys_abc_path)
        self.aig_to_bench = AigToBenchConverter(abc_path)
        self.bench_to_graphml = BenchToGraphMLConverter()
        self.graphml_to_pt = GraphMLToPTConverter()

    def convert(self, verilog_file: str, pt_file: str,
                top_module: Optional[str] = None,
                keep_intermediate: bool = False,
                intermediate_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Convert Verilog file directly to PT format

        Args:
            verilog_file: Path to input .v file
            pt_file: Path to output .pt file
            top_module: Optional top module name
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
            base_name = Path(verilog_file).stem
            temp_aig = os.path.join(intermediate_dir, base_name + ".aig")
            temp_bench = os.path.join(intermediate_dir, base_name + ".bench")
            temp_graphml = os.path.join(intermediate_dir, base_name + ".graphml")
            use_temp_dir = False
        else:
            use_temp_dir = True

        try:
            if use_temp_dir:
                # Use temporary directory for intermediate files
                with tempfile.TemporaryDirectory() as tmpdir:
                    temp_aig = os.path.join(tmpdir, "temp.aig")
                    temp_bench = os.path.join(tmpdir, "temp.bench")
                    temp_graphml = os.path.join(tmpdir, "temp.graphml")
                    return self._do_conversion(verilog_file, temp_aig,
                                              temp_bench, temp_graphml,
                                              pt_file, top_module)
            else:
                # Keep intermediate files
                return self._do_conversion(verilog_file, temp_aig,
                                          temp_bench, temp_graphml,
                                          pt_file, top_module)

        except Exception as e:
            return False, f"Conversion error: {str(e)}"

    def _do_conversion(self, verilog_file: str, aig_file: str,
                      bench_file: str, graphml_file: str, pt_file: str,
                      top_module: Optional[str] = None) -> Tuple[bool, str]:
        """Perform the actual conversion chain"""
        # Step 1: Verilog → AIG
        success, msg = self.verilog_to_aig.convert(verilog_file, aig_file, top_module)
        if not success:
            return False, f"Verilog→AIG failed: {msg}"

        # Step 2: AIG → BENCH
        success, msg = self.aig_to_bench.convert(aig_file, bench_file)
        if not success:
            return False, f"AIG→BENCH failed: {msg}"

        # Step 3: BENCH → GraphML
        success, msg = self.bench_to_graphml.convert(bench_file, graphml_file)
        if not success:
            return False, f"BENCH→GraphML failed: {msg}"

        # Step 4: GraphML → PT
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
        Convert all Verilog files in a directory to PT format

        Args:
            input_dir: Input directory containing .v files
            output_dir: Output directory for .pt files
            recursive: Whether to search subdirectories
            keep_intermediate: Whether to keep intermediate files

        Returns:
            Dictionary with conversion statistics
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # Find all Verilog files
        if recursive:
            verilog_files = list(input_path.rglob("*.v"))
        else:
            verilog_files = list(input_path.glob("*.v"))

        stats = {
            'total': len(verilog_files),
            'success': 0,
            'failed': 0,
            'failed_files': []
        }

        for verilog_file in verilog_files:
            # Preserve directory structure
            rel_path = verilog_file.relative_to(input_path)
            pt_file = output_path / rel_path.with_suffix('.pt')

            # Set intermediate directory if keeping files
            if keep_intermediate:
                intermediate_dir = output_path / rel_path.parent / "intermediate"
            else:
                intermediate_dir = None

            # Convert
            success, message = self.convert(
                str(verilog_file), str(pt_file),
                keep_intermediate=keep_intermediate,
                intermediate_dir=str(intermediate_dir) if intermediate_dir else None
            )

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_files'].append({
                    'file': str(verilog_file),
                    'error': message
                })

        return stats


def convert_verilog_to_pt(verilog_file: str, pt_file: str,
                         yosys_abc_path: Optional[str] = None,
                         abc_path: Optional[str] = None,
                         top_module: Optional[str] = None,
                         keep_intermediate: bool = False) -> Tuple[bool, str]:
    """
    Convenience function to convert Verilog directly to PT format

    Args:
        verilog_file: Path to input .v file
        pt_file: Path to output .pt file
        yosys_abc_path: Optional path to yosys-abc executable
        abc_path: Optional path to ABC executable
        top_module: Optional top module name
        keep_intermediate: Whether to keep intermediate files

    Returns:
        Tuple of (success: bool, message: str)
    """
    converter = VerilogToPTConverter(yosys_abc_path, abc_path)
    return converter.convert(verilog_file, pt_file, top_module, keep_intermediate)
