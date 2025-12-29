"""
SmartFrame Unit Tests
"""

import os
import sys
import tempfile
import unittest

import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartframe import SmartFrame, StorageBackend, get_memory_size, format_size


class TestStorageBackend(unittest.TestCase):
    """Test the storage backend."""
    
    def setUp(self):
        self.storage = StorageBackend()
        self.df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': ['x', 'y', 'z']
        })
    
    def tearDown(self):
        self.storage.cleanup()
    
    def test_save_and_load(self):
        """Test saving and loading a DataFrame."""
        self.storage.save('test', self.df)
        loaded = self.storage.load('test')
        pd.testing.assert_frame_equal(self.df, loaded)
    
    def test_delete(self):
        """Test deleting a stored DataFrame."""
        self.storage.save('test', self.df)
        self.assertTrue(self.storage.exists('test'))
        self.storage.delete('test')
        self.assertFalse(self.storage.exists('test'))
    
    def test_list_stored(self):
        """Test listing stored DataFrames."""
        self.storage.save('df1', self.df)
        self.storage.save('df2', self.df)
        stored = self.storage.list_stored()
        self.assertEqual(set(stored), {'df1', 'df2'})
    
    def test_cleanup(self):
        """Test cleanup removes all files."""
        self.storage.save('df1', self.df)
        self.storage.save('df2', self.df)
        count = self.storage.cleanup()
        self.assertEqual(count, 2)
        self.assertEqual(len(self.storage.list_stored()), 0)


class TestSmartFrame(unittest.TestCase):
    """Test the main SmartFrame class."""
    
    def setUp(self):
        self.sf = SmartFrame(verbose=False)
        self.df1 = pd.DataFrame({'a': range(100), 'b': range(100)})
        self.df2 = pd.DataFrame({'x': range(50), 'y': range(50)})
        self.df3 = pd.DataFrame({'p': range(25), 'q': range(25)})
    
    def tearDown(self):
        self.sf.cleanup()
    
    def test_store_and_retrieve(self):
        """Test basic store and retrieve."""
        self.sf['data'] = self.df1
        pd.testing.assert_frame_equal(self.sf['data'], self.df1)
    
    def test_offload_to_disk(self):
        """Test that old DataFrames are offloaded to disk."""
        self.sf['first'] = self.df1
        self.sf['second'] = self.df2
        
        # 'first' should be on disk, 'second' in RAM
        self.assertNotIn('first', self.sf._ram_cache)
        self.assertIn('second', self.sf._ram_cache)
    
    def test_auto_load_from_disk(self):
        """Test that accessing offloaded data loads it."""
        self.sf['first'] = self.df1
        self.sf['second'] = self.df2
        
        # Access 'first' - should load from disk
        loaded = self.sf['first']
        pd.testing.assert_frame_equal(loaded, self.df1)
    
    def test_delete(self):
        """Test deleting a DataFrame."""
        self.sf['data'] = self.df1
        del self.sf['data']
        self.assertNotIn('data', self.sf)
    
    def test_contains(self):
        """Test 'in' operator."""
        self.sf['data'] = self.df1
        self.assertIn('data', self.sf)
        self.assertNotIn('other', self.sf)
    
    def test_len(self):
        """Test len()."""
        self.assertEqual(len(self.sf), 0)
        self.sf['a'] = self.df1
        self.sf['b'] = self.df2
        self.assertEqual(len(self.sf), 2)
    
    def test_keys(self):
        """Test keys() method."""
        self.sf['a'] = self.df1
        self.sf['b'] = self.df2
        self.assertEqual(set(self.sf.keys()), {'a', 'b'})
    
    def test_pin(self):
        """Test pinning a DataFrame."""
        self.sf['first'] = self.df1
        self.sf.pin('first')
        self.sf['second'] = self.df2
        
        # 'first' should still be in RAM (pinned)
        self.assertIn('first', self.sf._ram_cache)
    
    def test_overwrite(self):
        """Test overwriting an existing DataFrame."""
        self.sf['data'] = self.df1
        self.sf['data'] = self.df2
        pd.testing.assert_frame_equal(self.sf['data'], self.df2)
    
    def test_max_in_ram(self):
        """Test max_in_ram parameter."""
        sf = SmartFrame(max_in_ram=2, verbose=False)
        sf['a'] = self.df1
        sf['b'] = self.df2
        sf['c'] = self.df3
        
        # Only 2 should be in RAM
        self.assertEqual(len(sf._ram_cache), 2)
        
        # 'a' should be on disk
        self.assertNotIn('a', sf._ram_cache)
        
        sf.cleanup()


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_format_size(self):
        """Test size formatting."""
        self.assertEqual(format_size(500), "500 B")
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1024 * 1024), "1.00 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.00 GB")
    
    def test_get_memory_size(self):
        """Test memory size estimation."""
        df = pd.DataFrame({'a': range(1000)})
        size = get_memory_size(df)
        self.assertGreater(size, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
