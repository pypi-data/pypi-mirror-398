# core/batch_encrypt.py

"""
Batch encryption module for folders and multiple files.
Supports parallel processing, compression, and metadata storage.
"""

import os
import json
import zipfile
import tarfile
from pathlib import Path
from multiprocessing import Pool, cpu_count
from typing import List, Tuple, Optional
from datetime import datetime

from core.aes_crypto import encrypt_file, decrypt_file, generate_key
from utils.logger import info, success, warning, error


class BatchEncryptor:
    """Handles encryption of multiple files and folders."""
    
    def __init__(self, key=None, password=None, key_size=32, use_compression=False, 
                 use_parallel=True, max_workers=None):
        """
        Initialize BatchEncryptor.
        
        Args:
            key: Encryption key (if None, will be generated)
            password: Password for key derivation (alternative to key)
            key_size: Key size in bytes (16 or 32)
            use_compression: Whether to compress before encryption
            use_parallel: Whether to use parallel processing
            max_workers: Number of parallel workers (default: CPU count)
        """
        if password:
            self.key, self.salt = generate_key(password, key_size)
        elif key:
            self.key = key
            self.salt = None
        else:
            self.key, self.salt = generate_key(None, key_size)
        
        self.key_size = key_size
        self.use_compression = use_compression
        self.use_parallel = use_parallel
        self.max_workers = max_workers or cpu_count()
        self.metadata = {}
    
    def encrypt_folder(self, folder_path: str, output_folder: str, 
                       recursive=True, pattern="*") -> dict:
        """
        Encrypt all files in a folder.
        
        Args:
            folder_path: Path to folder to encrypt
            output_folder: Path to output folder
            recursive: Whether to process subfolders
            pattern: File pattern to match (e.g., "*.txt")
        
        Returns:
            dict: Metadata about encrypted files
        """
        folder_path = Path(folder_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Find all files
        if recursive:
            files = list(folder_path.rglob(pattern))
        else:
            files = list(folder_path.glob(pattern))
        
        files = [f for f in files if f.is_file()]
        
        if not files:
            warning(f"No files found matching pattern '{pattern}'")
            return {}
        
        info(f"Found {len(files)} files to encrypt")
        
        # Compress if requested
        if self.use_compression:
            info("Compressing folder before encryption...")
            compressed_file = output_folder / f"{folder_path.name}.zip"
            self._compress_folder(folder_path, compressed_file, files)
            files_to_encrypt = [(compressed_file, output_folder / f"{compressed_file.name}.enc")]
        else:
            # Prepare file pairs (input, output)
            files_to_encrypt = []
            for file in files:
                rel_path = file.relative_to(folder_path)
                output_path = output_folder / f"{rel_path}.enc"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                files_to_encrypt.append((file, output_path))
        
        # Encrypt files
        if self.use_parallel and len(files_to_encrypt) > 1:
            self._encrypt_parallel(files_to_encrypt)
        else:
            self._encrypt_sequential(files_to_encrypt)
        
        # Save metadata
        metadata = self._create_metadata(folder_path, files_to_encrypt)
        metadata_path = output_folder / "encryption_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        success(f"Encrypted {len(files_to_encrypt)} file(s) to {output_folder}")
        return metadata
    
    def decrypt_folder(self, encrypted_folder: str, output_folder: str, 
                       metadata_file: str = None) -> int:
        """
        Decrypt all encrypted files in a folder.
        
        Args:
            encrypted_folder: Path to folder with encrypted files
            output_folder: Path to output folder
            metadata_file: Path to metadata file (optional)
        
        Returns:
            int: Number of files decrypted
        """
        encrypted_folder = Path(encrypted_folder)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Load metadata if available
        metadata = None
        if metadata_file:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        elif (encrypted_folder / "encryption_metadata.json").exists():
            with open(encrypted_folder / "encryption_metadata.json", 'r') as f:
                metadata = json.load(f)
        
        # Find encrypted files
        enc_files = list(encrypted_folder.rglob("*.enc"))
        
        if not enc_files:
            warning("No encrypted files found")
            return 0
        
        info(f"Found {len(enc_files)} encrypted files")
        
        # Decrypt files
        decrypted_count = 0
        for enc_file in enc_files:
            try:
                # Determine output path
                if metadata and str(enc_file.name) in metadata.get('files', {}):
                    original_name = metadata['files'][str(enc_file.name)]['original_name']
                    output_path = output_folder / original_name
                else:
                    output_path = output_folder / enc_file.stem
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Decrypt
                decrypt_file(
                    str(enc_file), 
                    str(output_path), 
                    key=self.key,
                    key_size=self.key_size
                )
                decrypted_count += 1
                success(f"Decrypted: {enc_file.name} -> {output_path.name}")
            
            except Exception as e:
                error(f"Failed to decrypt {enc_file.name}: {e}")
        
        # Decompress if it was compressed
        if metadata and metadata.get('compressed'):
            info("Decompressing archive...")
            archive_file = output_folder / metadata['files'][list(metadata['files'].keys())[0]]['original_name']
            if archive_file.suffix == '.zip':
                with zipfile.ZipFile(archive_file, 'r') as zf:
                    zf.extractall(output_folder)
                archive_file.unlink()  # Remove the archive
        
        success(f"Decrypted {decrypted_count} file(s) to {output_folder}")
        return decrypted_count
    
    def _compress_folder(self, folder_path: Path, output_file: Path, files: List[Path]):
        """Compress files into a ZIP archive."""
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                arcname = file.relative_to(folder_path.parent)
                zf.write(file, arcname)
    
    def _encrypt_sequential(self, file_pairs: List[Tuple[Path, Path]]):
        """Encrypt files sequentially."""
        for i, (input_path, output_path) in enumerate(file_pairs, 1):
            try:
                info(f"[{i}/{len(file_pairs)}] Encrypting: {input_path.name}")
                encrypt_file(
                    str(input_path), 
                    str(output_path), 
                    self.key, 
                    salt=self.salt
                )
            except Exception as e:
                error(f"Failed to encrypt {input_path.name}: {e}")
    
    def _encrypt_parallel(self, file_pairs: List[Tuple[Path, Path]]):
        """Encrypt files in parallel."""
        info(f"Using {self.max_workers} parallel workers")
        
        # Prepare arguments for parallel processing
        args_list = [
            (str(inp), str(out), self.key, self.salt) 
            for inp, out in file_pairs
        ]
        
        with Pool(self.max_workers) as pool:
            results = pool.starmap(_encrypt_worker, args_list)
        
        # Report results
        successful = sum(1 for r in results if r)
        if successful < len(file_pairs):
            warning(f"{len(file_pairs) - successful} file(s) failed to encrypt")
    
    def _create_metadata(self, folder_path: Path, file_pairs: List[Tuple[Path, Path]]) -> dict:
        """Create metadata for encrypted files."""
        metadata = {
            'encrypted_at': datetime.now().isoformat(),
            'key_size': self.key_size,
            'compressed': self.use_compression,
            'files': {}
        }
        
        for input_path, output_path in file_pairs:
            metadata['files'][output_path.name] = {
                'original_name': input_path.name,
                'original_path': str(input_path.relative_to(folder_path)) if self.use_compression else str(input_path),
                'size': input_path.stat().st_size if input_path.exists() else 0
            }
        
        return metadata


def _encrypt_worker(input_path: str, output_path: str, key: bytes, salt: bytes) -> bool:
    """Worker function for parallel encryption."""
    try:
        encrypt_file(input_path, output_path, key, salt=salt)
        return True
    except Exception as e:
        print(f"Error encrypting {input_path}: {e}")
        return False


def encrypt_files_batch(file_paths: List[str], output_dir: str, 
                       key=None, password=None, key_size=32) -> dict:
    """
    Convenience function to encrypt multiple files.
    
    Args:
        file_paths: List of file paths to encrypt
        output_dir: Output directory
        key: Encryption key (optional)
        password: Password for encryption (optional)
        key_size: Key size in bytes
    
    Returns:
        dict: Metadata about encrypted files
    """
    encryptor = BatchEncryptor(key=key, password=password, key_size=key_size, use_parallel=True)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_pairs = [
        (Path(fp), output_path / f"{Path(fp).name}.enc") 
        for fp in file_paths
    ]
    
    encryptor._encrypt_parallel(file_pairs)
    
    return encryptor._create_metadata(Path.cwd(), file_pairs)
