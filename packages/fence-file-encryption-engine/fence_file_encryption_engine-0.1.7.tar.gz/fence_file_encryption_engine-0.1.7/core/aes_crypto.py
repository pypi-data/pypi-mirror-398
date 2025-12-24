# core/aes_crypto.py

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import HMAC, SHA256
import os
import secrets
from typing import Optional, Tuple

BLOCK_SIZE = AES.block_size  # 16 bytes

def pad(data: bytes) -> bytes:
    """PKCS7 padding"""
    padding_length = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + bytes([padding_length] * padding_length)

def unpad(data: bytes) -> bytes:
    """Remove PKCS7 padding with validation"""
    if len(data) == 0:
        raise ValueError("Cannot unpad empty data")
    
    padding_length = data[-1]
    
    # Validate padding
    if padding_length > BLOCK_SIZE or padding_length == 0:
        raise ValueError("Invalid padding length")
    
    # Check all padding bytes are correct
    if data[-padding_length:] != bytes([padding_length] * padding_length):
        raise ValueError("Invalid padding bytes")
    
    return data[:-padding_length]

def generate_key(password: Optional[str] = None, key_size: int = 32) -> Tuple[bytes, Optional[bytes]]:
    """
    Generate encryption key either from password (PBKDF2) or randomly.
    
    Args:
        password: Optional password string for key derivation
        key_size: Key size in bytes (16 for AES-128, 32 for AES-256)
    
    Returns:
        tuple: (key, salt) - salt is None for random keys
    """
    if password:
        salt = get_random_bytes(16)
        # Use 100,000 iterations for PBKDF2 (OWASP recommendation)
        key = PBKDF2(password, salt, dkLen=key_size, count=100000)
        return key, salt

    return secrets.token_bytes(key_size), None

def compute_hmac(key: bytes, data: bytes) -> bytes:
    """Compute HMAC-SHA256 for data authentication"""
    h = HMAC.new(key, digestmod=SHA256)
    h.update(data)
    return h.digest()

def verify_hmac(key: bytes, data: bytes, expected_hmac: bytes) -> bool:
    """Verify HMAC-SHA256"""
    if expected_hmac is None:
        raise ValueError("expected_hmac must be provided for HMAC verification")
    computed = compute_hmac(key, data)
    return secrets.compare_digest(computed, expected_hmac)

def encrypt_file(input_path: str, output_path: str, key: bytes, iv: Optional[bytes] = None, salt: Optional[bytes] = None, use_hmac: bool = True) -> None:
    """
    Encrypt a file using AES-CBC with optional HMAC authentication.
    
    File format:
    [salt (16 bytes, optional)] [iv (16 bytes)] [hmac (32 bytes, optional)] [encrypted_data]
    
    Args:
        input_path: Path to input file
        output_path: Path to output encrypted file
        key: Encryption key (16 or 32 bytes)
        iv: Initialization vector (optional, generated if None)
        salt: Salt used for key derivation (optional)
        use_hmac: Whether to include HMAC for authentication
    """
    if key is None:
        raise ValueError("Encryption key must be provided")

    iv = iv or get_random_bytes(16)
    if not isinstance(iv, (bytes, bytearray)) or len(iv) != AES.block_size:
        raise ValueError("IV must be 16 bytes")

    cipher = AES.new(key, AES.MODE_CBC, iv)

    with open(input_path, 'rb') as f:
        raw = f.read()
    data = pad(raw)

    encrypted = cipher.encrypt(data)
    
    # Compute HMAC over IV + encrypted data for authentication
    if use_hmac:
        hmac_value = compute_hmac(key, iv + encrypted)

    with open(output_path, 'wb') as f:
        if salt:
            if not isinstance(salt, (bytes, bytearray)) or len(salt) != 16:
                raise ValueError("Salt must be 16 bytes when provided")
            f.write(salt)  # 16 bytes
        f.write(iv)  # 16 bytes
        if use_hmac:
            # hmac_value is set above when use_hmac is True
            f.write(hmac_value)  # type: ignore[arg-type]
        f.write(encrypted)

def decrypt_file(input_path: str, output_path: str, password: Optional[str] = None, key: Optional[bytes] = None, key_size: int = 32, use_hmac: bool = True) -> None:
    """
    Decrypt a file encrypted with encrypt_file.
    
    Args:
        input_path: Path to encrypted file
        output_path: Path to output decrypted file
        password: Password for key derivation (if used during encryption)
        key: Direct encryption key (if not using password)
        key_size: Key size in bytes (16 or 32)
        use_hmac: Whether HMAC was used during encryption
    
    Raises:
        ValueError: If HMAC verification fails or padding is invalid
    """
    with open(input_path, 'rb') as f:
        if password:
            salt = f.read(16)
            if len(salt) != 16:
                raise ValueError("Encrypted file missing or has invalid salt")
            key = PBKDF2(password, salt, dkLen=key_size, count=100000)

        iv = f.read(16)
        if len(iv) != AES.block_size:
            raise ValueError("Invalid or missing IV in encrypted file")

        stored_hmac = None
        if use_hmac:
            stored_hmac = f.read(32)
            if len(stored_hmac) != 32:
                raise ValueError("Invalid or missing HMAC in encrypted file")

        encrypted = f.read()
        if not encrypted:
            raise ValueError("No encrypted payload found in file")
    
    # Verify HMAC before decryption
    if use_hmac:
        if key is None:
            raise ValueError("Decryption key must be provided for HMAC verification")
        # mypy/static analyzers may not infer stored_hmac is bytes; assert to narrow type
        assert isinstance(stored_hmac, (bytes, bytearray)), "Invalid HMAC value"
        if not verify_hmac(key, iv + encrypted, stored_hmac):
            raise ValueError("HMAC verification failed - file may be corrupted or tampered with")

    if key is None:
        raise ValueError("Decryption key must be provided")

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted))

    with open(output_path, 'wb') as f:
        f.write(decrypted)

def secure_delete(filepath, passes=3):
    """
    Securely delete a file by overwriting it before deletion.
    
    Args:
        filepath: Path to file to securely delete
        passes: Number of overwrite passes (default: 3)
    """
    if not os.path.exists(filepath):
        return

    file_size = os.path.getsize(filepath)

    with open(filepath, 'r+b') as f:
        for _ in range(passes):
            f.seek(0)
            # Use secrets for cryptographically secure random bytes
            f.write(secrets.token_bytes(file_size))
            f.flush()
            os.fsync(f.fileno())

    os.remove(filepath)

