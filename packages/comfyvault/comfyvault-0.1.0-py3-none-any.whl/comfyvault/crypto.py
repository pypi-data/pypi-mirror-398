import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.exceptions import InvalidSignature

def generate_salt(size: int = 16) -> bytes:
    """Generate a random salt."""
    return os.urandom(size)

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 32-byte key from the password and salt using PBKDF2HMAC-SHA256.
    We use 600,000 iterations for high security against brute-force.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt bytes using Fernet (AES-128-CBC + HMAC)."""
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_data(token: bytes, key: bytes) -> bytes:
    """Decrypt bytes using Fernet. Raises InvalidToken if key is wrong."""
    f = Fernet(key)
    return f.decrypt(token)
