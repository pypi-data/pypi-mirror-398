# FENCE (File ENCryption Engine)

A comprehensive Python-based file and folder encryption tool using AES (Advanced Encryption Standard). Supports AES-128 and AES-256 encryption with password-based or random key generation.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### Complete Implementation ✅

- **🔐 Dual Encryption Modes**: AES-128 (128-bit) and AES-256 (256-bit)
- **📁 File & Folder Support**: Encrypt single files or entire directory trees
- **🔑 Flexible Key Management**: Password-based (PBKDF2) or random key generation
- **💾 Secure Key Storage**: Built-in keystore with optional encryption
- **✓ HMAC Authentication**: Detect tampering with encrypted files (HMAC-SHA256)
- **⚡ Batch Processing**: Parallel encryption for improved performance
- **📦 Compression Support**: Optional ZIP compression before encryption
- **🗑️ Secure File Deletion**: Multi-pass overwrite before deletion
- **🖥️ Comprehensive CLI**: Feature-rich command-line interface
- **🖼️ GUI Interface**: User-friendly graphical interface with Tkinter
- **🧪 Complete Test Suite**: 38 unit tests with 100% pass rate
- **📦 Desktop App**: Standalone executables with PyInstaller

## 🚀 Quick Start

### Install via PyPI (CLI/GUI)

Install and use the tool like this:

```powershell
pip install fence-file-encryption-engine

# CLI
fence --help

# GUI (Tkinter)
fence-gui
```

TestPyPI (for verification before real PyPI):
```powershell
python -m pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple fence-file-encryption-engine==0.1.6
```

### Installation

```powershell
# Clone the repository
git clone https://github.com/bhardwaj-kushagra/FENCE.git
cd FENCE

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

**GUI Mode (Recommended for beginners):**
```powershell
python run_gui.py
```

**CLI - Encrypt a file:**
```powershell
python -m cli.aes_cli encrypt myfile.txt --password "YourSecurePassword" --output myfile.txt.enc
```

**CLI - Decrypt a file:**
```powershell
python -m cli.aes_cli decrypt myfile.txt.enc --password "YourSecurePassword" --output myfile.txt
```

**CLI - Encrypt a folder:**
```powershell
python -m cli.aes_cli encrypt-folder ./data --output ./encrypted --password "YourPassword"
```


## 🚧 Automated Desktop Builds (GitHub Actions)

This repository includes a GitHub Actions workflow that builds platform binaries using PyInstaller and attaches them to a GitHub Release. It triggers when you push a tag matching `v*.*.*` (for example `v1.0.0`) or when you run it manually from the Actions tab.

How to create a release (trigger build):

```powershell
# create a tag locally
git tag v1.0.0
git push origin v1.0.0
```

Where is the .exe? Why don't I see it locally?
- GitHub Actions builds run on GitHub-hosted runners; binaries are not written into your local workspace.
- Download them from either:
	1) Actions → Build and Release → select the run → Artifacts (per-OS zips), or
	2) Releases → select the tag you pushed → Assets (per-OS binaries).

Manually run the workflow (no tag):
1. Push your latest changes to GitHub.
2. Go to the Actions tab → Build and Release → Run workflow.
3. Pick a branch and click Run.

Local one-off build (Windows):
```powershell
pip install pyinstaller
pyinstaller --clean run_gui.spec
# Output: .\dist\AES-Tool-GUI.exe
```

Notes:
- The workflow currently builds on Windows runners only. Binaries are produced by PyInstaller.
- If you have non-Python assets (icons, data files), keep `run_gui.spec`; it bundles GUI data and embeds `gui/icon.ico` if present.
- Optional: add code signing and a release checklist for production builds.

Windows-specific notes:
- The Windows build will produce an `AES-Tool-GUI.exe` in the `dist` folder on the runner. It will be available via the Release assets and/or workflow Artifacts.
- The GUI artifact may be a zipped folder (one-dir) containing `AES-Tool-GUI.exe`; download the `.zip`, extract, then run `AES-Tool-GUI.exe`.
- To test a Windows build locally, run on a Windows machine; cross-building a Windows EXE on Linux is not officially supported by PyInstaller.

Adding icons or data files:
- Place GUI assets inside the `gui/` directory (e.g., `gui/icon.ico`). The included `run_gui.spec` collects GUI package data and will bundle assets automatically when you run `pyinstaller run_gui.spec`.
- If you need custom packaging behavior, modify `run_gui.spec` and commit it; the workflow will prefer it automatically.

## 📚 Documentation

- **[DOCS/GUI_GUIDE.md](DOCS/GUI_GUIDE.md)** - Comprehensive GUI user guide with screenshots and tutorials
- **[DOCS/DOCUMENTATION.md](DOCS/DOCUMENTATION.md)** - Complete guide with cryptographic theory, architecture, detailed usage, and a Crypto Primer for newcomers
- **[DOCS/QUICK_REFERENCE.md](DOCS/QUICK_REFERENCE.md)** - Quick command reference and cheat sheet
- **[CHANGES.md](CHANGES.md)** - Detailed changelog and implementation notes

## 📦 Publish to (Test)PyPI via GitHub Actions

This repo includes a workflow at `.github/workflows/publish-pypi.yml`:

- **TestPyPI**: Actions → "Publish to PyPI" → Run workflow → choose `testpypi`
- **PyPI**: push a version tag like `v0.1.6` (publishes automatically)

Required GitHub repo secrets:
- `TEST_PYPI_API_TOKEN` (token created on https://test.pypi.org/)
- `PYPI_API_TOKEN` (token created on https://pypi.org/)

Important: PyPI and TestPyPI tokens are different and not interchangeable.

## 🏗️ Project Structure

```
FENCE/
├── cli/
│   ├── __init__.py
│   └── aes_cli.py          # Command-line interface
├── core/
│   ├── __init__.py
│   ├── aes_crypto.py       # Core encryption/decryption
│   ├── key_store.py        # Key management
│   └── batch_encrypt.py    # Folder & batch operations
├── gui/
│   ├── __init__.py
│   ├── main_window.py      # Main GUI window
│   ├── file_tab.py         # File encryption tab
│   ├── folder_tab.py       # Folder encryption tab
│   ├── keys_tab.py         # Key management tab
│   └── settings_dialog.py  # Settings configuration
├── utils/
│   ├── __init__.py
│   └── logger.py           # Colored console output
├── tests/
│   ├── __init__.py
│   ├── test_aes_crypto.py
│   ├── test_key_store.py
│   ├── test_batch_encrypt.py
│   └── run_tests.py
├── DOCS/
│   ├── DOCUMENTATION.md
│   └── QUICK_REFERENCE.md
├── CHANGES.md
├── requirements.txt
└── README.md
```

## 🔒 Security Features

- **AES-256-CBC**: Industry-standard encryption algorithm
- **PBKDF2**: 100,000 iterations for password-based key derivation (OWASP recommendation)
- **HMAC-SHA256**: Authentication to detect tampering and corruption
- **Secure Random**: Uses `secrets` module for cryptographically strong randomness
- **Padding Validation**: Prevents padding oracle attacks
- **Secure Delete**: 3-pass overwrite for sensitive file deletion

## 🧪 Testing

Run the complete test suite:

```powershell
python tests\run_tests.py
```

Run specific test modules:
```powershell
python -m unittest tests.test_aes_crypto
python -m unittest tests.test_key_store
python -m unittest tests.test_batch_encrypt
```

## 📦 Requirements

- Python 3.8 or higher
- pycryptodome >= 3.18.0
- rich >= 13.0.0

Install with:
```powershell
pip install -r requirements.txt
```

## 🎯 Use Cases

- **Personal Data Backup**: Encrypt sensitive files before cloud storage
- **Secure File Sharing**: Encrypt files for secure transmission
- **Compliance**: Meet data encryption requirements
- **Privacy**: Protect confidential documents
- **Development**: Encrypt configuration files with secrets

## 🔧 Command Overview

| Command | Description |
|---------|-------------|
| `encrypt` | Encrypt a single file |
| `decrypt` | Decrypt a single file |
| `encrypt-folder` | Encrypt all files in a folder |
| `decrypt-folder` | Decrypt all files in a folder |
| `keystore list` | List all stored keys |
| `keystore delete` | Delete a stored key |

**Get help:**
```powershell
python -m cli.aes_cli --help
python -m cli.aes_cli encrypt --help
```

## 📊 Project Phases

| Phase | Status | Features |
|-------|--------|----------|
| **Phase 1** | ✅ Complete | Core AES encryption, CLI implementation |
| **Phase 2** | ✅ Complete | Folder encryption, parallel processing, compression |
| **Phase 3** | ✅ Complete | GUI development (Tkinter) |
| **Phase 4** | ✅ Complete | Desktop app packaging (PyInstaller, Windows) |

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Add tests for new functionality
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Kushagra Bhardwaj**
- GitHub: [@bhardwaj-kushagra](https://github.com/bhardwaj-kushagra)
- Repository: [FENCE](https://github.com/bhardwaj-kushagra/FENCE)

## 🙏 Acknowledgments

- **PyCryptodome** - Cryptographic library
- **Rich** - Terminal formatting
- **NIST** - AES standard specification

## 🛠️ Troubleshooting

- **Buttons not visible**: The Encrypt/Decrypt buttons are at the bottom of the File tab. Resize the window if they’re not visible. The default size is now 950x800 (minimum 900x700).
- **Release creation fails (403)**: GitHub Actions needs `permissions: contents: write` in the workflow to publish releases. This repository includes that permission.

## 📦 Publish to PyPI (recommended: TestPyPI first)

```powershell
# Install packaging tools
python -m pip install --upgrade build twine

# Build wheel + sdist
python -m build

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Verify install from TestPyPI
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple fence-file-encryption-engine

# Upload to PyPI
python -m twine upload dist/*
```

## 📝 Version

**Current Version:** 2.0  
**Last Updated:** October 13, 2025

---

**⭐ Star this repository if you find it useful!**

For detailed documentation, see [DOCS/DOCUMENTATION.md](DOCS/DOCUMENTATION.md)  
For quick reference, see [DOCS/QUICK_REFERENCE.md](DOCS/QUICK_REFERENCE.md)

