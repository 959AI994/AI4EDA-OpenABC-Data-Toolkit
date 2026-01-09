#!/usr/bin/env python3
"""
BENCH to GraphML converter
Converts .bench files to .graphml format for graph representation
"""

import os
import re
from pathlib import Path
from typing import Tuple, Optional
import networkx as nx


# Node types: 0-PI (Primary Input), 1-PO (Primary Output), 2-Internal
NODE_TYPE = {
    "PI": 0,
    "PO": 1,
    "Internal": 2
}

# Edge types: 0-BUFF (Buffer), 1-NOT (Inverter)
EDGE_TYPE = {
    "BUFF": 0,
    "NOT": 1
}


class BenchToGraphMLConverter:
    """Convert BENCH files to GraphML format"""

    def __init__(self):
        """Initialize converter"""
        pass

    def parse_bench_file(self, bench_file: str) -> nx.MultiDiGraph:
        """
        Parse BENCH file and create NetworkX graph

        Args:
            bench_file: Path to .bench file

        Returns:
            NetworkX MultiDiGraph representing the AIG
        """
        with open(bench_file, 'r') as f:
            lines = f.readlines()

        # Create directed graph
        aig_dag = nx.MultiDiGraph()

        # Tracking structures
        node_name_id_mapping = {}
        single_gate_input_io_mapping = {}
        po_list = []
        idx_counter = 0

        # Parse file line by line
        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#') or 'ABC' in line:
                continue

            # Handle VDD (treat as Primary Input)
            elif 'vdd' in line:
                line = line.replace(' ', '')
                match = re.search(r'(.*?)=', line)
                if match:
                    pi = match.group(1)
                    node_attr = {
                        "node_id": pi,
                        "node_type": NODE_TYPE["PI"],
                        "num_inverted_predecessors": 0
                    }
                    aig_dag.add_nodes_from([(idx_counter, node_attr)])
                    node_name_id_mapping[pi] = idx_counter
                    idx_counter += 1

            # Handle INPUT
            elif 'INPUT' in line:
                line = line.replace(' ', '')
                match = re.search(r'INPUT\((.*?)\)', line)
                if match:
                    pi = match.group(1)
                    node_attr = {
                        "node_id": pi,
                        "node_type": NODE_TYPE["PI"],
                        "num_inverted_predecessors": 0
                    }
                    aig_dag.add_nodes_from([(idx_counter, node_attr)])
                    node_name_id_mapping[pi] = idx_counter
                    idx_counter += 1

            # Handle OUTPUT
            elif 'OUTPUT' in line:
                line = line.replace(' ', '')
                match = re.search(r'OUTPUT\((.*?)\)', line)
                if match:
                    po = match.group(1)
                    po_list.append(po)

            # Handle AND gates
            elif 'AND' in line:
                line = line.replace(' ', '')
                output = re.search(r'(.*?)=', line).group(1)
                input1 = re.search(r'AND\((.*?),', line).group(1)
                input2 = re.search(r',(.*?)\)', line).group(1)

                idx_counter = self._process_and_gate(
                    [input1, input2], output, idx_counter,
                    po_list, node_name_id_mapping,
                    single_gate_input_io_mapping, aig_dag
                )

            # Handle NOT gates
            elif 'NOT' in line:
                line = line.replace(' ', '')
                output = re.search(r'(.*?)=', line).group(1)
                input_pin = re.search(r'NOT\((.*?)\)', line).group(1)
                single_gate_input_io_mapping[output] = input_pin

                if output in po_list:
                    node_attr = {
                        "node_id": output + "_inv",
                        "node_type": NODE_TYPE["PO"],
                        "num_inverted_predecessors": 1
                    }
                    aig_dag.add_nodes_from([(idx_counter, node_attr)])
                    node_name_id_mapping[output + "_inv"] = idx_counter
                    src_idx = node_name_id_mapping[input_pin]
                    aig_dag.add_edge(idx_counter, src_idx, edge_type=EDGE_TYPE["NOT"])
                    idx_counter += 1

            # Handle BUFF gates
            elif 'BUFF' in line:
                line = line.replace(' ', '')
                output = re.search(r'(.*?)=', line).group(1)
                input_pin = re.search(r'BUFF\((.*?)\)', line).group(1)
                single_gate_input_io_mapping[output] = input_pin
                num_inverted_predecessors = 0

                if output in po_list:
                    if input_pin in node_name_id_mapping:
                        src_idx = node_name_id_mapping[input_pin]
                        edge_type = EDGE_TYPE["BUFF"]
                    else:
                        src_idx = node_name_id_mapping[single_gate_input_io_mapping[input_pin]]
                        edge_type = EDGE_TYPE["NOT"]
                        num_inverted_predecessors += 1

                    node_attr = {
                        "node_id": output + "_buff",
                        "node_type": NODE_TYPE["PO"],
                        "num_inverted_predecessors": num_inverted_predecessors
                    }
                    aig_dag.add_nodes_from([(idx_counter, node_attr)])
                    node_name_id_mapping[output + "_buff"] = idx_counter
                    aig_dag.add_edge(idx_counter, src_idx, edge_type=edge_type)
                    idx_counter += 1

        return aig_dag

    def _process_and_gate(self, inputs, output, idx_counter, po_list,
                         node_name_id_mapping, single_gate_input_io_mapping, aig_dag):
        """Process AND gate assignment"""
        node_attr = {
            "node_id": output,
            "node_type": NODE_TYPE["Internal"],
            "num_inverted_predecessors": 0
        }
        aig_dag.add_nodes_from([(idx_counter, node_attr)])
        node_name_id_mapping[output] = idx_counter
        num_inverted_predecessors = 0

        for inp in inputs:
            if inp not in node_name_id_mapping:
                src_idx = node_name_id_mapping[single_gate_input_io_mapping[inp]]
                edge_type = EDGE_TYPE["NOT"]
                num_inverted_predecessors += 1
            else:
                src_idx = node_name_id_mapping[inp]
                edge_type = EDGE_TYPE["BUFF"]
            aig_dag.add_edge(idx_counter, src_idx, edge_type=edge_type)

        aig_dag.nodes[idx_counter]["num_inverted_predecessors"] = num_inverted_predecessors

        # If output is primary output, add additional node
        if output in po_list:
            node_attr = {
                "node_id": output + "_buff",
                "node_type": NODE_TYPE["PO"],
                "num_inverted_predecessors": 0
            }
            aig_dag.add_nodes_from([(idx_counter + 1, node_attr)])
            node_name_id_mapping[output + "_buff"] = idx_counter + 1
            src_idx = idx_counter
            aig_dag.add_edge(idx_counter + 1, src_idx, edge_type=EDGE_TYPE["BUFF"])
            idx_counter += 1

        idx_counter += 1
        return idx_counter

    def convert(self, bench_file: str, graphml_file: str) -> Tuple[bool, str]:
        """
        Convert a single BENCH file to GraphML format

        Args:
            bench_file: Path to input .bench file
            graphml_file: Path to output .graphml file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(graphml_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Parse BENCH file
            graph = self.parse_bench_file(bench_file)

            # Write GraphML
            nx.write_graphml(graph, graphml_file)

            # Get file size
            size = os.path.getsize(graphml_file)
            return True, f"Success ({size} bytes)"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def convert_batch(self, input_dir: str, output_dir: str,
                     recursive: bool = True) -> dict:
        """
        Convert all BENCH files in a directory

        Args:
            input_dir: Input directory containing .bench files
            output_dir: Output directory for .graphml files
            recursive: Whether to search subdirectories

        Returns:
            Dictionary with conversion statistics
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # Find all BENCH files
        if recursive:
            bench_files = list(input_path.rglob("*.bench"))
        else:
            bench_files = list(input_path.glob("*.bench"))

        stats = {
            'total': len(bench_files),
            'success': 0,
            'failed': 0,
            'failed_files': []
        }

        for bench_file in bench_files:
            # Preserve directory structure
            rel_path = bench_file.relative_to(input_path)
            graphml_file = output_path / rel_path.with_suffix('.graphml')

            # Convert
            success, message = self.convert(str(bench_file), str(graphml_file))

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_files'].append({
                    'file': str(bench_file),
                    'error': message
                })

        return stats


def convert_bench_to_graphml(bench_file: str, graphml_file: str) -> Tuple[bool, str]:
    """
    Convenience function to convert a single BENCH file to GraphML

    Args:
        bench_file: Path to input .bench file
        graphml_file: Path to output .graphml file

    Returns:
        Tuple of (success: bool, message: str)
    """
    converter = BenchToGraphMLConverter()
    return converter.convert(bench_file, graphml_file)
