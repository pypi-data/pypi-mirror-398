# tests/test_aes_crypto.py

"""
Unit tests for core AES encryption/decryption functionality.
"""

import unittest
import os
import tempfile
from pathlib import Path

from core.aes_crypto import (
    pad, unpad, generate_key, encrypt_file, decrypt_file,
    compute_hmac, verify_hmac, secure_delete
)


class TestPadding(unittest.TestCase):
    """Test PKCS7 padding functions."""
    
    def test_pad_single_block(self):
        """Test padding data less than block size."""
        data = b"Hello"
        padded = pad(data)
        self.assertEqual(len(padded) % 16, 0)
        self.assertEqual(unpad(padded), data)
    
    def test_pad_exact_block(self):
        """Test padding data exactly one block size."""
        data = b"A" * 16
        padded = pad(data)
        self.assertEqual(len(padded), 32)  # Should add full block of padding
        self.assertEqual(unpad(padded), data)
    
    def test_pad_multiple_blocks(self):
        """Test padding data spanning multiple blocks."""
        data = b"B" * 25
        padded = pad(data)
        self.assertEqual(len(padded) % 16, 0)
        self.assertEqual(unpad(padded), data)
    
    def test_unpad_invalid_padding(self):
        """Test unpad raises error for invalid padding."""
        invalid_data = b"Hello" + b"\x10" * 11  # Invalid padding
        with self.assertRaises(ValueError):
            unpad(invalid_data)
    
    def test_unpad_empty_data(self):
        """Test unpad raises error for empty data."""
        with self.assertRaises(ValueError):
            unpad(b"")


class TestKeyGeneration(unittest.TestCase):
    """Test key generation functions."""
    
    def test_random_key_128(self):
        """Test random AES-128 key generation."""
        key, salt = generate_key(None, 16)
        self.assertEqual(len(key), 16)
        self.assertIsNone(salt)
    
    def test_random_key_256(self):
        """Test random AES-256 key generation."""
        key, salt = generate_key(None, 32)
        self.assertEqual(len(key), 32)
        self.assertIsNone(salt)
    
    def test_password_key_128(self):
        """Test password-based AES-128 key derivation."""
        password = "test_password_123"
        key, salt = generate_key(password, 16)
        self.assertEqual(len(key), 16)
        self.assertEqual(len(salt), 16)
    
    def test_password_key_256(self):
        """Test password-based AES-256 key derivation."""
        password = "test_password_456"
        key, salt = generate_key(password, 32)
        self.assertEqual(len(key), 32)
        self.assertEqual(len(salt), 16)
    
    def test_password_key_deterministic(self):
        """Test same password and salt produce same key."""
        password = "my_secure_password"
        key1, salt = generate_key(password, 32)
        
        # Simulate using same salt
        from Crypto.Protocol.KDF import PBKDF2
        key2 = PBKDF2(password, salt, dkLen=32, count=100000)
        
        self.assertEqual(key1, key2)
    
    def test_different_passwords_different_keys(self):
        """Test different passwords produce different keys."""
        key1, _ = generate_key("password1", 32)
        key2, _ = generate_key("password2", 32)
        self.assertNotEqual(key1, key2)


class TestHMAC(unittest.TestCase):
    """Test HMAC authentication functions."""
    
    def test_compute_hmac(self):
        """Test HMAC computation."""
        key = b"secret_key_12345" * 2
        data = b"test data for hmac"
        
        hmac_value = compute_hmac(key, data)
        self.assertEqual(len(hmac_value), 32)  # SHA256 produces 32 bytes
    
    def test_verify_hmac_valid(self):
        """Test HMAC verification with valid HMAC."""
        key = b"another_secret_key_abcdef_123456"
        data = b"important message"
        
        hmac_value = compute_hmac(key, data)
        self.assertTrue(verify_hmac(key, data, hmac_value))
    
    def test_verify_hmac_invalid(self):
        """Test HMAC verification with tampered data."""
        key = b"key_for_testing_hmac_validation"
        data = b"original data"
        
        hmac_value = compute_hmac(key, data)
        
        # Tamper with data
        tampered_data = b"tampered data"
        self.assertFalse(verify_hmac(key, tampered_data, hmac_value))
    
    def test_verify_hmac_wrong_key(self):
        """Test HMAC verification with wrong key."""
        key1 = b"correct_key_1234567890abcdefgh"
        key2 = b"wrong_key___0987654321hgfedcba"
        data = b"secure message"
        
        hmac_value = compute_hmac(key1, data)
        self.assertFalse(verify_hmac(key2, data, hmac_value))


class TestFileEncryption(unittest.TestCase):
    """Test file encryption and decryption."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        self.encrypted_file = os.path.join(self.temp_dir, "test.txt.enc")
        self.decrypted_file = os.path.join(self.temp_dir, "test.txt.dec")
        
        # Create test file
        self.test_data = b"This is a test file for encryption.\nIt has multiple lines.\n" * 100
        with open(self.test_file, 'wb') as f:
            f.write(self.test_data)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_encrypt_decrypt_password(self):
        """Test encryption and decryption with password."""
        password = "test_password_secure_123"
        key, salt = generate_key(password, 32)
        
        # Encrypt
        encrypt_file(self.test_file, self.encrypted_file, key, salt=salt)
        self.assertTrue(os.path.exists(self.encrypted_file))
        
        # Decrypt
        decrypt_file(self.encrypted_file, self.decrypted_file, password=password, key_size=32)
        
        # Verify
        with open(self.decrypted_file, 'rb') as f:
            decrypted_data = f.read()
        
        self.assertEqual(decrypted_data, self.test_data)
    
    def test_encrypt_decrypt_random_key(self):
        """Test encryption and decryption with random key."""
        key, salt = generate_key(None, 32)
        
        # Encrypt
        encrypt_file(self.test_file, self.encrypted_file, key)
        
        # Decrypt
        decrypt_file(self.encrypted_file, self.decrypted_file, key=key, key_size=32)
        
        # Verify
        with open(self.decrypted_file, 'rb') as f:
            decrypted_data = f.read()
        
        self.assertEqual(decrypted_data, self.test_data)
    
    def test_encrypt_decrypt_no_hmac(self):
        """Test encryption and decryption without HMAC."""
        password = "password_no_hmac"
        key, salt = generate_key(password, 32)
        
        # Encrypt without HMAC
        encrypt_file(self.test_file, self.encrypted_file, key, salt=salt, use_hmac=False)
        
        # Decrypt without HMAC
        decrypt_file(self.encrypted_file, self.decrypted_file, password=password, 
                    key_size=32, use_hmac=False)
        
        # Verify
        with open(self.decrypted_file, 'rb') as f:
            decrypted_data = f.read()
        
        self.assertEqual(decrypted_data, self.test_data)
    
    def test_decrypt_wrong_password(self):
        """Test decryption fails with wrong password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        
        key, salt = generate_key(password, 32)
        encrypt_file(self.test_file, self.encrypted_file, key, salt=salt)
        
        # Try to decrypt with wrong password - should fail
        with self.assertRaises(ValueError):
            decrypt_file(self.encrypted_file, self.decrypted_file, 
                        password=wrong_password, key_size=32)
    
    def test_tampered_file_detected(self):
        """Test HMAC detects tampered encrypted file."""
        password = "secure_password"
        key, salt = generate_key(password, 32)
        
        # Encrypt with HMAC
        encrypt_file(self.test_file, self.encrypted_file, key, salt=salt, use_hmac=True)
        
        # Tamper with encrypted file
        with open(self.encrypted_file, 'r+b') as f:
            f.seek(-10, 2)  # Go to near end
            f.write(b"TAMPERED!!")
        
        # Try to decrypt - should fail HMAC verification
        with self.assertRaises(ValueError) as context:
            decrypt_file(self.encrypted_file, self.decrypted_file, 
                        password=password, key_size=32, use_hmac=True)
        
        self.assertIn("HMAC", str(context.exception))


class TestSecureDelete(unittest.TestCase):
    """Test secure file deletion."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_secure_delete_file(self):
        """Test secure deletion of a file."""
        test_file = os.path.join(self.temp_dir, "to_delete.txt")
        
        # Create test file
        with open(test_file, 'w') as f:
            f.write("Sensitive data to be deleted\n" * 100)
        
        self.assertTrue(os.path.exists(test_file))
        
        # Securely delete
        secure_delete(test_file)
        
        # Verify file is deleted
        self.assertFalse(os.path.exists(test_file))
    
    def test_secure_delete_nonexistent(self):
        """Test secure delete on non-existent file doesn't raise error."""
        nonexistent = os.path.join(self.temp_dir, "does_not_exist.txt")
        
        # Should not raise error
        secure_delete(nonexistent)


if __name__ == '__main__':
    unittest.main()
