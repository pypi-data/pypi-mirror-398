# Secure Run Manifest (sr-ms)

**Version:** 0.1.0
**Author:** Viren  
**License:** Proprietary © 2025  

Secure Run Manifest (`sr-ms`) is a lightweight Python tool to securely lock, manage, and run Python scripts. It uses XOR encryption with PBKDF2 key derivation and allows scripts to be run from memory without exposing the source on disk.

## Features
- **Encrypt scripts:** Protect Python files with a password.  
- **Memory execution:** Run scripts without writing decrypted code to disk.  
- **Export & Import:** Copy locked scripts in and out easily.  
- **Cache safety:** Decrypted scripts are zeroed from memory after use.  
- **Reset & Delete:** Remove single scripts or reset all locked files.  
- **Cross-platform:** Works on Windows, Linux, and macOS.

## Overview
`sr-ms` lets developers quickly secure Python scripts. Files are hashed with SHA256 for integrity. Decrypted scripts are only in memory and cleared after execution.

## Security Notes
- **Encryption:** XOR + PBKDF2 password-based.  
- **Integrity check:** SHA256 ensures files aren't tampered with.  
- **Memory safety:** Runtime cache is zeroed after use.  
- **Disclaimer:** Use responsibly; author is not liable for misuse.

## Getting Started
1. Install Python 3.  
2. Run scripts using `srms lock <label> <file>` and `srms run <label>`.  
3. Manage scripts with `delete`, `reset`, `export`, `import`, and `labels` and more in the next updates.