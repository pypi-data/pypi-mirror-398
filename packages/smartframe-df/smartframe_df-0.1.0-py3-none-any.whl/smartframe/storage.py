"""
SmartFrame Storage Backend

Handles saving/loading DataFrames to/from disk using Parquet format.
Falls back to Pickle for non-standard data types.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd


class StorageBackend:
    """Manages disk storage for offloaded DataFrames."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize storage backend.
        
        Args:
            storage_dir: Custom directory for temp files. 
                        If None, uses system temp directory.
        """
        if storage_dir:
            self._storage_dir = Path(storage_dir)
            self._storage_dir.mkdir(parents=True, exist_ok=True)
            self._is_temp = False
        else:
            self._storage_dir = Path(tempfile.mkdtemp(prefix="smartframe_"))
            self._is_temp = True
        
        self._files: Dict[str, Path] = {}  # name -> file path
    
    @property
    def storage_dir(self) -> Path:
        """Get the storage directory path."""
        return self._storage_dir
    
    def save(self, name: str, df: pd.DataFrame) -> Path:
        """
        Save DataFrame to disk.
        
        Args:
            name: Identifier for the dataframe
            df: DataFrame to save
            
        Returns:
            Path to saved file
        """
        # Try Parquet first (fast, compressed)
        file_path = self._storage_dir / f"{name}.parquet"
        
        try:
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')
        except Exception:
            # Fallback to pickle for complex data types
            file_path = self._storage_dir / f"{name}.pkl"
            df.to_pickle(file_path)
        
        self._files[name] = file_path
        return file_path
    
    def load(self, name: str) -> pd.DataFrame:
        """
        Load DataFrame from disk.
        
        Args:
            name: Identifier for the dataframe
            
        Returns:
            Loaded DataFrame
            
        Raises:
            KeyError: If name not found in storage
        """
        if name not in self._files:
            raise KeyError(f"'{name}' not found in storage")
        
        file_path = self._files[name]
        
        if file_path.suffix == '.parquet':
            return pd.read_parquet(file_path)
        else:
            return pd.read_pickle(file_path)
    
    def delete(self, name: str) -> bool:
        """
        Delete a specific file from storage.
        
        Args:
            name: Identifier for the dataframe
            
        Returns:
            True if deleted, False if not found
        """
        if name not in self._files:
            return False
        
        file_path = self._files[name]
        if file_path.exists():
            file_path.unlink()
        
        del self._files[name]
        return True
    
    def exists(self, name: str) -> bool:
        """Check if a dataframe exists in storage."""
        return name in self._files
    
    def list_stored(self) -> list:
        """List all stored dataframe names."""
        return list(self._files.keys())
    
    def get_size(self, name: str) -> int:
        """Get file size in bytes for a stored dataframe."""
        if name not in self._files:
            return 0
        return self._files[name].stat().st_size
    
    def cleanup(self) -> int:
        """
        Delete all stored files and the temp directory.
        
        Returns:
            Number of files deleted
        """
        count = len(self._files)
        
        # Delete all tracked files
        for file_path in self._files.values():
            if file_path.exists():
                file_path.unlink()
        
        self._files.clear()
        
        # Remove temp directory if we created it
        if self._is_temp and self._storage_dir.exists():
            shutil.rmtree(self._storage_dir, ignore_errors=True)
        
        return count
    
    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during cleanup
