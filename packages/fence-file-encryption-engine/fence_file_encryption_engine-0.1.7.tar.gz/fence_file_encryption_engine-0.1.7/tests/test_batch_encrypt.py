# tests/test_batch_encrypt.py

"""
Unit tests for batch encryption functionality.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

from core.batch_encrypt import BatchEncryptor, encrypt_files_batch
from core.aes_crypto import generate_key


class TestBatchEncryptor(unittest.TestCase):
    """Test batch encryption functionality."""
    
    def setUp(self):
        """Create temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_folder = os.path.join(self.temp_dir, "test_data")
        self.output_folder = os.path.join(self.temp_dir, "encrypted")
        self.decrypt_folder = os.path.join(self.temp_dir, "decrypted")
        
        # Create test folder structure
        os.makedirs(self.test_folder)
        os.makedirs(os.path.join(self.test_folder, "subfolder"))
        
        # Create test files
        self.test_files = {
            "file1.txt": b"Content of file 1\n" * 50,
            "file2.txt": b"Content of file 2\n" * 100,
            "subfolder/file3.txt": b"Content of file 3 in subfolder\n" * 75,
        }
        
        for rel_path, content in self.test_files.items():
            file_path = os.path.join(self.test_folder, rel_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(content)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def test_encrypt_folder_password(self):
        """Test encrypting folder with password."""
        password = "test_password_batch"
        encryptor = BatchEncryptor(password=password, key_size=32)
        
        metadata = encryptor.encrypt_folder(
            self.test_folder,
            self.output_folder,
            recursive=True
        )
        
        # Check encrypted files exist
        enc_files = list(Path(self.output_folder).rglob("*.enc"))
        self.assertGreater(len(enc_files), 0)
        
        # Check metadata file exists
        metadata_file = os.path.join(self.output_folder, "encryption_metadata.json")
        self.assertTrue(os.path.exists(metadata_file))
    
    def test_encrypt_decrypt_folder(self):
        """Test encrypting and decrypting folder."""
        # Use random key for this test since password-based creates different
        # salts for each file
        key, _ = generate_key(None, 32)
        
        # Encrypt
        encryptor = BatchEncryptor(key=key, key_size=32)
        encryptor.encrypt_folder(self.test_folder, self.output_folder)
        
        # Decrypt with same key
        decryptor = BatchEncryptor(key=key, key_size=32)
        count = decryptor.decrypt_folder(self.output_folder, self.decrypt_folder)
        
        self.assertGreater(count, 0)
        
        # Verify files
        for rel_path, original_content in self.test_files.items():
            decrypted_file = os.path.join(self.decrypt_folder, os.path.basename(rel_path))
            if os.path.exists(decrypted_file):
                with open(decrypted_file, 'rb') as f:
                    decrypted_content = f.read()
                self.assertEqual(decrypted_content, original_content)
    
    def test_encrypt_folder_random_key(self):
        """Test encrypting folder with random key."""
        key, _ = generate_key(None, 32)
        encryptor = BatchEncryptor(key=key, key_size=32)
        
        metadata = encryptor.encrypt_folder(
            self.test_folder,
            self.output_folder
        )
        
        # Verify encryption
        enc_files = list(Path(self.output_folder).rglob("*.enc"))
        self.assertGreater(len(enc_files), 0)
        
        # Decrypt with same key
        decryptor = BatchEncryptor(key=key, key_size=32)
        count = decryptor.decrypt_folder(self.output_folder, self.decrypt_folder)
        self.assertGreater(count, 0)
    
    def test_encrypt_folder_non_recursive(self):
        """Test encrypting folder without recursion."""
        password = "test_password"
        encryptor = BatchEncryptor(password=password, use_parallel=False)
        
        metadata = encryptor.encrypt_folder(
            self.test_folder,
            self.output_folder,
            recursive=False
        )
        
        # Should only encrypt top-level files
        enc_files = list(Path(self.output_folder).glob("*.enc"))
        self.assertEqual(len(enc_files), 2)  # file1.txt and file2.txt
    
    def test_encrypt_folder_pattern_filter(self):
        """Test encrypting folder with file pattern."""
        # Create additional non-txt file
        pdf_file = os.path.join(self.test_folder, "document.pdf")
        with open(pdf_file, 'wb') as f:
            f.write(b"PDF content")
        
        password = "pattern_test"
        encryptor = BatchEncryptor(password=password)
        
        metadata = encryptor.encrypt_folder(
            self.test_folder,
            self.output_folder,
            recursive=False,
            pattern="*.txt"
        )
        
        # Should only encrypt .txt files
        self.assertEqual(len(metadata['files']), 2)
    
    def test_encrypt_files_batch(self):
        """Test batch encryption of specific files."""
        file_paths = [
            os.path.join(self.test_folder, "file1.txt"),
            os.path.join(self.test_folder, "file2.txt")
        ]
        
        password = "batch_password"
        metadata = encrypt_files_batch(
            file_paths,
            self.output_folder,
            password=password,
            key_size=32
        )
        
        # Check encrypted files
        enc_files = list(Path(self.output_folder).glob("*.enc"))
        self.assertEqual(len(enc_files), 2)


if __name__ == '__main__':
    unittest.main()
