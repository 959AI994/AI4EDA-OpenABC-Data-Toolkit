#!/usr/bin/env python3
"""
GraphML to PyTorch Geometric converter
Converts .graphml files to .pt format for PyTorch Geometric
"""

import os
from pathlib import Path
from typing import Tuple, Optional
import networkx as nx
import torch
import torch_geometric.data


# Node types mapping
NODE_TYPE = {
    0: "PI",
    1: "PO",
    2: "Internal"
}

# Edge types mapping
EDGE_TYPE = {
    1: "NOT",
    0: 'BUFF'
}


class GraphMLToPTConverter:
    """Convert GraphML files to PyTorch Geometric .pt format"""

    def __init__(self):
        """Initialize converter"""
        pass

    def graphml_to_pyg_data(self, graphml_file: str) -> torch_geometric.data.Data:
        """
        Convert GraphML file to PyTorch Geometric Data object

        Args:
            graphml_file: Path to .graphml file

        Returns:
            PyTorch Geometric Data object
        """
        # Read GraphML
        G = nx.read_graphml(graphml_file)

        # Convert to PyG Data
        G = nx.convert_node_labels_to_integers(G)
        G = G.to_directed() if not nx.is_directed(G) else G

        # Get edge index
        edge_index = torch.LongTensor(list(G.edges)).t().contiguous()

        # Extract node and edge features
        data_dict = {}
        node_count_dict = {"PI": 0, "PO": 0, "Internal": 0}
        edge_count_dict = {'BUFF': 0, 'NOT': 0}

        # Process nodes
        for i, (_, feat_dict) in enumerate(G.nodes(data=True)):
            for key, value in feat_dict.items():
                if i == 0:
                    data_dict[str(key)] = [value]
                else:
                    data_dict[str(key)].append(value)

            # Count node types
            if 'node_type' in feat_dict:
                node_type_val = int(feat_dict['node_type'])
                node_count_dict[NODE_TYPE[node_type_val]] += 1

        # Process edges
        for i, (_, _, feat_dict) in enumerate(G.edges(data=True)):
            for key, value in feat_dict.items():
                if i == 0:
                    data_dict[str(key)] = [value]
                else:
                    data_dict[str(key)].append(value)

            # Count edge types
            if 'edge_type' in feat_dict:
                edge_type_val = int(feat_dict['edge_type'])
                edge_count_dict[EDGE_TYPE[edge_type_val]] += 1

        # Calculate graph statistics
        try:
            data_dict['longest_path'] = nx.dag_longest_path_length(G)
        except:
            data_dict['longest_path'] = 0

        data_dict['and_nodes'] = node_count_dict["Internal"]
        data_dict['pi'] = node_count_dict["PI"]
        data_dict['po'] = node_count_dict["PO"]
        data_dict['not_edges'] = edge_count_dict["NOT"]

        # Convert to tensors
        for key, item in data_dict.items():
            try:
                data_dict[key] = torch.tensor(item)
            except (ValueError, TypeError):
                # Keep as-is if cannot convert to tensor
                pass

        # Set edge index
        data_dict['edge_index'] = edge_index.view(2, -1)

        # Create PyG Data object
        data = torch_geometric.data.Data.from_dict(data_dict)
        data.num_nodes = G.number_of_nodes()

        return data

    def convert(self, graphml_file: str, pt_file: str) -> Tuple[bool, str]:
        """
        Convert a single GraphML file to .pt format

        Args:
            graphml_file: Path to input .graphml file
            pt_file: Path to output .pt file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(pt_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Convert to PyG Data
            data = self.graphml_to_pyg_data(graphml_file)

            # Save as .pt file
            torch.save(data, pt_file)

            # Get file size
            size = os.path.getsize(pt_file)
            return True, f"Success ({size} bytes, {data.num_nodes} nodes)"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def convert_batch(self, input_dir: str, output_dir: str,
                     recursive: bool = True) -> dict:
        """
        Convert all GraphML files in a directory

        Args:
            input_dir: Input directory containing .graphml files
            output_dir: Output directory for .pt files
            recursive: Whether to search subdirectories

        Returns:
            Dictionary with conversion statistics
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # Find all GraphML files
        if recursive:
            graphml_files = list(input_path.rglob("*.graphml"))
        else:
            graphml_files = list(input_path.glob("*.graphml"))

        stats = {
            'total': len(graphml_files),
            'success': 0,
            'failed': 0,
            'failed_files': []
        }

        for graphml_file in graphml_files:
            # Preserve directory structure
            rel_path = graphml_file.relative_to(input_path)
            pt_file = output_path / rel_path.with_suffix('.pt')

            # Convert
            success, message = self.convert(str(graphml_file), str(pt_file))

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_files'].append({
                    'file': str(graphml_file),
                    'error': message
                })

        return stats


def convert_graphml_to_pt(graphml_file: str, pt_file: str) -> Tuple[bool, str]:
    """
    Convenience function to convert a single GraphML file to .pt format

    Args:
        graphml_file: Path to input .graphml file
        pt_file: Path to output .pt file

    Returns:
        Tuple of (success: bool, message: str)
    """
    converter = GraphMLToPTConverter()
    return converter.convert(graphml_file, pt_file)
