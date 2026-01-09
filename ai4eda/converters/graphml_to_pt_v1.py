#!/usr/bin/env python3
"""
GraphML to PyTorch Geometric converter for PyG 1.x
Generates PT files compatible with PyG 1.x versions
Use this in PyG 1.x environments (e.g., openabc)
"""

import os
from pathlib import Path
from typing import Tuple
import networkx as nx
import torch

try:
    from torch_geometric.data import Data
except ImportError:
    # Fallback for very old PyG versions
    import torch_geometric
    Data = torch_geometric.data.Data


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


class GraphMLToPTV1Converter:
    """Convert GraphML files to PyG 1.x compatible PT format"""

    def __init__(self):
        """Initialize converter"""
        pass

    def graphml_to_pyg_data_v1(self, graphml_file: str) -> Data:
        """
        Convert GraphML file to PyG 1.x Data object

        Args:
            graphml_file: Path to .graphml file

        Returns:
            PyTorch Geometric Data object (PyG 1.x format)
        """
        # Read GraphML
        G = nx.read_graphml(graphml_file)

        # Convert to PyG Data (simple format for PyG 1.x)
        G = nx.convert_node_labels_to_integers(G)
        G = G.to_directed() if not nx.is_directed(G) else G

        # Get edge index
        edge_list = list(G.edges)
        if len(edge_list) > 0:
            edge_index = torch.LongTensor(edge_list).t().contiguous()
        else:
            edge_index = torch.LongTensor([[], []])

        # Extract features as simple tensors (PyG 1.x style)
        data_dict = {}

        # Process nodes
        node_type_list = []
        node_id_list = []
        num_inverted_pred_list = []

        for i, (node_id, feat_dict) in enumerate(G.nodes(data=True)):
            if 'node_type' in feat_dict:
                node_type_list.append(int(feat_dict['node_type']))
            if 'node_id' in feat_dict:
                node_id_list.append(str(feat_dict['node_id']))
            if 'num_inverted_predecessors' in feat_dict:
                num_inverted_pred_list.append(int(feat_dict['num_inverted_predecessors']))

        # Convert to tensors
        if node_type_list:
            data_dict['node_type'] = torch.tensor(node_type_list, dtype=torch.long)
        if num_inverted_pred_list:
            data_dict['num_inverted_predecessors'] = torch.tensor(num_inverted_pred_list, dtype=torch.long)

        # Process edges
        edge_type_list = []
        for i, (_, _, feat_dict) in enumerate(G.edges(data=True)):
            if 'edge_type' in feat_dict:
                edge_type_list.append(int(feat_dict['edge_type']))

        if edge_type_list:
            data_dict['edge_type'] = torch.tensor(edge_type_list, dtype=torch.long)

        # Calculate graph statistics
        node_count_dict = {"PI": 0, "PO": 0, "Internal": 0}
        edge_count_dict = {'BUFF': 0, 'NOT': 0}

        for node_type_val in node_type_list:
            if node_type_val in NODE_TYPE:
                node_count_dict[NODE_TYPE[node_type_val]] += 1

        for edge_type_val in edge_type_list:
            if edge_type_val in EDGE_TYPE:
                edge_count_dict[EDGE_TYPE[edge_type_val]] += 1

        # Add graph-level features
        try:
            data_dict['longest_path'] = torch.tensor([nx.dag_longest_path_length(G)], dtype=torch.long)
        except:
            data_dict['longest_path'] = torch.tensor([0], dtype=torch.long)

        data_dict['and_nodes'] = torch.tensor([node_count_dict["Internal"]], dtype=torch.long)
        data_dict['pi'] = torch.tensor([node_count_dict["PI"]], dtype=torch.long)
        data_dict['po'] = torch.tensor([node_count_dict["PO"]], dtype=torch.long)
        data_dict['not_edges'] = torch.tensor([edge_count_dict["NOT"]], dtype=torch.long)

        # Set edge index
        data_dict['edge_index'] = edge_index

        # Create PyG Data object (PyG 1.x compatible)
        data = Data(**data_dict)
        data.num_nodes = G.number_of_nodes()

        return data

    def convert(self, graphml_file: str, pt_file: str) -> Tuple[bool, str]:
        """
        Convert a single GraphML file to PyG 1.x compatible .pt format

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
            data = self.graphml_to_pyg_data_v1(graphml_file)

            # Save as .pt file (protocol 4 for compatibility)
            torch.save(data, pt_file, pickle_protocol=4)

            # Get file size
            size = os.path.getsize(pt_file)
            return True, f"Success ({size} bytes, {data.num_nodes} nodes, PyG 1.x format)"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def convert_batch(self, input_dir: str, output_dir: str,
                     recursive: bool = True) -> dict:
        """
        Convert all GraphML files in a directory to PyG 1.x format

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


def convert_graphml_to_pt_v1(graphml_file: str, pt_file: str) -> Tuple[bool, str]:
    """
    Convenience function to convert GraphML to PyG 1.x compatible PT format

    Args:
        graphml_file: Path to input .graphml file
        pt_file: Path to output .pt file

    Returns:
        Tuple of (success: bool, message: str)
    """
    converter = GraphMLToPTV1Converter()
    return converter.convert(graphml_file, pt_file)
