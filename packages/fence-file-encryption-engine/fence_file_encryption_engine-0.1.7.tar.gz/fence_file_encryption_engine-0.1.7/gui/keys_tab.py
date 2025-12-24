# gui/keys_tab.py

"""
Key management tab for GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os

from core.key_store import KeyStore, save_key_to_file, load_key_from_file
from core.aes_crypto import generate_key


class KeyManagementTab(ttk.Frame):
    """Tab for managing encryption keys."""
    
    def __init__(self, parent, main_app):
        """
        Initialize key management tab.
        
        Args:
            parent: Parent widget
            main_app: Reference to main application
        """
        super().__init__(parent)
        self.main_app = main_app
        self.keystore = KeyStore()
        
        self._create_widgets()
        self._refresh_key_list()
    
    def _create_widgets(self):
        """Create all widgets for the tab."""
        # Main container
        container = ttk.Frame(self, padding="20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(
            container,
            text="Key Management",
            font=('Arial', 16, 'bold')
        )
        title.pack(pady=(0, 20))
        
        # ===== Key List Section =====
        list_frame = ttk.LabelFrame(container, text="Stored Keys", padding="15")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create Treeview
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Tree widget
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Key ID", "Created", "Metadata"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("Key ID", text="Key ID")
        self.tree.heading("Created", text="Created Date")
        self.tree.heading("Metadata", text="Metadata")
        
        self.tree.column("Key ID", width=200)
        self.tree.column("Created", width=180)
        self.tree.column("Metadata", width=300)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # ===== Action Buttons =====
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(
            button_frame,
            text="🔄 Refresh",
            command=self._refresh_key_list,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="➕ Generate New Key",
            command=self._generate_new_key,
            width=18
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="📥 Import Key",
            command=self._import_key,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="📤 Export Key",
            command=self._export_key,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="🗑️ Delete Key",
            command=self._delete_key,
            width=15
        ).pack(side=tk.LEFT)
    
    def _refresh_key_list(self):
        """Refresh the list of keys."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get keys from keystore
        keys = self.keystore.list_keys()
        
        # Add to tree
        for key_id, created, metadata in keys:
            # Format metadata
            meta_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
            if not meta_str:
                meta_str = "(no metadata)"
            
            # Format created date
            created_display = created[:19] if len(created) > 19 else created
            
            self.tree.insert("", tk.END, values=(key_id, created_display, meta_str))
        
        self.main_app.set_status(f"Loaded {len(keys)} key(s)", "blue")
    
    def _generate_new_key(self):
        """Generate a new random key."""
        # Create dialog for key ID and size
        dialog = tk.Toplevel(self)
        dialog.title("Generate New Key")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        # Key ID
        ttk.Label(dialog, text="Key ID:").pack(pady=(20, 5))
        key_id_var = tk.StringVar()
        key_id_entry = ttk.Entry(dialog, textvariable=key_id_var, width=40)
        key_id_entry.pack(pady=(0, 15))
        key_id_entry.focus()
        
        # Key size
        ttk.Label(dialog, text="Key Size:").pack(pady=(0, 5))
        key_size_var = tk.IntVar(value=32)
        
        size_frame = ttk.Frame(dialog)
        size_frame.pack(pady=(0, 20))
        
        ttk.Radiobutton(
            size_frame,
            text="AES-128 (16 bytes)",
            variable=key_size_var,
            value=16
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            size_frame,
            text="AES-256 (32 bytes)",
            variable=key_size_var,
            value=32
        ).pack(side=tk.LEFT, padx=10)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack()
        
        def on_generate():
            key_id = key_id_var.get().strip()
            if not key_id:
                messagebox.showerror("Error", "Please enter a key ID")
                return
            
            # Check if key ID already exists
            existing_keys = [k[0] for k in self.keystore.list_keys()]
            if key_id in existing_keys:
                messagebox.showerror("Error", "Key ID already exists")
                return
            
            # Generate key
            key, _ = generate_key(None, key_size_var.get())
            
            # Save to keystore
            self.keystore.save_key(key_id, key, {
                "generated": "GUI",
                "key_size": key_size_var.get()
            })
            
            # Refresh list
            self._refresh_key_list()
            
            messagebox.showinfo("Success", f"Key '{key_id}' generated successfully!")
            dialog.destroy()
        
        ttk.Button(
            button_frame,
            text="Generate",
            command=on_generate
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def _import_key(self):
        """Import a key from file."""
        filename = filedialog.askopenfilename(
            title="Select Key File",
            filetypes=[("Key Files", "*.key"), ("All Files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Load key from file
            key, metadata = load_key_from_file(filename)
            
            # Ask for key ID
            key_id = simpledialog.askstring(
                "Import Key",
                "Enter Key ID:",
                initialvalue=os.path.basename(filename).replace(".key", "")
            )
            
            if not key_id:
                return
            
            # Save to keystore
            self.keystore.save_key(key_id, key, metadata)
            
            # Refresh list
            self._refresh_key_list()
            
            messagebox.showinfo("Success", f"Key imported as '{key_id}'")
        
        except Exception as e:
            messagebox.showerror("Import Error", str(e))
    
    def _export_key(self):
        """Export selected key to file."""
        # Get selected item
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a key to export")
            return
        
        # Get key ID
        item = self.tree.item(selection[0])
        key_id = item['values'][0]
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Export Key",
            defaultextension=".key",
            initialfile=f"{key_id}.key",
            filetypes=[("Key Files", "*.key"), ("All Files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Get key
            key = self.keystore.get_key(key_id)
            
            # Get metadata
            keys_list = self.keystore.list_keys()
            metadata = {}
            for kid, _, meta in keys_list:
                if kid == key_id:
                    metadata = meta
                    break
            
            # Save to file
            save_key_to_file(key, filename, key_id, metadata)
            
            messagebox.showinfo("Success", f"Key exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
    
    def _delete_key(self):
        """Delete selected key."""
        # Get selected item
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a key to delete")
            return
        
        # Get key ID
        item = self.tree.item(selection[0])
        key_id = item['values'][0]
        
        # Confirm deletion
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete key '{key_id}'?\n\n"
            "This action cannot be undone."
        ):
            try:
                self.keystore.delete_key(key_id)
                self._refresh_key_list()
                messagebox.showinfo("Success", f"Key '{key_id}' deleted")
            except Exception as e:
                messagebox.showerror("Delete Error", str(e))
