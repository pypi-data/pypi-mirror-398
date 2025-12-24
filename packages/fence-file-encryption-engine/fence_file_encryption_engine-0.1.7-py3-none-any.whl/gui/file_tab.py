# gui/file_tab.py

"""
File encryption/decryption tab for GUI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

from core.aes_crypto import generate_key, encrypt_file, decrypt_file, secure_delete
from core.key_store import KeyStore, save_key_to_file, load_key_from_file


class FileEncryptionTab(ttk.Frame):
    """Tab for encrypting/decrypting single files."""
    
    def __init__(self, parent, main_app):
        """
        Initialize file encryption tab.
        
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
            text="File Encryption / Decryption",
            font=('Arial', 16, 'bold')
        )
        title.pack(pady=(0, 20))
        
        # ===== Input File Section =====
        input_frame = ttk.LabelFrame(container, text="Input File", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.input_path_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_path_var, width=60)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_input_btn = ttk.Button(
            input_frame,
            text="Browse...",
            command=self._browse_input_file
        )
        browse_input_btn.pack(side=tk.LEFT)
        
        # ===== Output File Section =====
        output_frame = ttk.LabelFrame(container, text="Output File", padding="15")
        output_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.output_path_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var, width=60)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_output_btn = ttk.Button(
            output_frame,
            text="Browse...",
            command=self._browse_output_file
        )
        browse_output_btn.pack(side=tk.LEFT)
        
        # ===== Encryption Options =====
        options_frame = ttk.LabelFrame(container, text="Encryption Options", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Key method selection
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
        random_key_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        existing_key_radio = ttk.Radiobutton(
            key_method_frame,
            text="Existing Key",
            variable=self.key_method_var,
            value="existing",
            command=self._update_key_method
        )
        existing_key_radio.pack(side=tk.LEFT)
        
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
        password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.show_password_var = tk.BooleanVar()
        show_password_check = ttk.Checkbutton(
            self.password_frame,
            text="Show",
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        show_password_check.pack(side=tk.LEFT)
        
        # Random key options
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
        
        # Existing key selection
        self.existing_key_frame = ttk.Frame(options_frame)
        
        tk.Label(self.existing_key_frame, text="Select Key:").pack(side=tk.LEFT, padx=(0, 10))
        self.key_list_var = tk.StringVar()
        self.key_combo = ttk.Combobox(
            self.existing_key_frame,
            textvariable=self.key_list_var,
            state="readonly",
            width=35
        )
        self.key_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_keys_btn = ttk.Button(
            self.existing_key_frame,
            text="Refresh",
            command=self._refresh_key_list
        )
        refresh_keys_btn.pack(side=tk.LEFT)
        
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
        
        # Additional options
        self.use_hmac_var = tk.BooleanVar(value=True)
        hmac_check = ttk.Checkbutton(
            options_frame,
            text="Use HMAC Authentication (Recommended)",
            variable=self.use_hmac_var
        )
        hmac_check.pack(anchor=tk.W, pady=(0, 5))
        
        self.secure_delete_var = tk.BooleanVar(value=False)
        secure_delete_check = ttk.Checkbutton(
            options_frame,
            text="Securely delete original file after encryption",
            variable=self.secure_delete_var
        )
        secure_delete_check.pack(anchor=tk.W)
        
        # ===== Progress Bar =====
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
            text="🔒 Encrypt File",
            command=self._encrypt_file,
            width=20
        )
        self.encrypt_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.decrypt_btn = ttk.Button(
            button_frame,
            text="🔓 Decrypt File",
            command=self._decrypt_file,
            width=20
        )
        self.decrypt_btn.pack(side=tk.LEFT)
        
        # Initialize UI state
        self._update_key_method()
    
    def _browse_input_file(self):
        """Browse for input file."""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("All Files", "*.*")]
        )
        if filename:
            self.input_path_var.set(filename)
            
            # Auto-suggest output filename
            if not self.output_path_var.get():
                if self.key_method_var.get() == "password" or self.key_method_var.get() == "random":
                    self.output_path_var.set(filename + ".enc")
                else:
                    if filename.endswith(".enc"):
                        self.output_path_var.set(filename[:-4])
    
    def _browse_output_file(self):
        """Browse for output file."""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            filetypes=[("All Files", "*.*")]
        )
        if filename:
            self.output_path_var.set(filename)
    
    def _update_key_method(self):
        """Update UI based on selected key method."""
        method = self.key_method_var.get()
        
        # Hide all method-specific frames
        self.password_frame.pack_forget()
        self.random_key_frame.pack_forget()
        self.existing_key_frame.pack_forget()
        
        # Show relevant frame
        if method == "password":
            self.password_frame.pack(fill=tk.X, pady=(0, 10))
        elif method == "random":
            self.random_key_frame.pack(fill=tk.X, pady=(0, 10))
        elif method == "existing":
            self.existing_key_frame.pack(fill=tk.X, pady=(0, 10))
            self._refresh_key_list()
    
    def _toggle_password_visibility(self):
        """Toggle password visibility."""
        show = self.show_password_var.get()
        for widget in self.password_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.config(show="" if show else "*")
    
    def _refresh_key_list(self):
        """Refresh list of available keys."""
        keys = self.keystore.list_keys()
        key_ids = [key[0] for key in keys]
        self.key_combo['values'] = key_ids
        if key_ids:
            self.key_combo.current(0)
    
    def _encrypt_file(self):
        """Handle file encryption."""
        # Validate inputs
        if not self.input_path_var.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not self.output_path_var.get():
            messagebox.showerror("Error", "Please specify an output file")
            return
        
        # Run encryption in background thread
        thread = threading.Thread(target=self._do_encrypt, daemon=True)
        thread.start()
    
    def _do_encrypt(self):
        """Perform encryption (runs in background thread)."""
        try:
            # Disable buttons
            self.encrypt_btn.config(state=tk.DISABLED)
            self.decrypt_btn.config(state=tk.DISABLED)
            
            # Start progress bar
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
            self.progress_label.config(text="Encrypting file...")
            self.main_app.set_status("Encrypting...", "blue")
            
            # Get parameters
            input_path = self.input_path_var.get()
            output_path = self.output_path_var.get()
            key_method = self.key_method_var.get()
            key_size = self.key_size_var.get()
            use_hmac = self.use_hmac_var.get()
            secure_del = self.secure_delete_var.get()
            
            # Generate or get key
            key = None
            salt = None
            
            if key_method == "password":
                password = self.password_var.get()
                if not password:
                    raise ValueError("Password is required")
                key, salt = generate_key(password, key_size)
            
            elif key_method == "random":
                key, salt = generate_key(None, key_size)
                
                # Save key
                key_id = self.key_id_var.get()
                if key_id:
                    self.keystore.save_key(key_id, key, {"file": input_path})
                else:
                    # Auto-generate key ID
                    key_id = f"key_{os.path.basename(input_path)}"
                    self.keystore.save_key(key_id, key, {"file": input_path})
                
                # Also save to file
                key_file = output_path + ".key"
                save_key_to_file(key, key_file, key_id, {"file": input_path})
            
            elif key_method == "existing":
                key_id = self.key_list_var.get()
                if not key_id:
                    raise ValueError("Please select a key")
                key = self.keystore.get_key(key_id)
            
            # Encrypt file
            encrypt_file(input_path, output_path, key, salt=salt, use_hmac=use_hmac)
            
            # Secure delete if requested
            if secure_del:
                self.progress_label.config(text="Securely deleting original file...")
                secure_delete(input_path)
            
            # Stop progress bar
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_var.set(100)
            self.progress_label.config(text="✓ Encryption complete!")
            self.main_app.set_status("File encrypted successfully", "green")
            
            # Show success message
            messagebox.showinfo(
                "Success",
                f"File encrypted successfully!\n\nOutput: {output_path}"
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
    
    def _decrypt_file(self):
        """Handle file decryption."""
        # Validate inputs
        if not self.input_path_var.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not self.output_path_var.get():
            messagebox.showerror("Error", "Please specify an output file")
            return
        
        # Run decryption in background thread
        thread = threading.Thread(target=self._do_decrypt, daemon=True)
        thread.start()
    
    def _do_decrypt(self):
        """Perform decryption (runs in background thread)."""
        try:
            # Disable buttons
            self.encrypt_btn.config(state=tk.DISABLED)
            self.decrypt_btn.config(state=tk.DISABLED)
            
            # Start progress bar
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
            self.progress_label.config(text="Decrypting file...")
            self.main_app.set_status("Decrypting...", "blue")
            
            # Get parameters
            input_path = self.input_path_var.get()
            output_path = self.output_path_var.get()
            key_method = self.key_method_var.get()
            key_size = self.key_size_var.get()
            use_hmac = self.use_hmac_var.get()
            
            # Get key
            key = None
            password = None
            
            if key_method == "password":
                password = self.password_var.get()
                if not password:
                    raise ValueError("Password is required")
            
            elif key_method == "existing" or key_method == "random":
                key_id = self.key_list_var.get()
                if key_id:
                    key = self.keystore.get_key(key_id)
                else:
                    # Try to find auto-saved key file
                    key_file = input_path + ".key"
                    if os.path.exists(key_file):
                        key, _ = load_key_from_file(key_file)
                    else:
                        raise ValueError("No key found. Please select a key or use password.")
            
            # Decrypt file
            decrypt_file(
                input_path,
                output_path,
                password=password,
                key=key,
                key_size=key_size,
                use_hmac=use_hmac
            )
            
            # Stop progress bar
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_var.set(100)
            self.progress_label.config(text="✓ Decryption complete!")
            self.main_app.set_status("File decrypted successfully", "green")
            
            # Show success message
            messagebox.showinfo(
                "Success",
                f"File decrypted successfully!\n\nOutput: {output_path}"
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
