import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

VAULT_FILE = Path.home() / ".secrets.enc"

class StorageError(Exception):
    pass

def load_raw_vault(path: Path = VAULT_FILE) -> Dict[str, str]:
    """
    Load the raw JSON containing salt and encrypted data from disk.
    Expected structure: {"salt": "hex_string", "data": "base64_string"}
    """
    if not path.exists():
        raise FileNotFoundError(f"Vault file not found at {path}")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise StorageError("Vault file is corrupted.")

def save_raw_vault(salt: bytes, encrypted_data: bytes, path: Path = VAULT_FILE):
    """
    Save the salt and encrypted payload to disk.
    """
    payload = {
        "salt": salt.hex(),
        "data": encrypted_data.decode("utf-8")
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)
