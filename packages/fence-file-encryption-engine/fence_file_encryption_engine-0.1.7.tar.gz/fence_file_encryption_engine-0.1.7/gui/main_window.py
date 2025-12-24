# gui/main_window.py

"""Main GUI window for FENCE (File ENCryption Engine)."""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.file_tab import FileEncryptionTab
from gui.folder_tab import FolderEncryptionTab
from gui.keys_tab import KeyManagementTab
from gui.settings_dialog import SettingsManager, SettingsDialog


class AESEncryptionGUI:
    """Main application window with tabbed interface."""
    
    def __init__(self, root):
        """
        Initialize the main GUI window.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("FENCE")
        self.root.geometry("950x800")
        
        # Set minimum window size
        self.root.minsize(900, 700)
        
        # Initialize settings
        self.settings = SettingsManager()
        
        # Configure root window
        self.root.configure(bg='#f0f0f0')
        
        # Set window icon (if available)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Create UI
        self._create_menu()
        self._create_header()
        self._create_status_bar()  # Create status bar BEFORE notebook
        self._create_notebook()
        
        # Center window on screen
        self._center_window()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self._show_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Reference", command=self._show_help)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_header(self):
        """Create header with title and logo."""
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="🔐 FENCE",
            font=('Arial', 24, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="File ENCryption Engine",
            font=('Arial', 11),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        subtitle_label.pack()
    
    def _create_notebook(self):
        """Create tabbed notebook interface."""
        # Create notebook
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.file_tab = FileEncryptionTab(self.notebook, self)
        self.folder_tab = FolderEncryptionTab(self.notebook, self)
        self.keys_tab = KeyManagementTab(self.notebook, self)
        
        # Add tabs to notebook
        self.notebook.add(self.file_tab, text="  File Encryption  ")
        self.notebook.add(self.folder_tab, text="  Folder Encryption  ")
        self.notebook.add(self.keys_tab, text="  Key Management  ")
    
    def _create_status_bar(self):
        """Create status bar at bottom."""
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg='#ecf0f1',
            padx=10,
            pady=5
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _center_window(self):
        """Center window on screen."""
        self.root.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Get window dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"+{x}+{y}")
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.root, self.settings)
        self.root.wait_window(dialog)
    
    def _show_help(self):
        """Show quick reference help."""
        help_text = """
FENCE - Quick Reference

FILE ENCRYPTION:
1. Select input file
2. Choose output location
3. Enter password or select key
4. Click Encrypt/Decrypt

FOLDER ENCRYPTION:
1. Select folder to encrypt
2. Choose output location
3. Set options (compression, parallel processing)
4. Enter password or select key
5. Click Encrypt/Decrypt

KEY MANAGEMENT:
• Random keys are automatically saved
• Use Key Manager tab to view/delete keys
• Export keys for backup

SECURITY TIPS:
✓ Use strong passwords (12+ characters)
✓ Enable HMAC (default)
✓ Back up encryption keys
✓ Use AES-256 for maximum security

For complete documentation, see Help → Documentation
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Quick Reference")
        help_window.geometry("600x500")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=20, pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        
        close_btn = tk.Button(help_window, text="Close", command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def _show_documentation(self):
        """Open documentation in default browser or text viewer."""
        doc_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'DOCS',
            'DOCUMENTATION.md'
        )
        
        if os.path.exists(doc_path):
            import webbrowser
            webbrowser.open(doc_path)
        else:
            messagebox.showinfo(
                "Documentation",
                "Documentation file not found.\nPlease see DOCUMENTATION.md in the project folder."
            )
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
FENCE (File ENCryption Engine)
Version 2.0

A comprehensive file and folder encryption tool
using AES-128 and AES-256 encryption.

Features:
• File and folder encryption
• Password-based and random key encryption
• HMAC authentication
• Parallel processing
• Secure key management

Author: Kushagra Bhardwaj
GitHub: bhardwaj-kushagra/FENCE

© 2025 - MIT License
        """

        messagebox.showinfo("About FENCE", about_text)
    
    def _on_closing(self):
        """Handle window close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
    
    def set_status(self, message, color='black'):
        """
        Update status bar message.
        
        Args:
            message: Status message to display
            color: Text color (default: black)
        """
        self.status_bar.config(text=message, fg=color)
        self.root.update_idletasks()
    
    def run(self):
        """Start the GUI event loop."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    root = tk.Tk()
    app = AESEncryptionGUI(root)
    app.run()


if __name__ == "__main__":
    main()
