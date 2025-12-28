import json
from pathlib import Path
from typing import Dict, List, Optional
from cryptography.fernet import InvalidToken

from . import crypto
from . import storage

class VaultError(Exception):
    pass

class VaultManager:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self._key: Optional[bytes] = None
        self._secrets: Dict[str, List[Dict[str, str]]] = {}

    def is_initialized(self) -> bool:
        return self.vault_path.exists()

    def initialize(self, master_password: str):
        """Initialize a new vault with a master password."""
        if self.is_initialized():
            raise VaultError("Vault already exists.")
        
        salt = crypto.generate_salt()
        key = crypto.derive_key(master_password, salt)
        self._key = key
        self._secrets = {}
        
        self._save(salt)

    def unlock(self, master_password: str):
        """Unlock the vault and load secrets into memory."""
        if not self.is_initialized():
            raise VaultError("Vault not initialized.")
        
        raw_data = storage.load_raw_vault(self.vault_path)
        salt = bytes.fromhex(raw_data["salt"])
        encrypted_blob = raw_data["data"].encode("utf-8")
        
        key = crypto.derive_key(master_password, salt)
        
        try:
            decrypted_json = crypto.decrypt_data(encrypted_blob, key)
            self._secrets = json.loads(decrypted_json)
            self._key = key

            migrated = False
            for service, value in self._secrets.items():
                if isinstance(value, dict):
                    self._secrets[service] = [value]
                    migrated = True
            
            if migrated:
                self._save(salt)
                
        except InvalidToken:
            raise VaultError("Invalid master password.")

    def _save(self, salt: Optional[bytes] = None):
        """Encrypt and save current state to disk."""
        if not self._key:
            raise VaultError("Vault is locked.")
        
        if salt is None:
            raw = storage.load_raw_vault(self.vault_path)
            salt = bytes.fromhex(raw["salt"])

        json_data = json.dumps(self._secrets).encode("utf-8")
        encrypted_data = crypto.encrypt_data(json_data, self._key)
        storage.save_raw_vault(salt, encrypted_data, self.vault_path)

    def add_secret(self, service: str, username: str, password: str):
        if not self._key:
            raise VaultError("Vault is locked.")
        
        if service not in self._secrets:
            self._secrets[service] = []
        
        for entry in self._secrets[service]:
            if entry["username"] == username:
                entry["password"] = password
                self._save()
                return

        self._secrets[service].append({"username": username, "password": password})
        self._save()

    def get_secrets(self, service: str) -> List[Dict[str, str]]:
        """Return list of secrets for a service."""
        if not self._key:
            raise VaultError("Vault is locked.")
        return self._secrets.get(service, [])

    def delete_secret(self, service: str, username: Optional[str] = None):
        """
        Delete a secret. 
        If username is provided, delete that specific entry.
        If username is None or it's the last entry, delete the service entirely.
        """
        if not self._key:
            raise VaultError("Vault is locked.")
        
        if service not in self._secrets:
            return

        if username:
            original_len = len(self._secrets[service])
            self._secrets[service] = [s for s in self._secrets[service] if s["username"] != username]
            
            if len(self._secrets[service]) == 0:
                del self._secrets[service]
            elif len(self._secrets[service]) == original_len:
                pass
        else:
            del self._secrets[service]
            
        self._save()

    def list_services(self) -> List[str]:
        if not self._key:
            raise VaultError("Vault is locked.")
        return list(self._secrets.keys())
