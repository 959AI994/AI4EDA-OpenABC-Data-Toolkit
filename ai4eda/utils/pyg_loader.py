#!/usr/bin/env python3
"""
PyTorch Geometric Data Loader with Version Compatibility
Supports loading .pt files across different PyG versions
"""

import torch
import pickle
from typing import Optional, Any, List


def extract_pyg_attr(data: Any, attr_name: str, default: Any = None) -> Any:
    """
    Extract attribute from PyG Data object, bypassing version checks

    Args:
        data: PyG Data object
        attr_name: Attribute name to extract
        default: Default value if extraction fails

    Returns:
        Attribute value or default value
    """
    # Method 1: Direct access to _store._mapping (internal dict, bypasses version check)
    try:
        if hasattr(data, '_store'):
            store = data._store
            if hasattr(store, '_mapping'):
                mapping = store._mapping
                if attr_name in mapping:
                    return mapping[attr_name]
    except Exception:
        pass

    # Method 2: Use pickle to convert format (bypasses version check completely)
    try:
        # Re-serialize and deserialize to convert format
        pickled = pickle.dumps(data, protocol=4)
        unpickled = pickle.loads(pickled)
        # Try _mapping on unpickled
        if hasattr(unpickled, '_store') and hasattr(unpickled._store, '_mapping'):
            mapping = unpickled._store._mapping
            if attr_name in mapping:
                return mapping[attr_name]
        # Try __dict__ on unpickled
        if hasattr(unpickled, '__dict__') and attr_name in unpickled.__dict__:
            return unpickled.__dict__[attr_name]
    except Exception:
        pass

    # Method 3: Try __dict__ access (old PyG format)
    try:
        if hasattr(data, '__dict__'):
            d = data.__dict__
            if attr_name in d:
                return d[attr_name]
    except Exception:
        pass

    # Method 4: Try to_dict() if available (new PyG)
    try:
        if hasattr(data, 'to_dict'):
            data_dict = data.to_dict()
            return data_dict.get(attr_name, default)
    except Exception:
        pass

    # Method 5: Try direct attribute access
    try:
        return getattr(data, attr_name)
    except Exception:
        pass

    return default


def load_pyg_data_compatible(
    file_path: str,
    map_location: str = 'cpu',
    extract_attrs: Optional[List[str]] = None
) -> Any:
    """
    Load PyG Data object with compatibility across versions

    Args:
        file_path: Path to .pt file
        map_location: Device location ('cpu' or 'cuda')
        extract_attrs: Optional list of attributes to extract
                      If provided, returns dict instead of Data object

    Returns:
        PyG Data object or attribute dictionary
    """
    # Load with compatibility for older PyG versions
    # Use weights_only=False to allow loading old format
    try:
        data = torch.load(file_path, map_location=map_location, weights_only=False)
    except TypeError:
        # Older PyTorch versions don't have weights_only parameter
        data = torch.load(file_path, map_location=map_location)

    # If extract_attrs is provided, extract specific attributes
    if extract_attrs is not None:
        result = {}
        for attr_name in extract_attrs:
            result[attr_name] = extract_pyg_attr(data, attr_name)
        return result

    # Return the data object as-is
    return data


def safe_get_pyg_attr(data: Any, attr_name: str, default: Any = None) -> Any:
    """
    Safely get attribute from PyG Data object (compatible with old/new versions)

    This is an alias for extract_pyg_attr with more intuitive naming

    Args:
        data: PyG Data object
        attr_name: Attribute name
        default: Default value

    Returns:
        Attribute value
    """
    return extract_pyg_attr(data, attr_name, default)


def list_pyg_attributes(data: Any) -> List[str]:
    """
    List all available attributes in a PyG Data object

    Args:
        data: PyG Data object

    Returns:
        List of attribute names
    """
    attrs = []

    # Try _store._mapping
    try:
        if hasattr(data, '_store') and hasattr(data._store, '_mapping'):
            attrs.extend(data._store._mapping.keys())
    except Exception:
        pass

    # Try __dict__
    try:
        if hasattr(data, '__dict__'):
            attrs.extend(data.__dict__.keys())
    except Exception:
        pass

    # Try to_dict()
    try:
        if hasattr(data, 'to_dict'):
            attrs.extend(data.to_dict().keys())
    except Exception:
        pass

    # Remove duplicates and internal attributes
    attrs = list(set(attrs))
    attrs = [a for a in attrs if not a.startswith('_')]

    return sorted(attrs)
