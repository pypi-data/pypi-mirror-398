import argparse
import os
from pathlib import Path
from core.aes_crypto import generate_key, encrypt_file, decrypt_file, secure_delete
from core.key_store import KeyStore, save_key_to_file, load_key_from_file
from core.batch_encrypt import BatchEncryptor
from utils.logger import info, success, error, warning

def main():
    parser = argparse.ArgumentParser(
        description="FENCE (File ENCryption Engine) - Secure file and folder encryption",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Encrypt a single file with password
  python -m cli.aes_cli encrypt file.txt --output file.txt.enc --password mypass
  
  # Encrypt with random key (saved to keystore)
  python -m cli.aes_cli encrypt file.txt --output file.txt.enc --random-key --key-id myfile
  
  # Encrypt entire folder
  python -m cli.aes_cli encrypt-folder ./data --output ./encrypted --password mypass
  
  # Decrypt file
  python -m cli.aes_cli decrypt file.txt.enc --output file.txt --password mypass
  
  # Decrypt with key from keystore
  python -m cli.aes_cli decrypt file.txt.enc --output file.txt --key-id myfile
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Encrypt file command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a single file")
    encrypt_parser.add_argument("input", help="Input file path")
    encrypt_parser.add_argument("--output", help="Output file path (default: input + .enc)")
    encrypt_parser.add_argument("--password", help="Password for encryption")
    encrypt_parser.add_argument("--random-key", action="store_true", help="Use random key instead of password")
    encrypt_parser.add_argument("--key-id", help="Key identifier for keystore")
    encrypt_parser.add_argument("--key-file", help="Save random key to this file")
    encrypt_parser.add_argument("--keysize", type=int, choices=[16, 32], default=32, 
                               help="Key size (16=AES-128, 32=AES-256, default: 32)")
    encrypt_parser.add_argument("--no-hmac", action="store_true", help="Disable HMAC authentication")
    encrypt_parser.add_argument("--secure-delete", action="store_true", help="Securely delete original file after encryption")

    # Decrypt file command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a single file")
    decrypt_parser.add_argument("input", help="Input encrypted file path")
    decrypt_parser.add_argument("--output", help="Output file path (default: removes .enc extension)")
    decrypt_parser.add_argument("--password", help="Password for decryption")
    decrypt_parser.add_argument("--key-id", help="Key identifier from keystore")
    decrypt_parser.add_argument("--key-file", help="Load key from this file")
    decrypt_parser.add_argument("--keysize", type=int, choices=[16, 32], default=32,
                               help="Key size (16=AES-128, 32=AES-256, default: 32)")
    decrypt_parser.add_argument("--no-hmac", action="store_true", help="File was encrypted without HMAC")

    # Encrypt folder command
    encrypt_folder_parser = subparsers.add_parser("encrypt-folder", help="Encrypt entire folder")
    encrypt_folder_parser.add_argument("input", help="Input folder path")
    encrypt_folder_parser.add_argument("--output", required=True, help="Output folder path")
    encrypt_folder_parser.add_argument("--password", help="Password for encryption")
    encrypt_folder_parser.add_argument("--random-key", action="store_true", help="Use random key")
    encrypt_folder_parser.add_argument("--key-id", help="Key identifier for keystore")
    encrypt_folder_parser.add_argument("--key-file", help="Save random key to this file")
    encrypt_folder_parser.add_argument("--keysize", type=int, choices=[16, 32], default=32)
    encrypt_folder_parser.add_argument("--compress", action="store_true", help="Compress folder before encryption")
    encrypt_folder_parser.add_argument("--no-parallel", action="store_true", help="Disable parallel processing")
    encrypt_folder_parser.add_argument("--pattern", default="*", help="File pattern to match (default: *)")
    encrypt_folder_parser.add_argument("--no-recursive", action="store_true", help="Don't process subfolders")

    # Decrypt folder command
    decrypt_folder_parser = subparsers.add_parser("decrypt-folder", help="Decrypt entire folder")
    decrypt_folder_parser.add_argument("input", help="Input encrypted folder path")
    decrypt_folder_parser.add_argument("--output", required=True, help="Output folder path")
    decrypt_folder_parser.add_argument("--password", help="Password for decryption")
    decrypt_folder_parser.add_argument("--key-id", help="Key identifier from keystore")
    decrypt_folder_parser.add_argument("--key-file", help="Load key from this file")
    decrypt_folder_parser.add_argument("--keysize", type=int, choices=[16, 32], default=32)
    decrypt_folder_parser.add_argument("--metadata", help="Path to metadata file")

    # Keystore management
    keystore_parser = subparsers.add_parser("keystore", help="Manage encryption keys")
    keystore_parser.add_argument("action", choices=["list", "delete"], help="Keystore action")
    keystore_parser.add_argument("--key-id", help="Key identifier (for delete)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # Initialize keystore
        keystore = KeyStore()

        if args.command == "encrypt":
            handle_encrypt_file(args, keystore)
        
        elif args.command == "decrypt":
            handle_decrypt_file(args, keystore)
        
        elif args.command == "encrypt-folder":
            handle_encrypt_folder(args, keystore)
        
        elif args.command == "decrypt-folder":
            handle_decrypt_folder(args, keystore)
        
        elif args.command == "keystore":
            handle_keystore(args, keystore)

    except FileNotFoundError as e:
        error(f"File not found: {e}")
    except ValueError as e:
        error(f"Error: {e}")
    except Exception as e:
        error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def handle_encrypt_file(args, keystore):
    """Handle single file encryption."""
    output_path = args.output or f"{args.input}.enc"
    
    # Determine encryption key
    if args.random_key:
        key, salt = generate_key(None, args.keysize)
        
        # Save key
        if args.key_id:
            keystore.save_key(args.key_id, key, {"file": args.input})
            info(f"Key saved to keystore with ID: {args.key_id}")
        
        if args.key_file:
            save_key_to_file(key, args.key_file, args.key_id, {"file": args.input})
            info(f"Key saved to file: {args.key_file}")
        
        if not args.key_id and not args.key_file:
            warning("Random key generated but not saved! You won't be able to decrypt without the key.")
            key_file = f"{output_path}.key"
            save_key_to_file(key, key_file, metadata={"file": args.input})
            info(f"Key automatically saved to: {key_file}")
    
    elif args.password:
        key, salt = generate_key(args.password, args.keysize)
    
    else:
        error("Either --password or --random-key must be specified")
        return
    
    # Encrypt
    info(f"Encrypting: {args.input}")
    encrypt_file(args.input, output_path, key, salt=salt, use_hmac=not args.no_hmac)
    success(f"File encrypted: {output_path}")
    
    # Secure delete original if requested
    if args.secure_delete:
        info(f"Securely deleting original file: {args.input}")
        secure_delete(args.input)
        success("Original file securely deleted")


def handle_decrypt_file(args, keystore):
    """Handle single file decryption."""
    output_path = args.output
    if not output_path:
        if args.input.endswith('.enc'):
            output_path = args.input[:-4]
        else:
            output_path = f"{args.input}.dec"
    
    # Determine decryption key
    key = None
    
    if args.key_id:
        try:
            key = keystore.get_key(args.key_id)
            info(f"Loaded key from keystore: {args.key_id}")
        except KeyError:
            error(f"Key '{args.key_id}' not found in keystore")
            return
    
    elif args.key_file:
        key, metadata = load_key_from_file(args.key_file)
        info(f"Loaded key from file: {args.key_file}")
    
    elif args.password:
        # Password-based decryption
        info(f"Decrypting with password")
        decrypt_file(args.input, output_path, password=args.password, 
                    key_size=args.keysize, use_hmac=not args.no_hmac)
        success(f"File decrypted: {output_path}")
        return
    
    else:
        # Try to find auto-saved key file
        auto_key_file = f"{args.input}.key"
        if os.path.exists(auto_key_file):
            key, metadata = load_key_from_file(auto_key_file)
            info(f"Using auto-saved key: {auto_key_file}")
        else:
            error("No decryption key provided. Use --password, --key-id, or --key-file")
            return
    
    # Decrypt
    info(f"Decrypting: {args.input}")
    decrypt_file(args.input, output_path, key=key, key_size=args.keysize, 
                use_hmac=not args.no_hmac)
    success(f"File decrypted: {output_path}")


def handle_encrypt_folder(args, keystore):
    """Handle folder encryption."""
    # Determine encryption key
    if args.random_key:
        key, _ = generate_key(None, args.keysize)
        password = None
        
        if args.key_id:
            keystore.save_key(args.key_id, key, {"folder": args.input})
            info(f"Key saved to keystore with ID: {args.key_id}")
        
        if args.key_file:
            save_key_to_file(key, args.key_file, args.key_id, {"folder": args.input})
            info(f"Key saved to file: {args.key_file}")
    
    elif args.password:
        key = None
        password = args.password
    
    else:
        error("Either --password or --random-key must be specified")
        return
    
    # Create batch encryptor
    encryptor = BatchEncryptor(
        key=key,
        password=password,
        key_size=args.keysize,
        use_compression=args.compress,
        use_parallel=not args.no_parallel
    )
    
    # Encrypt folder
    encryptor.encrypt_folder(
        args.input,
        args.output,
        recursive=not args.no_recursive,
        pattern=args.pattern
    )


def handle_decrypt_folder(args, keystore):
    """Handle folder decryption."""
    # Determine decryption key
    key = None
    password = None
    
    if args.key_id:
        key = keystore.get_key(args.key_id)
        info(f"Loaded key from keystore: {args.key_id}")
    
    elif args.key_file:
        key, metadata = load_key_from_file(args.key_file)
        info(f"Loaded key from file: {args.key_file}")
    
    elif args.password:
        password = args.password
    
    else:
        error("No decryption key provided. Use --password, --key-id, or --key-file")
        return
    
    # Create batch encryptor
    encryptor = BatchEncryptor(
        key=key,
        password=password,
        key_size=args.keysize
    )
    
    # Decrypt folder
    encryptor.decrypt_folder(args.input, args.output, args.metadata)


def handle_keystore(args, keystore):
    """Handle keystore management."""
    if args.action == "list":
        keys = keystore.list_keys()
        if not keys:
            info("Keystore is empty")
            return
        
        info(f"Stored keys ({len(keys)}):")
        for key_id, created, metadata in keys:
            print(f"  • {key_id}")
            print(f"    Created: {created}")
            if metadata:
                print(f"    Metadata: {metadata}")
    
    elif args.action == "delete":
        if not args.key_id:
            error("--key-id required for delete action")
            return
        
        keystore.delete_key(args.key_id)
        success(f"Key '{args.key_id}' deleted from keystore")


if __name__ == "__main__":
    main()

