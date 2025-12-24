#!/usr/bin/env python3
# run_gui.py

"""Launcher script for FENCE (File ENCryption Engine) GUI."""

import tkinter as tk
from gui.main_window import AESEncryptionGUI


def main():
    """Main entry point for GUI application."""
    # Create root window
    root = tk.Tk()
    
    # Create application
    app = AESEncryptionGUI(root)
    
    # Start main loop
    root.mainloop()


if __name__ == "__main__":
    main()
