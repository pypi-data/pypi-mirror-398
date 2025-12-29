"""
SmartFrame Utilities

Helper functions for memory management and debugging.
"""

import sys
from typing import Any


def get_memory_size(obj: Any) -> int:
    """
    Estimate memory usage of an object in bytes.
    
    For DataFrames, uses pandas memory_usage().
    For other objects, uses sys.getsizeof().
    
    Args:
        obj: Object to measure
        
    Returns:
        Estimated size in bytes
    """
    try:
        # For pandas DataFrames
        if hasattr(obj, 'memory_usage'):
            return int(obj.memory_usage(deep=True).sum())
    except Exception:
        pass
    
    # Fallback for other objects
    return sys.getsizeof(obj)


def format_size(size_bytes: int) -> str:
    """
    Format bytes as human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string like "1.5 GB" or "256 MB"
    """
    if size_bytes < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def get_df_info(df: Any) -> dict:
    """
    Get summary info about a DataFrame.
    
    Args:
        df: DataFrame to summarize
        
    Returns:
        Dict with shape, columns, memory info
    """
    info = {
        'type': type(df).__name__,
        'memory': get_memory_size(df),
        'memory_formatted': format_size(get_memory_size(df))
    }
    
    if hasattr(df, 'shape'):
        info['rows'] = df.shape[0]
        info['columns'] = df.shape[1] if len(df.shape) > 1 else 1
    
    if hasattr(df, 'columns'):
        info['column_names'] = list(df.columns)[:10]  # First 10
        if len(df.columns) > 10:
            info['column_names'].append(f"... +{len(df.columns) - 10} more")
    
    return info
