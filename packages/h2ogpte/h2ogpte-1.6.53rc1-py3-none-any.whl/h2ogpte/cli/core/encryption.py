import os
import base64
import hashlib
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureStorage:
    """Handles encryption/decryption of sensitive data."""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.key_file = config_dir / ".keyfile"
        self._cipher_suite = None

    def _get_machine_id(self) -> bytes:
        """Generate a machine-specific identifier."""
        # Use machine-specific data for key generation
        import platform
        import socket

        machine_data = (
            platform.node()
            + platform.machine()
            + platform.processor()
            + str(os.getuid() if hasattr(os, "getuid") else "windows")
        ).encode()

        return hashlib.sha256(machine_data).digest()

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                return f.read()

        # Create new key based on machine ID
        machine_id = self._get_machine_id()

        # Use PBKDF2 to derive a key from machine ID
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"hbot_salt_2024",  # Static salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id))

        # Save key to file
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.key_file, "wb") as f:
            f.write(key)

        # Set restrictive permissions
        os.chmod(self.key_file, 0o600)

        return key

    def _get_cipher_suite(self) -> Fernet:
        """Get cipher suite for encryption/decryption."""
        if self._cipher_suite is None:
            key = self._get_or_create_key()
            self._cipher_suite = Fernet(key)
        return self._cipher_suite

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not data:
            return ""

        cipher_suite = self._get_cipher_suite()
        encrypted_data = cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not encrypted_data:
            return ""

        try:
            cipher_suite = self._get_cipher_suite()
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            # Return empty string if decryption fails (corrupted or wrong key)
            return ""

    def is_encrypted(self, data: str) -> bool:
        """Check if data appears to be encrypted."""
        if not data:
            return False

        # Simple heuristic: encrypted data should be base64-like and long
        try:
            # Check if it's valid base64
            base64.urlsafe_b64decode(data.encode())
            # Encrypted data should be long (>50 chars) and not look like a normal API key
            return len(data) > 50 and not data.startswith("sk-")
        except:
            return False
