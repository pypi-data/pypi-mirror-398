# gui/settings_dialog.py

"""
Settings and configuration dialog for GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class SettingsManager:
    """Manage application settings."""
    
    DEFAULT_SETTINGS = {
        "default_key_size": 32,
        "use_hmac": True,
        "secure_delete": False,
        "compression": True,
        "parallel_workers": 4,
        "theme": "default",
        "auto_save_keys": True,
        "confirm_delete": True
    }
    
    def __init__(self, config_file="settings.json"):
        """
        Initialize settings manager.
        
        Args:
            config_file: Path to settings file
        """
        self.config_file = config_file
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """Load settings from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                # Merge with defaults (for new settings)
                settings = self.DEFAULT_SETTINGS.copy()
                settings.update(loaded)
                return settings
            except Exception:
                pass
        
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        """Save settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value."""
        self.settings[key] = value
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self.DEFAULT_SETTINGS.copy()


class SettingsDialog(tk.Toplevel):
    """Settings dialog window."""
    
    def __init__(self, parent, settings_manager):
        """
        Initialize settings dialog.
        
        Args:
            parent: Parent window
            settings_manager: SettingsManager instance
        """
        super().__init__(parent)
        
        self.parent = parent
        self.settings = settings_manager
        
        # Configure window
        self.title("Settings")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Center window
        self.transient(parent)
        self.grab_set()
        
        # Create widgets
        self._create_widgets()
        
        # Load current settings
        self._load_current_settings()
    
    def _create_widgets(self):
        """Create all widgets."""
        # Main container
        container = ttk.Frame(self, padding="20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(
            container,
            text="Application Settings",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=(0, 20))
        
        # Notebook for categories
        notebook = ttk.Notebook(container)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # ===== Encryption Settings Tab =====
        encryption_frame = ttk.Frame(notebook, padding="15")
        notebook.add(encryption_frame, text="Encryption")
        
        # Default Key Size
        ttk.Label(
            encryption_frame,
            text="Default Key Size:",
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.key_size_var = tk.IntVar(value=32)
        
        key_size_frame = ttk.Frame(encryption_frame)
        key_size_frame.pack(anchor=tk.W, pady=(0, 15))
        
        ttk.Radiobutton(
            key_size_frame,
            text="AES-128 (16 bytes)",
            variable=self.key_size_var,
            value=16
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Radiobutton(
            key_size_frame,
            text="AES-256 (32 bytes)",
            variable=self.key_size_var,
            value=32
        ).pack(side=tk.LEFT)
        
        # HMAC
        self.hmac_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            encryption_frame,
            text="Use HMAC authentication (recommended)",
            variable=self.hmac_var
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Secure Delete
        self.secure_delete_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            encryption_frame,
            text="Secure delete original files after encryption",
            variable=self.secure_delete_var
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Auto-save Keys
        self.auto_save_keys_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            encryption_frame,
            text="Auto-save randomly generated keys to keystore",
            variable=self.auto_save_keys_var
        ).pack(anchor=tk.W)
        
        # ===== Folder Settings Tab =====
        folder_frame = ttk.Frame(notebook, padding="15")
        notebook.add(folder_frame, text="Folder Operations")
        
        # Compression
        self.compression_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            folder_frame,
            text="Enable compression for folder encryption",
            variable=self.compression_var
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Parallel Workers
        ttk.Label(
            folder_frame,
            text="Parallel Processing Workers:",
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))
        
        worker_frame = ttk.Frame(folder_frame)
        worker_frame.pack(anchor=tk.W, pady=(0, 10))
        
        self.workers_var = tk.IntVar(value=4)
        
        ttk.Label(worker_frame, text="Workers:").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Spinbox(
            worker_frame,
            from_=1,
            to=16,
            textvariable=self.workers_var,
            width=5
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            folder_frame,
            text="Higher values may be faster but use more CPU",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor=tk.W)
        
        # ===== General Settings Tab =====
        general_frame = ttk.Frame(notebook, padding="15")
        notebook.add(general_frame, text="General")
        
        # Theme (placeholder for future)
        ttk.Label(
            general_frame,
            text="Theme:",
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.theme_var = tk.StringVar(value="default")
        
        theme_combo = ttk.Combobox(
            general_frame,
            textvariable=self.theme_var,
            values=["default", "dark", "light"],
            state="readonly",
            width=20
        )
        theme_combo.pack(anchor=tk.W, pady=(0, 15))
        
        # Confirm Delete
        self.confirm_delete_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            general_frame,
            text="Confirm before deleting keys",
            variable=self.confirm_delete_var
        ).pack(anchor=tk.W)
        
        # ===== Buttons =====
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_settings,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Apply",
            command=self._apply_settings,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
            width=15
        ).pack(side=tk.RIGHT)
    
    def _load_current_settings(self):
        """Load current settings into widgets."""
        self.key_size_var.set(self.settings.get("default_key_size", 32))
        self.hmac_var.set(self.settings.get("use_hmac", True))
        self.secure_delete_var.set(self.settings.get("secure_delete", False))
        self.compression_var.set(self.settings.get("compression", True))
        self.workers_var.set(self.settings.get("parallel_workers", 4))
        self.theme_var.set(self.settings.get("theme", "default"))
        self.auto_save_keys_var.set(self.settings.get("auto_save_keys", True))
        self.confirm_delete_var.set(self.settings.get("confirm_delete", True))
    
    def _apply_settings(self):
        """Apply settings without closing."""
        self.settings.set("default_key_size", self.key_size_var.get())
        self.settings.set("use_hmac", self.hmac_var.get())
        self.settings.set("secure_delete", self.secure_delete_var.get())
        self.settings.set("compression", self.compression_var.get())
        self.settings.set("parallel_workers", self.workers_var.get())
        self.settings.set("theme", self.theme_var.get())
        self.settings.set("auto_save_keys", self.auto_save_keys_var.get())
        self.settings.set("confirm_delete", self.confirm_delete_var.get())
        
        messagebox.showinfo("Settings", "Settings applied successfully!")
    
    def _save_settings(self):
        """Save settings and close."""
        self._apply_settings()
        
        if self.settings.save_settings():
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to save settings to file")
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?"
        ):
            self.settings.reset_to_defaults()
            self._load_current_settings()
            messagebox.showinfo("Settings", "Settings reset to defaults")
