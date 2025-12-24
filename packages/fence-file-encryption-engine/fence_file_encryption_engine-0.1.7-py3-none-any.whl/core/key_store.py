# core/key_store.py

"""
Secure key storage and management module.
Stores encryption keys securely, optionally encrypted with a master password.
"""

import os
import json
import base64
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256

class KeyStore:
    """Manages secure storage of encryption keys."""
    
    def __init__(self, keystore_path=".keystore"):
        """
        Initialize KeyStore.
        
        Args:
            keystore_path: Path to keystore file
        """
        self.keystore_path = keystore_path
        self.keys = {}
        
        if os.path.exists(keystore_path):
            try:
                self.load()
            except ValueError:
                # Keystore exists but is encrypted, skip auto-load
                pass
    
    def save_key(self, key_id: str, key: bytes, metadata: dict = None):
        """
        Save a key to the keystore.
        
        Args:
            key_id: Unique identifier for the key
            key: The encryption key (bytes)
            metadata: Optional metadata (e.g., file associations, creation date)
        """
        self.keys[key_id] = {
            'key': base64.b64encode(key).decode('utf-8'),
            'created': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.save()
    
    def get_key(self, key_id: str) -> bytes:
        """
        Retrieve a key from the keystore.
        
        Args:
            key_id: Unique identifier for the key
        
        Returns:
            The encryption key as bytes
        
        Raises:
            KeyError: If key_id not found
        """
        if key_id not in self.keys:
            raise KeyError(f"Key '{key_id}' not found in keystore")
        
        return base64.b64decode(self.keys[key_id]['key'])
    
    def list_keys(self) -> list:
        """
        List all stored key IDs with metadata.
        
        Returns:
            List of tuples: (key_id, created_date, metadata)
        """
        return [
            (key_id, info['created'], info['metadata'])
            for key_id, info in self.keys.items()
        ]
    
    def delete_key(self, key_id: str):
        """Delete a key from the keystore."""
        if key_id in self.keys:
            del self.keys[key_id]
            self.save()
    
    def save(self, password: str = None):
        """
        Save keystore to disk.
        
        Args:
            password: Optional password to encrypt the keystore
        """
        data = json.dumps(self.keys, indent=2)
        
        if password:
            # Encrypt keystore with password
            salt = get_random_bytes(16)
            key = PBKDF2(password, salt, dkLen=32, count=100000)
            iv = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # Pad data
            padding_length = 16 - len(data) % 16
            padded_data = data.encode('utf-8') + bytes([padding_length] * padding_length)
            
            encrypted = cipher.encrypt(padded_data)
            
            # Save encrypted format
            with open(self.keystore_path, 'wb') as f:
                f.write(b'ENCRYPTED\n')  # Magic header
                f.write(salt)
                f.write(iv)
                f.write(encrypted)
        else:
            # Save plaintext (base64 encoded keys are still not human-readable)
            with open(self.keystore_path, 'w') as f:
                f.write(data)
    
    def load(self, password: str = None):
        """
        Load keystore from disk.
        
        Args:
            password: Password if keystore is encrypted
        
        Raises:
            ValueError: If password is required but not provided or incorrect
        """
        with open(self.keystore_path, 'rb') as f:
            header = f.read(10)
            
            if header == b'ENCRYPTED\n':
                if not password:
                    raise ValueError("Keystore is encrypted. Password required.")
                
                salt = f.read(16)
                iv = f.read(16)
                encrypted = f.read()
                
                # Derive key
                key = PBKDF2(password, salt, dkLen=32, count=100000)
                cipher = AES.new(key, AES.MODE_CBC, iv)
                
                decrypted = cipher.decrypt(encrypted)
                
                # Unpad
                padding_length = decrypted[-1]
                data = decrypted[:-padding_length].decode('utf-8')
            else:
                # Plaintext format
                f.seek(0)
                data = f.read().decode('utf-8')
        
        self.keys = json.loads(data)


def save_key_to_file(key: bytes, filepath: str, key_id: str = None, metadata: dict = None):
    """
    Save a key to a standalone file (alternative to KeyStore).
    
    Args:
        key: The encryption key
        filepath: Path to save the key file
        key_id: Optional identifier
        metadata: Optional metadata
    """
    key_data = {
        'key_id': key_id or os.path.basename(filepath),
        'key': base64.b64encode(key).decode('utf-8'),
        'created': datetime.now().isoformat(),
        'metadata': metadata or {}
    }
    
    with open(filepath, 'w') as f:
        json.dump(key_data, f, indent=2)


def load_key_from_file(filepath: str) -> tuple:
    """
    Load a key from a standalone file.
    
    Args:
        filepath: Path to the key file
    
    Returns:
        tuple: (key, metadata)
    """
    with open(filepath, 'r') as f:
        key_data = json.load(f)
    
    key = base64.b64decode(key_data['key'])
    metadata = key_data.get('metadata', {})
    
    return key, metadata
