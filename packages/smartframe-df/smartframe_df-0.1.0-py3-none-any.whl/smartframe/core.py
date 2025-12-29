"""
SmartFrame Core

Main SmartFrame class that automatically manages DataFrame memory.
Keeps only the latest DataFrame in RAM, offloads others to disk.
"""

import gc
from typing import Optional, Dict, Any, Iterator
from collections import OrderedDict
import pandas as pd

from .storage import StorageBackend
from .utils import get_memory_size, format_size, get_df_info


class SmartFrame:
    """
    Memory-efficient DataFrame container.
    
    Automatically keeps only the most recent DataFrame in RAM,
    offloading older ones to disk. Provides transparent access
    with auto-loading from disk when needed.
    
    Example:
        >>> sf = SmartFrame()
        >>> sf['raw'] = pd.read_csv('huge.csv')       # raw in RAM
        >>> sf['filtered'] = sf['raw'].query('x > 0') # raw → disk, filtered in RAM
        >>> sf['result'] = sf['filtered'].sum()       # filtered → disk, result in RAM
        >>>
        >>> # Access old data - auto-loads from disk
        >>> print(sf['raw'].head())
        >>>
        >>> # Cleanup when done
        >>> sf.cleanup()
    """
    
    def __init__(
        self,
        storage_dir: Optional[str] = None,
        max_in_ram: int = 1,
        verbose: bool = False
    ):
        """
        Initialize SmartFrame.
        
        Args:
            storage_dir: Custom directory for temp files.
                        If None, uses system temp directory.
            max_in_ram: Maximum number of DataFrames to keep in RAM.
                       Default is 1 (only the latest).
            verbose: If True, print messages when offloading/loading.
        """
        self._storage = StorageBackend(storage_dir)
        self._max_in_ram = max_in_ram
        self._verbose = verbose
        
        # OrderedDict to track access order (most recent last)
        self._ram_cache: OrderedDict[str, pd.DataFrame] = OrderedDict()
        
        # Track which names exist (in RAM or on disk)
        self._names: set = set()
        
        # Pinned dataframes that should never be offloaded
        self._pinned: set = set()
    
    def __setitem__(self, name: str, df: pd.DataFrame) -> None:
        """
        Store a DataFrame.
        
        The new DataFrame is kept in RAM. If this exceeds max_in_ram,
        the oldest unpinned DataFrame is offloaded to disk.
        
        Args:
            name: Identifier for the dataframe
            df: DataFrame to store
        """
        # If name already exists, remove old version
        if name in self._names:
            self._remove_from_ram(name)
            self._storage.delete(name)
        
        # Add to RAM cache
        self._ram_cache[name] = df
        self._ram_cache.move_to_end(name)  # Mark as most recently used
        self._names.add(name)
        
        if self._verbose:
            size = format_size(get_memory_size(df))
            print(f"📥 Stored '{name}' in RAM ({size})")
        
        # Offload excess to disk
        self._enforce_ram_limit()
    
    def __getitem__(self, name: str) -> pd.DataFrame:
        """
        Get a DataFrame by name.
        
        If the DataFrame is in RAM, returns it directly.
        If it's on disk, loads it transparently.
        
        Args:
            name: Identifier for the dataframe
            
        Returns:
            The requested DataFrame
            
        Raises:
            KeyError: If name not found
        """
        if name not in self._names:
            raise KeyError(f"'{name}' not found in SmartFrame")
        
        # If in RAM, mark as recently used and return
        if name in self._ram_cache:
            self._ram_cache.move_to_end(name)
            return self._ram_cache[name]
        
        # Load from disk
        if self._verbose:
            print(f"💾 Loading '{name}' from disk...")
        
        df = self._storage.load(name)
        
        # Optionally bring back to RAM cache
        # (commented out to keep behavior simple - only latest in RAM)
        # self._ram_cache[name] = df
        # self._enforce_ram_limit()
        
        return df
    
    def __delitem__(self, name: str) -> None:
        """
        Delete a DataFrame from SmartFrame.
        
        Removes from both RAM and disk.
        
        Args:
            name: Identifier for the dataframe
        """
        if name not in self._names:
            raise KeyError(f"'{name}' not found in SmartFrame")
        
        self._remove_from_ram(name)
        self._storage.delete(name)
        self._names.discard(name)
        self._pinned.discard(name)
        
        if self._verbose:
            print(f"🗑️  Deleted '{name}'")
    
    def __contains__(self, name: str) -> bool:
        """Check if a name exists in SmartFrame."""
        return name in self._names
    
    def __len__(self) -> int:
        """Return number of stored DataFrames."""
        return len(self._names)
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over DataFrame names."""
        return iter(self._names)
    
    def keys(self) -> list:
        """Return list of all DataFrame names."""
        return list(self._names)
    
    def _remove_from_ram(self, name: str) -> None:
        """Remove a DataFrame from RAM cache."""
        if name in self._ram_cache:
            del self._ram_cache[name]
            gc.collect()  # Help free memory
    
    def _enforce_ram_limit(self) -> None:
        """Offload oldest DataFrames to disk if over limit."""
        while len(self._ram_cache) > self._max_in_ram:
            # Find oldest non-pinned item
            to_offload = None
            for name in self._ram_cache:
                if name not in self._pinned:
                    to_offload = name
                    break
            
            if to_offload is None:
                # All items are pinned, can't offload
                break
            
            # Save to disk and remove from RAM
            df = self._ram_cache[to_offload]
            self._storage.save(to_offload, df)
            
            if self._verbose:
                size = format_size(get_memory_size(df))
                print(f"💾 Offloaded '{to_offload}' to disk ({size})")
            
            del self._ram_cache[to_offload]
            gc.collect()
    
    def pin(self, name: str) -> None:
        """
        Pin a DataFrame to keep it in RAM permanently.
        
        Pinned DataFrames are never offloaded to disk.
        Use this for DataFrames you access frequently.
        
        Args:
            name: Name of DataFrame to pin
        """
        if name not in self._names:
            raise KeyError(f"'{name}' not found in SmartFrame")
        
        self._pinned.add(name)
        
        # If it's on disk, load it back to RAM
        if name not in self._ram_cache and self._storage.exists(name):
            self._ram_cache[name] = self._storage.load(name)
            self._storage.delete(name)
        
        if self._verbose:
            print(f"📌 Pinned '{name}' to RAM")
    
    def unpin(self, name: str) -> None:
        """
        Unpin a DataFrame, allowing it to be offloaded.
        
        Args:
            name: Name of DataFrame to unpin
        """
        self._pinned.discard(name)
        self._enforce_ram_limit()
        
        if self._verbose:
            print(f"📌 Unpinned '{name}'")
    
    def status(self) -> None:
        """
        Print status of all DataFrames showing RAM vs disk location.
        
        Displays a table showing:
        - Name
        - Location (RAM/Disk)
        - Size
        - Shape (rows × columns)
        """
        print("\n" + "=" * 60)
        print("📊 SmartFrame Status")
        print("=" * 60)
        
        total_ram = 0
        total_disk = 0
        
        print(f"{'Name':<20} {'Location':<10} {'Size':<12} {'Shape':<15}")
        print("-" * 60)
        
        for name in sorted(self._names):
            if name in self._ram_cache:
                location = "🟢 RAM"
                if name in self._pinned:
                    location += " 📌"
                df = self._ram_cache[name]
                size = get_memory_size(df)
                total_ram += size
                shape = f"{df.shape[0]:,} × {df.shape[1]}"
            else:
                location = "💾 Disk"
                size = self._storage.get_size(name)
                total_disk += size
                shape = "(load to see)"
            
            print(f"{name:<20} {location:<10} {format_size(size):<12} {shape:<15}")
        
        print("-" * 60)
        print(f"Total RAM:  {format_size(total_ram)}")
        print(f"Total Disk: {format_size(total_disk)}")
        print(f"Storage:    {self._storage.storage_dir}")
        print("=" * 60 + "\n")
    
    def cleanup(self) -> None:
        """
        Delete all stored data and temp files.
        
        Clears all DataFrames from RAM and disk.
        Call this when you're done with the SmartFrame.
        """
        count_ram = len(self._ram_cache)
        count_disk = self._storage.cleanup()
        
        self._ram_cache.clear()
        self._names.clear()
        self._pinned.clear()
        gc.collect()
        
        if self._verbose or True:  # Always print cleanup summary
            print(f"🧹 Cleanup complete: {count_ram} from RAM, {count_disk} from disk")
    
    def to_dict(self) -> Dict[str, pd.DataFrame]:
        """
        Load all DataFrames into a regular dict.
        
        Warning: This loads everything into RAM!
        
        Returns:
            Dict mapping names to DataFrames
        """
        return {name: self[name] for name in self._names}
    
    def __repr__(self) -> str:
        ram_count = len(self._ram_cache)
        disk_count = len(self._names) - ram_count
        return f"SmartFrame({ram_count} in RAM, {disk_count} on disk)"
