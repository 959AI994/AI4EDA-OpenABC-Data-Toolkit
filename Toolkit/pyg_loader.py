"""
PyG Data 加载工具 - 版本兼容性处理

用于在不同 PyG 版本之间安全加载 .pt 文件，避免版本检查错误。
"""

import torch
import pickle
from typing import Optional, Any


def extract_pyg_attr(data: Any, attr_name: str, default: Any = None) -> Any:
    """
    从 PyG Data 对象中提取属性，绕过版本检查
    
    Args:
        data: PyG Data 对象
        attr_name: 要提取的属性名
        default: 默认值（如果提取失败）
    
    Returns:
        属性值或默认值
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
            return data_dict.get(attr_name)
    except Exception:
        pass
    
    return default


def load_pyg_data_compatible(
    file_path: str,
    map_location: str = 'cpu',
    extract_attrs: Optional[list] = None
) -> Any:
    """
    兼容性加载 PyG Data 对象
    
    Args:
        file_path: .pt 文件路径
        map_location: 设备位置（'cpu' 或 'cuda'）
        extract_attrs: 可选，要提取的属性列表（如 ['node_type', 'edge_index']）
                      如果提供，返回字典而不是 Data 对象
    
    Returns:
        PyG Data 对象或属性字典
    """
    # Load with compatibility for older PyG versions
    # Use weights_only=False to allow loading old format
    data = torch.load(file_path, map_location=map_location, weights_only=False)
    
    # If extract_attrs is provided, extract specific attributes
    if extract_attrs is not None:
        result = {}
        for attr_name in extract_attrs:
            result[attr_name] = extract_pyg_attr(data, attr_name)
        return result
    
    # Return the data object as-is (may need to use extract_pyg_attr to access attributes)
    return data


def safe_get_pyg_attr(data: Any, attr_name: str, default: Any = None) -> Any:
    """
    安全地从 PyG Data 对象获取属性（兼容新旧版本）
    
    这是 extract_pyg_attr 的别名，提供更直观的命名
    
    Args:
        data: PyG Data 对象
        attr_name: 属性名
        default: 默认值
    
    Returns:
        属性值
    """
    return extract_pyg_attr(data, attr_name, default)

