# ComfyVault 🔒

A secure, terminal-only password manager for hackers and CLI enthusiasts.

**No GUI. No Cloud. Just you and your encrypted secrets.**

## Features

- 🔐 **Strong Encryption**: AES-256 (via Fernet) with PBKDF2 key derivation.
- 🚀 **Fast**: Instant startup, no laggy Electron apps.
- 📦 **Portable**: Single encrypted file storage (`.secrets.enc`).
- 📋 **clipboard**: Auto-copy passwords to clipboard.
- 🐧 **Cross-Platform**: Windows, macOS, Linux.

## Installation

### From PyPI (Recommended)

```bash
pip install comfyvault
```

### From Source

```bash
git clone https://github.com/abderrahmanyouabd/comfyvault.git
cd comfyvault
poetry install
```

## Usage

**1. Initialize your vault**
```bash
comfyvault init
```

**2. Add a password**
```bash
comfyvault add github "myusername"
# You will be prompted for the password securely
```

**3. Get a password**
```bash
comfyvault get github
# Copies password to clipboard and shows metadata
```

**4. List all services**
```bash
comfyvault list
```

**5. Generate a secure password**
```bash
comfyvault gen --length 20 --symbols
```

## Security Design

- **Master Password**: Never stored. Used to derive the encryption key.
- **Key Derivation**: PBKDF2HMAC-SHA256, 600,000 iterations, random salt.
- **Encryption**: Fernet (AES-128-CBC with HMAC-SHA256). *Note: Cryptography's Fernet guarantees valid encryption.*

## License

MIT
