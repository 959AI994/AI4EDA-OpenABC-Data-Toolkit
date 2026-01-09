#!/usr/bin/env python3
"""
PyG Version Detection and Compatibility Guide
Automatically detects PyG version and provides appropriate loader
"""

import sys


def get_pyg_version():
    """
    Get PyTorch Geometric version

    Returns:
        Tuple of (major, minor, patch) or None if PyG not found
    """
    try:
        import torch_geometric
        version_str = torch_geometric.__version__
        parts = version_str.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2].split('+')[0]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except ImportError:
        return None
    except Exception:
        return None


def is_pyg_v1():
    """Check if current environment is PyG 1.x"""
    version = get_pyg_version()
    if version is None:
        return False
    return version[0] == 1


def is_pyg_v2():
    """Check if current environment is PyG 2.x"""
    version = get_pyg_version()
    if version is None:
        return False
    return version[0] >= 2


def get_recommended_loader():
    """
    Get recommended loader module based on PyG version

    Returns:
        String indicating which loader to use
    """
    if is_pyg_v1():
        return "pyg_loader_v1"
    elif is_pyg_v2():
        return "pyg_loader"
    else:
        return "pyg_loader"  # Default to v2


def get_recommended_converter():
    """
    Get recommended converter module based on PyG version

    Returns:
        String indicating which converter to use
    """
    if is_pyg_v1():
        return "graphml_to_pt_v1"
    elif is_pyg_v2():
        return "graphml_to_pt"
    else:
        return "graphml_to_pt"  # Default to v2


def print_compatibility_info():
    """Print PyG version and compatibility information"""
    try:
        import torch
        import torch_geometric

        print("=" * 60)
        print("PyG Environment Information")
        print("=" * 60)
        print(f"PyTorch version: {torch.__version__}")
        print(f"PyG version: {torch_geometric.__version__}")

        version = get_pyg_version()
        if version:
            print(f"PyG major version: {version[0]}.x")

            if is_pyg_v1():
                print("\n✓ PyG 1.x detected")
                print("  Recommended loader: pyg_loader_v1")
                print("  Recommended converter: graphml_to_pt_v1")
                print("\n  Usage:")
                print("    from ai4eda.utils.pyg_loader_v1 import load_pyg_data_v1")
                print("    data = load_pyg_data_v1('file.pt')")
            elif is_pyg_v2():
                print("\n✓ PyG 2.x detected")
                print("  Recommended loader: pyg_loader")
                print("  Recommended converter: graphml_to_pt")
                print("\n  Usage:")
                print("    from ai4eda.utils.pyg_loader import load_pyg_data_compatible")
                print("    data = load_pyg_data_compatible('file.pt')")

        print("=" * 60)

    except ImportError as e:
        print(f"Error: {e}")
        print("PyTorch Geometric not found")


def load_pt_auto(file_path: str, map_location: str = 'cpu'):
    """
    Automatically load PT file using appropriate loader for current PyG version

    Handles all compatibility scenarios:
    - PyG 1.x loading PyG 1.x data ✓
    - PyG 1.x loading PyG 2.x data ✓ (auto-converts)
    - PyG 2.x loading PyG 1.x data ✓
    - PyG 2.x loading PyG 2.x data ✓

    Args:
        file_path: Path to .pt file
        map_location: Device location

    Returns:
        Loaded PyG Data object
    """
    if is_pyg_v1():
        # PyG 1.x environment - uses v1 loader with auto-conversion
        from ai4eda.utils.pyg_loader_v1 import load_pyg_data_v1
        return load_pyg_data_v1(file_path, map_location)
    else:
        # PyG 2.x environment - uses compatible loader
        from ai4eda.utils.pyg_loader import load_pyg_data_compatible
        return load_pyg_data_compatible(file_path, map_location)


if __name__ == '__main__':
    print_compatibility_info()
