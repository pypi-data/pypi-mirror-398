# tests/test_key_store.py

"""
Unit tests for key storage and management.
"""

import unittest
import os
import tempfile
import shutil

from core.key_store import KeyStore, save_key_to_file, load_key_from_file
from core.aes_crypto import generate_key


class TestKeyStore(unittest.TestCase):
    """Test KeyStore functionality."""
    
    def setUp(self):
        """Create temporary directory for keystore."""
        self.temp_dir = tempfile.mkdtemp()
        self.keystore_path = os.path.join(self.temp_dir, ".keystore")
        self.keystore = KeyStore(self.keystore_path)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_key(self):
        """Test saving and loading a key."""
        key, _ = generate_key(None, 32)
        key_id = "test_key_1"
        
        self.keystore.save_key(key_id, key)
        loaded_key = self.keystore.get_key(key_id)
        
        self.assertEqual(key, loaded_key)
    
    def test_save_key_with_metadata(self):
        """Test saving key with metadata."""
        key, _ = generate_key(None, 32)
        key_id = "test_key_meta"
        metadata = {"file": "test.txt", "purpose": "backup"}
        
        self.keystore.save_key(key_id, key, metadata)
        loaded_key = self.keystore.get_key(key_id)
        
        self.assertEqual(key, loaded_key)
        
        # Check metadata
        keys = self.keystore.list_keys()
        found = False
        for kid, created, meta in keys:
            if kid == key_id:
                self.assertEqual(meta, metadata)
                found = True
        
        self.assertTrue(found)
    
    def test_list_keys(self):
        """Test listing all keys."""
        keys_to_add = {
            "key1": generate_key(None, 32)[0],
            "key2": generate_key(None, 32)[0],
            "key3": generate_key(None, 16)[0]
        }
        
        for key_id, key in keys_to_add.items():
            self.keystore.save_key(key_id, key)
        
        listed_keys = self.keystore.list_keys()
        self.assertEqual(len(listed_keys), 3)
        
        listed_ids = [k[0] for k in listed_keys]
        for key_id in keys_to_add.keys():
            self.assertIn(key_id, listed_ids)
    
    def test_delete_key(self):
        """Test deleting a key."""
        key, _ = generate_key(None, 32)
        key_id = "to_delete"
        
        self.keystore.save_key(key_id, key)
        self.assertEqual(len(self.keystore.list_keys()), 1)
        
        self.keystore.delete_key(key_id)
        self.assertEqual(len(self.keystore.list_keys()), 0)
        
        with self.assertRaises(KeyError):
            self.keystore.get_key(key_id)
    
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        with self.assertRaises(KeyError):
            self.keystore.get_key("nonexistent_key")
    
    def test_persistence(self):
        """Test keystore persists to disk."""
        key, _ = generate_key(None, 32)
        key_id = "persistent_key"
        
        self.keystore.save_key(key_id, key)
        
        # Create new keystore instance
        new_keystore = KeyStore(self.keystore_path)
        loaded_key = new_keystore.get_key(key_id)
        
        self.assertEqual(key, loaded_key)
    
    def test_encrypted_keystore(self):
        """Test saving and loading encrypted keystore."""
        password = "keystore_password_123"
        key, _ = generate_key(None, 32)
        key_id = "encrypted_key"
        
        self.keystore.save_key(key_id, key)
        self.keystore.save(password)
        
        # Create new keystore and load with password
        new_keystore = KeyStore(self.keystore_path)
        new_keystore.load(password)
        
        loaded_key = new_keystore.get_key(key_id)
        self.assertEqual(key, loaded_key)
    
    def test_encrypted_keystore_wrong_password(self):
        """Test loading encrypted keystore with wrong password fails."""
        password = "correct_password"
        wrong_password = "wrong_password"
        key, _ = generate_key(None, 32)
        
        self.keystore.save_key("test", key)
        self.keystore.save(password)
        
        # Try to load with wrong password
        new_keystore = KeyStore(self.keystore_path)
        with self.assertRaises(Exception):  # Will raise decrypt/padding error
            new_keystore.load(wrong_password)


class TestKeyFile(unittest.TestCase):
    """Test standalone key file operations."""
    
    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_key_file(self):
        """Test saving and loading key from file."""
        key, _ = generate_key(None, 32)
        key_file = os.path.join(self.temp_dir, "test.key")
        
        save_key_to_file(key, key_file)
        loaded_key, metadata = load_key_from_file(key_file)
        
        self.assertEqual(key, loaded_key)
    
    def test_save_key_file_with_metadata(self):
        """Test saving key file with metadata."""
        key, _ = generate_key(None, 16)
        key_file = os.path.join(self.temp_dir, "meta.key")
        metadata = {"original_file": "data.txt", "date": "2025-01-01"}
        
        save_key_to_file(key, key_file, "meta_key", metadata)
        loaded_key, loaded_meta = load_key_from_file(key_file)
        
        self.assertEqual(key, loaded_key)
        self.assertEqual(loaded_meta, metadata)


if __name__ == '__main__':
    unittest.main()
