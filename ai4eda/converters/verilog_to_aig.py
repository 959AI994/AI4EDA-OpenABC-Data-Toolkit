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
    """Convert Verilog files to AIG format using Yosys and ABC"""

    def __init__(self, yosys_abc_path: Optional[str] = None,
                 yosys_path: Optional[str] = None):
        """
        Initialize converter

        Args:
            yosys_abc_path: Path to yosys-abc executable
            yosys_path: Path to yosys executable (for complex Verilog)
        """
        # Try to find yosys in project directory or user's yosys directory
        project_root = Path(__file__).parent.parent.parent

        # Set yosys path
        if yosys_path is None:
            # Try user's yosys directory first
            user_yosys = Path("/home/wjx/yosys/yosys")
            if user_yosys.exists():
                self.yosys_path = str(user_yosys)
            else:
                # Try project bin directory
                project_yosys = project_root / "bin" / "yosys"
                if project_yosys.exists():
                    self.yosys_path = str(project_yosys)
                else:
                    # Fallback to system yosys
                    self.yosys_path = "yosys"
        else:
            self.yosys_path = yosys_path

        # Set yosys-abc path
        if yosys_abc_path is None:
            # Try user's yosys directory first
            user_abc = Path("/home/wjx/yosys/yosys-abc")
            if user_abc.exists():
                self.yosys_abc_path = str(user_abc)
            else:
                # Try project bin directory
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
        Convert Verilog file to AIG format using Yosys

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

        # Build Yosys script
        verilog_path = os.path.abspath(verilog_file)
        aig_path = os.path.abspath(aig_file)

        # Yosys script to read Verilog, synthesize, and export to AIGER
        # AIGER format only supports AND gates and inverters
        if top_module:
            yosys_script = f"""
read_verilog {verilog_path}
hierarchy -top {top_module}
proc
flatten
tribuf -logic
deminout
opt
memory
techmap
opt
aigmap
clean
write_aiger {aig_path}
"""
        else:
            yosys_script = f"""
read_verilog {verilog_path}
hierarchy -auto-top
proc
flatten
tribuf -logic
deminout
opt
memory
techmap
opt
aigmap
clean
write_aiger {aig_path}
"""

        try:
            result = subprocess.run(
                [self.yosys_path, '-p', yosys_script],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0 and os.path.exists(aig_file):
                size = os.path.getsize(aig_file)
                return True, f"Success ({size} bytes)"
            else:
                error_msg = result.stderr if result.stderr else result.stdout

                # Provide helpful error messages
                if "ERROR:" in error_msg:
                    # Extract the actual error message
                    error_lines = [line for line in error_msg.split('\n') if 'ERROR:' in line]
                    if error_lines:
                        error_line = error_lines[0]

                        # Check for specific error types
                        if "Unsupported cell type: $_SDFF" in error_line or "Unsupported cell type: $_DFF" in error_line:
                            return False, (
                                "This Verilog file contains sequential logic (flip-flops/latches) which "
                                "cannot be directly converted to combinational AIG format. "
                                "AIG (And-Inverter Graph) only represents combinational logic. "
                                "Consider: (1) extracting only the combinational logic, or "
                                "(2) using a different format that supports sequential circuits."
                            )
                        elif "Unsupported cell type" in error_line:
                            # Extract cell type
                            import re
                            match = re.search(r'Unsupported cell type: (\S+)', error_line)
                            cell_type = match.group(1) if match else "unknown"
                            return False, (
                                f"Synthesis generated unsupported cell type: {cell_type}. "
                                f"This may indicate the circuit uses advanced features that "
                                f"cannot be converted to basic AIG format (AND gates + inverters only)."
                            )
                        else:
                            return False, f"Verilog synthesis error: {error_line}"

                return False, f"Verilog conversion failed: {error_msg[:300]}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout (>{timeout}s)"
        except FileNotFoundError:
            return False, f"Yosys not found at: {self.yosys_path}. Please install Yosys or set the correct path."
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

                # Provide helpful error messages
                if "Cannot parse" in error_msg or "syntax error" in error_msg.lower():
                    return False, (
                        f"Verilog syntax not supported by yosys-abc. "
                        f"This file may contain advanced Verilog features (parameters, generate blocks, etc.) "
                        f"that require full Yosys. Try using Yosys first to synthesize to a simpler format, "
                        f"or simplify the Verilog code. Error: {error_msg[:150]}"
                    )
                elif "Cannot open file" in error_msg:
                    return False, f"Cannot open Verilog file. Please check the file path and permissions."
                else:
                    return False, f"Verilog conversion failed: {error_msg[:200]}"

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
