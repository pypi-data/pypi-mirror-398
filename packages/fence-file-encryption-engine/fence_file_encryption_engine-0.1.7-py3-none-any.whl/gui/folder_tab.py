# gui/folder_tab.py

"""
Folder encryption/decryption tab for GUI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

from core.aes_crypto import generate_key
from core.key_store import KeyStore, save_key_to_file
from core.batch_encrypt import BatchEncryptor


class FolderEncryptionTab(ttk.Frame):
    """Tab for encrypting/decrypting folders."""
    
    def __init__(self, parent, main_app):
        """
        Initialize folder encryption tab.
        
        Args:
            parent: Parent widget
            main_app: Reference to main application
        """
        super().__init__(parent)
        self.main_app = main_app
        self.keystore = KeyStore()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all widgets for the tab."""
        # Main container
        container = ttk.Frame(self, padding="20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(
            container,
            text="Folder Encryption / Decryption",
            font=('Arial', 16, 'bold')
        )
        title.pack(pady=(0, 20))
        
        # ===== Input Folder Section =====
        input_frame = ttk.LabelFrame(container, text="Input Folder", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.input_path_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_path_var, width=60)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_input_btn = ttk.Button(
            input_frame,
            text="Browse...",
            command=self._browse_input_folder
        )
        browse_input_btn.pack(side=tk.LEFT)
        
        # ===== Output Folder Section =====
        output_frame = ttk.LabelFrame(container, text="Output Folder", padding="15")
        output_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.output_path_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var, width=60)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_output_btn = ttk.Button(
            output_frame,
            text="Browse...",
            command=self._browse_output_folder
        )
        browse_output_btn.pack(side=tk.LEFT)
        
        # ===== Encryption Options =====
        options_frame = ttk.LabelFrame(container, text="Encryption Options", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Key method
        key_method_frame = ttk.Frame(options_frame)
        key_method_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(key_method_frame, text="Key Method:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.key_method_var = tk.StringVar(value="password")
        password_radio = ttk.Radiobutton(
            key_method_frame,
            text="Password",
            variable=self.key_method_var,
            value="password",
            command=self._update_key_method
        )
        password_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        random_key_radio = ttk.Radiobutton(
            key_method_frame,
            text="Random Key",
            variable=self.key_method_var,
            value="random",
            command=self._update_key_method
        )
        random_key_radio.pack(side=tk.LEFT)
        
        # Password entry
        self.password_frame = ttk.Frame(options_frame)
        self.password_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(self.password_frame, text="Password:").pack(side=tk.LEFT, padx=(0, 10))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(
            self.password_frame,
            textvariable=self.password_var,
            show="*",
            width=40
        )
        password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Random key ID
        self.random_key_frame = ttk.Frame(options_frame)
        
        tk.Label(self.random_key_frame, text="Key ID:").pack(side=tk.LEFT, padx=(0, 10))
        self.key_id_var = tk.StringVar()
        key_id_entry = ttk.Entry(
            self.random_key_frame,
            textvariable=self.key_id_var,
            width=30
        )
        key_id_entry.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(self.random_key_frame, text="(optional)").pack(side=tk.LEFT)
        
        # Key size
        key_size_frame = ttk.Frame(options_frame)
        key_size_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(key_size_frame, text="Key Size:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.key_size_var = tk.IntVar(value=32)
        aes128_radio = ttk.Radiobutton(
            key_size_frame,
            text="AES-128",
            variable=self.key_size_var,
            value=16
        )
        aes128_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        aes256_radio = ttk.Radiobutton(
            key_size_frame,
            text="AES-256",
            variable=self.key_size_var,
            value=32
        )
        aes256_radio.pack(side=tk.LEFT)
        
        # File pattern
        pattern_frame = ttk.Frame(options_frame)
        pattern_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(pattern_frame, text="File Pattern:").pack(side=tk.LEFT, padx=(0, 10))
        self.pattern_var = tk.StringVar(value="*")
        pattern_entry = ttk.Entry(pattern_frame, textvariable=self.pattern_var, width=20)
        pattern_entry.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(pattern_frame, text="(e.g., *.pdf, *.txt, * for all)").pack(side=tk.LEFT)
        
        # Checkboxes for options
        self.use_compression_var = tk.BooleanVar(value=False)
        compression_check = ttk.Checkbutton(
            options_frame,
            text="Compress folder before encryption (ZIP)",
            variable=self.use_compression_var
        )
        compression_check.pack(anchor=tk.W, pady=(0, 5))
        
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_check = ttk.Checkbutton(
            options_frame,
            text="Process subfolders recursively",
            variable=self.recursive_var
        )
        recursive_check.pack(anchor=tk.W, pady=(0, 5))
        
        self.use_parallel_var = tk.BooleanVar(value=True)
        parallel_check = ttk.Checkbutton(
            options_frame,
            text="Use parallel processing (faster)",
            variable=self.use_parallel_var
        )
        parallel_check.pack(anchor=tk.W)
        
        # ===== Progress Section =====
        self.progress_frame = ttk.Frame(container)
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='indeterminate'
        )
        self.progress_bar.pack(fill=tk.X)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=('Arial', 9)
        )
        self.progress_label.pack(pady=(5, 0))
        
        # ===== Action Buttons =====
        button_frame = ttk.Frame(container)
        button_frame.pack(pady=(10, 0))
        
        self.encrypt_btn = ttk.Button(
            button_frame,
            text="🔒 Encrypt Folder",
            command=self._encrypt_folder,
            width=20
        )
        self.encrypt_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.decrypt_btn = ttk.Button(
            button_frame,
            text="🔓 Decrypt Folder",
            command=self._decrypt_folder,
            width=20
        )
        self.decrypt_btn.pack(side=tk.LEFT)
        
        # Initialize UI
        self._update_key_method()
    
    def _browse_input_folder(self):
        """Browse for input folder."""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_path_var.set(folder)
            
            # Auto-suggest output folder
            if not self.output_path_var.get():
                self.output_path_var.set(folder + "_encrypted")
    
    def _browse_output_folder(self):
        """Browse for output folder."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_path_var.set(folder)
    
    def _update_key_method(self):
        """Update UI based on selected key method."""
        method = self.key_method_var.get()
        
        # Hide all frames
        self.password_frame.pack_forget()
        self.random_key_frame.pack_forget()
        
        # Show relevant frame
        if method == "password":
            self.password_frame.pack(fill=tk.X, pady=(0, 10))
        elif method == "random":
            self.random_key_frame.pack(fill=tk.X, pady=(0, 10))
    
    def _encrypt_folder(self):
        """Handle folder encryption."""
        # Validate inputs
        if not self.input_path_var.get():
            messagebox.showerror("Error", "Please select an input folder")
            return
        
        if not self.output_path_var.get():
            messagebox.showerror("Error", "Please specify an output folder")
            return
        
        if not os.path.isdir(self.input_path_var.get()):
            messagebox.showerror("Error", "Input path is not a valid folder")
            return
        
        # Run encryption in background thread
        thread = threading.Thread(target=self._do_encrypt_folder, daemon=True)
        thread.start()
    
    def _do_encrypt_folder(self):
        """Perform folder encryption (runs in background thread)."""
        try:
            # Disable buttons
            self.encrypt_btn.config(state=tk.DISABLED)
            self.decrypt_btn.config(state=tk.DISABLED)
            
            # Start progress bar
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
            self.progress_label.config(text="Encrypting folder...")
            self.main_app.set_status("Encrypting folder...", "blue")
            
            # Get parameters
            input_path = self.input_path_var.get()
            output_path = self.output_path_var.get()
            key_method = self.key_method_var.get()
            key_size = self.key_size_var.get()
            pattern = self.pattern_var.get()
            use_compression = self.use_compression_var.get()
            recursive = self.recursive_var.get()
            use_parallel = self.use_parallel_var.get()
            
            # Generate or get key
            key = None
            password = None
            
            if key_method == "password":
                password = self.password_var.get()
                if not password:
                    raise ValueError("Password is required")
            elif key_method == "random":
                key, _ = generate_key(None, key_size)
                
                # Save key
                key_id = self.key_id_var.get() or f"folder_{os.path.basename(input_path)}"
                self.keystore.save_key(key_id, key, {"folder": input_path})
                
                # Also save to file
                key_file = os.path.join(output_path + ".key")
                save_key_to_file(key, key_file, key_id, {"folder": input_path})
            
            # Create batch encryptor
            encryptor = BatchEncryptor(
                key=key,
                password=password,
                key_size=key_size,
                use_compression=use_compression,
                use_parallel=use_parallel
            )
            
            # Encrypt folder
            metadata = encryptor.encrypt_folder(
                input_path,
                output_path,
                recursive=recursive,
                pattern=pattern
            )
            
            # Stop progress bar
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_var.set(100)
            self.progress_label.config(text=f"✓ Encrypted {len(metadata.get('files', {}))} file(s)")
            self.main_app.set_status("Folder encrypted successfully", "green")
            
            # Show success message
            messagebox.showinfo(
                "Success",
                f"Folder encrypted successfully!\n\n"
                f"Files processed: {len(metadata.get('files', {}))}\n"
                f"Output: {output_path}"
            )
        
        except Exception as e:
            self.progress_bar.stop()
            self.progress_label.config(text=f"✗ Error: {str(e)}")
            self.main_app.set_status("Encryption failed", "red")
            messagebox.showerror("Encryption Error", str(e))
        
        finally:
            # Re-enable buttons
            self.encrypt_btn.config(state=tk.NORMAL)
            self.decrypt_btn.config(state=tk.NORMAL)
    
    def _decrypt_folder(self):
        """Handle folder decryption."""
        # Validate inputs
        if not self.input_path_var.get():
            messagebox.showerror("Error", "Please select an input folder")
            return
        
        if not self.output_path_var.get():
            messagebox.showerror("Error", "Please specify an output folder")
            return
        
        if not os.path.isdir(self.input_path_var.get()):
            messagebox.showerror("Error", "Input path is not a valid folder")
            return
        
        # Run decryption in background thread
        thread = threading.Thread(target=self._do_decrypt_folder, daemon=True)
        thread.start()
    
    def _do_decrypt_folder(self):
        """Perform folder decryption (runs in background thread)."""
        try:
            # Disable buttons
            self.encrypt_btn.config(state=tk.DISABLED)
            self.decrypt_btn.config(state=tk.DISABLED)
            
            # Start progress bar
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
            self.progress_label.config(text="Decrypting folder...")
            self.main_app.set_status("Decrypting folder...", "blue")
            
            # Get parameters
            input_path = self.input_path_var.get()
            output_path = self.output_path_var.get()
            key_method = self.key_method_var.get()
            key_size = self.key_size_var.get()
            
            # Get key
            key = None
            password = None
            
            if key_method == "password":
                password = self.password_var.get()
                if not password:
                    raise ValueError("Password is required")
            elif key_method == "random":
                # Try to find key file
                key_file = input_path + ".key"
                if os.path.exists(key_file):
                    from core.key_store import load_key_from_file
                    key, _ = load_key_from_file(key_file)
                else:
                    # Try keystore
                    key_id = self.key_id_var.get()
                    if key_id:
                        key = self.keystore.get_key(key_id)
                    else:
                        raise ValueError("No key found. Please provide key ID or use password.")
            
            # Create batch decryptor
            decryptor = BatchEncryptor(
                key=key,
                password=password,
                key_size=key_size
            )
            
            # Decrypt folder
            count = decryptor.decrypt_folder(input_path, output_path)
            
            # Stop progress bar
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_var.set(100)
            self.progress_label.config(text=f"✓ Decrypted {count} file(s)")
            self.main_app.set_status("Folder decrypted successfully", "green")
            
            # Show success message
            messagebox.showinfo(
                "Success",
                f"Folder decrypted successfully!\n\n"
                f"Files processed: {count}\n"
                f"Output: {output_path}"
            )
        
        except Exception as e:
            self.progress_bar.stop()
            self.progress_label.config(text=f"✗ Error: {str(e)}")
            self.main_app.set_status("Decryption failed", "red")
            messagebox.showerror("Decryption Error", str(e))
        
        finally:
            # Re-enable buttons
            self.encrypt_btn.config(state=tk.NORMAL)
            self.decrypt_btn.config(state=tk.NORMAL)
