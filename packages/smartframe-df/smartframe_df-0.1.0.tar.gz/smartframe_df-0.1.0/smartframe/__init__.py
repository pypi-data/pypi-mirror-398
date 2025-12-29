"""
SmartFrame - Memory-Efficient DataFrame Management

Automatically manages RAM by keeping only the latest DataFrame in memory,
offloading older ones to disk, and providing transparent access with auto-loading.

Example:
    >>> from smartframe import SmartFrame
    >>> 
    >>> sf = SmartFrame()
    >>> sf['raw'] = pd.read_csv('huge.csv')       # raw in RAM
    >>> sf['filtered'] = sf['raw'].query('x > 0') # raw → disk, filtered in RAM
    >>> sf['result'] = sf['filtered'].sum()       # filtered → disk, result in RAM
    >>>
    >>> # Access old data - auto-loads from disk
    >>> print(sf['raw'].head())
    >>>
    >>> # See what's where
    >>> sf.status()
    >>>
    >>> # Cleanup when done
    >>> sf.cleanup()
"""

from .core import SmartFrame
from .storage import StorageBackend
from .utils import get_memory_size, format_size, get_df_info

__version__ = "0.1.0"
__author__ = "SmartFrame"

__all__ = [
    "SmartFrame",
    "StorageBackend", 
    "get_memory_size",
    "format_size",
    "get_df_info",
]
