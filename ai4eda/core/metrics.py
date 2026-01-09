#!/usr/bin/env python3
"""
Compute area and delay metrics using Liberty library
Uses ABC for technology mapping and metric extraction
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict


class MetricsCalculator:
    """Calculate area and delay metrics using ABC and Liberty library"""

    def __init__(self, lib_path: Optional[str] = None, abc_path: Optional[str] = None):
        """
        Initialize metrics calculator

        Args:
            lib_path: Path to Liberty (.lib) file
            abc_path: Path to ABC executable
        """
        # Set default lib path
        if lib_path is None:
            project_root = Path(__file__).parent.parent.parent
            default_lib = project_root / "libs" / "asap7.lib"
            self.lib_path = str(default_lib) if default_lib.exists() else None
        else:
            self.lib_path = lib_path

        # Set default ABC path
        if abc_path is None:
            project_root = Path(__file__).parent.parent.parent
            default_abc = project_root / "bin" / "yosys-abc"
            if default_abc.exists():
                self.abc_path = str(default_abc)
            else:
                self.abc_path = "abc"
        else:
            self.abc_path = abc_path

    def calculate_from_aig(self, aig_file: str, opt_script: str = "",
                          timeout: int = 300) -> Tuple[Optional[float], Optional[float], str]:
        """
        Calculate area and delay from AIG file

        Args:
            aig_file: Path to .aig file
            opt_script: Optional ABC optimization script (e.g., "balance; rewrite")
            timeout: Timeout in seconds

        Returns:
            Tuple of (area, delay, error_message)
        """
        if self.lib_path is None:
            return None, None, "Liberty library not specified"

        if not os.path.exists(self.lib_path):
            return None, None, f"Liberty library not found: {self.lib_path}"

        if not os.path.exists(aig_file):
            return None, None, f"AIG file not found: {aig_file}"

        # Build ABC command
        if opt_script:
            script = f"read_aiger {aig_file}; read_lib {self.lib_path}; strash; {opt_script}; map; print_stats"
        else:
            script = f"read_aiger {aig_file}; read_lib {self.lib_path}; strash; map; print_stats"

        command = f'{self.abc_path} -c "{script}"'

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout

            # Parse ABC output for area and delay
            area = self._extract_metric(output, 'area')
            delay = self._extract_metric(output, 'delay')

            if area is None or delay is None:
                return area, delay, "Failed to parse metrics from ABC output"

            return area, delay, "Success"

        except subprocess.TimeoutExpired:
            return None, None, f"Timeout (>{timeout}s)"
        except FileNotFoundError:
            return None, None, f"ABC tool not found: {self.abc_path}"
        except Exception as e:
            return None, None, f"Error: {str(e)}"

    def calculate_from_bench(self, bench_file: str, opt_script: str = "",
                            timeout: int = 300) -> Tuple[Optional[float], Optional[float], str]:
        """
        Calculate area and delay from BENCH file

        Args:
            bench_file: Path to .bench file
            opt_script: Optional ABC optimization script
            timeout: Timeout in seconds

        Returns:
            Tuple of (area, delay, error_message)
        """
        if self.lib_path is None:
            return None, None, "Liberty library not specified"

        if not os.path.exists(self.lib_path):
            return None, None, f"Liberty library not found: {self.lib_path}"

        if not os.path.exists(bench_file):
            return None, None, f"BENCH file not found: {bench_file}"

        # Build ABC command
        if opt_script:
            script = f"read_bench {bench_file}; read_lib {self.lib_path}; strash; {opt_script}; map; print_stats"
        else:
            script = f"read_bench {bench_file}; read_lib {self.lib_path}; strash; map; print_stats"

        command = f'{self.abc_path} -c "{script}"'

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout

            # Parse ABC output for area and delay
            area = self._extract_metric(output, 'area')
            delay = self._extract_metric(output, 'delay')

            if area is None or delay is None:
                return area, delay, "Failed to parse metrics from ABC output"

            return area, delay, "Success"

        except subprocess.TimeoutExpired:
            return None, None, f"Timeout (>{timeout}s)"
        except FileNotFoundError:
            return None, None, f"ABC tool not found: {self.abc_path}"
        except Exception as e:
            return None, None, f"Error: {str(e)}"

    def _extract_metric(self, abc_output: str, metric_name: str) -> Optional[float]:
        """
        Extract metric value from ABC output

        Args:
            abc_output: ABC command output
            metric_name: Metric name ('area' or 'delay')

        Returns:
            Metric value or None if not found
        """
        # Try multiple patterns
        patterns = [
            rf'{metric_name}\s*=\s*([\d\.]+)',
            rf'{metric_name}\s+=\s*([\d\.]+)',
            rf'{metric_name}=([\d\.]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, abc_output, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def calculate_batch(self, input_dir: str, file_pattern: str = "*.aig",
                       opt_script: str = "", timeout: int = 300) -> Dict:
        """
        Calculate metrics for all files matching pattern

        Args:
            input_dir: Input directory
            file_pattern: File pattern (e.g., "*.aig" or "*.bench")
            opt_script: Optional ABC optimization script
            timeout: Timeout per file

        Returns:
            Dictionary with results
        """
        input_path = Path(input_dir)
        files = list(input_path.rglob(file_pattern))

        results = {
            'total': len(files),
            'success': 0,
            'failed': 0,
            'metrics': []
        }

        for file_path in files:
            # Determine file type and calculate
            if file_path.suffix == '.aig':
                area, delay, msg = self.calculate_from_aig(str(file_path), opt_script, timeout)
            elif file_path.suffix == '.bench':
                area, delay, msg = self.calculate_from_bench(str(file_path), opt_script, timeout)
            else:
                continue

            if area is not None and delay is not None:
                results['success'] += 1
                results['metrics'].append({
                    'file': str(file_path),
                    'area': area,
                    'delay': delay
                })
            else:
                results['failed'] += 1

        return results


def calculate_metrics(file_path: str, lib_path: str,
                     abc_path: Optional[str] = None,
                     opt_script: str = "") -> Tuple[Optional[float], Optional[float], str]:
    """
    Convenience function to calculate metrics for a single file

    Args:
        file_path: Path to .aig or .bench file
        lib_path: Path to Liberty library file
        abc_path: Optional path to ABC executable
        opt_script: Optional ABC optimization script

    Returns:
        Tuple of (area, delay, message)
    """
    calculator = MetricsCalculator(lib_path, abc_path)

    file_ext = Path(file_path).suffix
    if file_ext == '.aig':
        return calculator.calculate_from_aig(file_path, opt_script)
    elif file_ext == '.bench':
        return calculator.calculate_from_bench(file_path, opt_script)
    else:
        return None, None, f"Unsupported file type: {file_ext}"
