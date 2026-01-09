#!/usr/bin/env python3
"""
Verilog to AIG converter
Converts Verilog files to AIG format using Yosys-ABC
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional


class VerilogToAigConverter:
    """Convert Verilog files to AIG format using Yosys-ABC"""

    def __init__(self, yosys_abc_path: Optional[str] = None):
        """
        Initialize converter

        Args:
            yosys_abc_path: Path to yosys-abc executable
        """
        if yosys_abc_path is None:
            # Try to find yosys-abc in project directory first
            project_root = Path(__file__).parent.parent.parent
            default_yosys_abc = project_root / "bin" / "yosys-abc"
            if default_yosys_abc.exists():
                self.yosys_abc_path = str(default_yosys_abc)
            else:
                # Fallback to system yosys-abc
                self.yosys_abc_path = "yosys-abc"
        else:
            self.yosys_abc_path = yosys_abc_path

    def convert(self, verilog_file: str, aig_file: str,
               top_module: Optional[str] = None,
               timeout: int = 300) -> Tuple[bool, str]:
        """
        Convert Verilog file to AIG format

        Args:
            verilog_file: Path to input .v file
            aig_file: Path to output .aig file
            top_module: Optional top module name
            timeout: Timeout in seconds

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(aig_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Build ABC command
        # Read verilog, synthesize to AIG, write AIG
        if top_module:
            abc_cmd = f'read -m {top_module} {verilog_file}; strash; write_aiger {aig_file}; quit'
        else:
            abc_cmd = f'read {verilog_file}; strash; write_aiger {aig_file}; quit'

        try:
            result = subprocess.run(
                [self.yosys_abc_path, '-c', abc_cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0 and os.path.exists(aig_file):
                # Get file size
                size = os.path.getsize(aig_file)
                return True, f"Success ({size} bytes)"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"Conversion error: {error_msg[:200]}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout (>{timeout}s)"
        except FileNotFoundError:
            return False, f"yosys-abc not found at: {self.yosys_abc_path}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def convert_with_script(self, verilog_file: str, aig_file: str,
                           abc_script: str,
                           timeout: int = 300) -> Tuple[bool, str]:
        """
        Convert Verilog to AIG using custom ABC script

        Args:
            verilog_file: Path to input .v file
            aig_file: Path to output .aig file
            abc_script: Custom ABC script (e.g., "read file.v; balance; rewrite; write_aiger out.aig")
            timeout: Timeout in seconds

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(aig_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        try:
            result = subprocess.run(
                [self.yosys_abc_path, '-c', abc_script],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0 and os.path.exists(aig_file):
                size = os.path.getsize(aig_file)
                return True, f"Success ({size} bytes)"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"Conversion error: {error_msg[:200]}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout (>{timeout}s)"
        except FileNotFoundError:
            return False, f"yosys-abc not found at: {self.yosys_abc_path}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def convert_batch(self, input_dir: str, output_dir: str,
                     recursive: bool = True,
                     timeout: int = 300) -> dict:
        """
        Convert all Verilog files in a directory

        Args:
            input_dir: Input directory containing .v files
            output_dir: Output directory for .aig files
            recursive: Whether to search subdirectories
            timeout: Timeout per file in seconds

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
            aig_file = output_path / rel_path.with_suffix('.aig')

            # Convert
            success, message = self.convert(str(verilog_file), str(aig_file), timeout=timeout)

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_files'].append({
                    'file': str(verilog_file),
                    'error': message
                })

        return stats


def convert_verilog_to_aig(verilog_file: str, aig_file: str,
                          yosys_abc_path: Optional[str] = None,
                          top_module: Optional[str] = None) -> Tuple[bool, str]:
    """
    Convenience function to convert a single Verilog file to AIG

    Args:
        verilog_file: Path to input .v file
        aig_file: Path to output .aig file
        yosys_abc_path: Optional path to yosys-abc executable
        top_module: Optional top module name

    Returns:
        Tuple of (success: bool, message: str)
    """
    converter = VerilogToAigConverter(yosys_abc_path)
    return converter.convert(verilog_file, aig_file, top_module)
