"""Local encryption utilities for sensitive data protection."""

import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import base64
import json
from datetime import datetime, timezone


class EncryptionKeyManager:
    """Manages encryption keys with secure generation and storage."""

    def __init__(self, key_file_path: Optional[str] = None):
        self.key_file_path = Path(key_file_path or "./encryption.key")
        self._key: Optional[bytes] = None

    def generate_key(self, overwrite: bool = False) -> bytes:
        """Generate a new encryption key and save it to file."""
        if self.key_file_path.exists() and not overwrite:
            raise FileExistsError(f"Key file already exists: {self.key_file_path}")

        # Generate a new Fernet key
        key = Fernet.generate_key()

        # Create key file with restrictive permissions
        self.key_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write key with metadata
        key_data = {
            "key": base64.b64encode(key).decode('utf-8'),
            "algorithm": "Fernet",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0"
        }

        with open(self.key_file_path, 'w') as f:
            json.dump(key_data, f, indent=2)

        # Set restrictive file permissions (owner read/write only)
        if os.name != 'nt':  # Unix-like systems
            self.key_file_path.chmod(0o600)

        self._key = key
        return key

    def load_key(self) -> bytes:
        """Load encryption key from file."""
        if self._key is not None:
            return self._key

        if not self.key_file_path.exists():
            raise FileNotFoundError(f"Key file not found: {self.key_file_path}")

        with open(self.key_file_path, 'r') as f:
            key_data = json.load(f)

        if key_data.get("algorithm") != "Fernet":
            raise ValueError("Unsupported key algorithm")

        self._key = base64.b64decode(key_data["key"])
        return self._key

    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Derive encryption key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key, salt

    def rotate_key(self, new_key: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Rotate encryption key, returning (old_key, new_key)."""
        old_key = self.load_key() if self.key_file_path.exists() else None

        if new_key is None:
            new_key = Fernet.generate_key()

        # Backup old key file
        if self.key_file_path.exists():
            backup_path = self.key_file_path.with_suffix('.key.backup')
            self.key_file_path.rename(backup_path)

        # Save new key
        self._key = None  # Clear cached key
        self._key = new_key

        key_data = {
            "key": base64.b64encode(new_key).decode('utf-8'),
            "algorithm": "Fernet",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "rotated_from": backup_path.name if self.key_file_path.exists() else None
        }

        with open(self.key_file_path, 'w') as f:
            json.dump(key_data, f, indent=2)

        if os.name != 'nt':
            self.key_file_path.chmod(0o600)

        return old_key, new_key


class LocalEncryption:
    """Local encryption service for sensitive data."""

    def __init__(self, key_manager: Optional[EncryptionKeyManager] = None):
        self.key_manager = key_manager or EncryptionKeyManager()
        self._cipher: Optional[Fernet] = None

    def _get_cipher(self) -> Fernet:
        """Get or create cipher instance."""
        if self._cipher is None:
            key = self.key_manager.load_key()
            self._cipher = Fernet(key)
        return self._cipher

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data and return encrypted bytes."""
        if isinstance(data, str):
            data = data.encode('utf-8')

        cipher = self._get_cipher()
        return cipher.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data and return original bytes."""
        cipher = self._get_cipher()
        return cipher.decrypt(encrypted_data)

    def encrypt_to_string(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return base64-encoded string."""
        encrypted_data = self.encrypt(data)
        return base64.b64encode(encrypted_data).decode('utf-8')

    def decrypt_from_string(self, encrypted_string: str) -> bytes:
        """Decrypt from base64-encoded string."""
        encrypted_data = base64.b64decode(encrypted_string)
        return self.decrypt(encrypted_data)

    def encrypt_json(self, data: dict) -> str:
        """Encrypt JSON-serializable data."""
        json_str = json.dumps(data, sort_keys=True)
        return self.encrypt_to_string(json_str)

    def decrypt_json(self, encrypted_string: str) -> dict:
        """Decrypt to JSON data."""
        decrypted_bytes = self.decrypt_from_string(encrypted_string)
        json_str = decrypted_bytes.decode('utf-8')
        return json.loads(json_str)

    def is_encrypted(self, data: bytes) -> bool:
        """Check if data appears to be encrypted (basic heuristic)."""
        try:
            # Try to decrypt - if it works without error, it was encrypted
            self.decrypt(data)
            return True
        except Exception:
            return False

    def encrypt_file(self, file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
        """Encrypt a file and save to output path."""
        file_path = Path(file_path)
        if output_path is None:
            output_path = file_path.with_suffix(file_path.suffix + '.encrypted')
        else:
            output_path = Path(output_path)

        with open(file_path, 'rb') as f:
            data = f.read()

        encrypted_data = self.encrypt(data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)

        # Set restrictive permissions
        if os.name != 'nt':
            output_path.chmod(0o600)

        return output_path

    def decrypt_file(self, encrypted_file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
        """Decrypt a file and save to output path."""
        encrypted_file_path = Path(encrypted_file_path)
        if output_path is None:
            # Remove .encrypted extension if present
            if encrypted_file_path.suffix == '.encrypted':
                output_path = encrypted_file_path.with_suffix('')
            else:
                output_path = encrypted_file_path.with_suffix('.decrypted')
        else:
            output_path = Path(output_path)

        with open(encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()

        data = self.decrypt(encrypted_data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(data)

        return output_path


class FieldEncryption:
    """Encryption for specific sensitive fields in data structures."""

    def __init__(self, encryption: LocalEncryption):
        self.encryption = encryption

    def encrypt_sensitive_fields(self, data: dict, sensitive_fields: set[str]) -> dict:
        """Encrypt specified sensitive fields in a dictionary."""
        result = data.copy()

        for field_name in sensitive_fields:
            if field_name in result:
                field_value = result[field_name]
                if field_value is not None:
                    # Convert to string if not already
                    if not isinstance(field_value, str):
                        field_value = json.dumps(field_value)

                    # Encrypt and mark as encrypted
                    result[field_name] = {
                        "_encrypted": True,
                        "_algorithm": "Fernet",
                        "_data": self.encryption.encrypt_to_string(field_value)
                    }

        return result

    def decrypt_sensitive_fields(self, data: dict) -> dict:
        """Decrypt any encrypted fields in a dictionary."""
        result = data.copy()

        for field_name, field_value in result.items():
            if isinstance(field_value, dict) and field_value.get("_encrypted"):
                # Decrypt the field
                encrypted_data = field_value["_data"]
                decrypted_bytes = self.encryption.decrypt_from_string(encrypted_data)
                decrypted_str = decrypted_bytes.decode('utf-8')

                # Try to parse as JSON, fall back to string
                try:
                    result[field_name] = json.loads(decrypted_str)
                except json.JSONDecodeError:
                    result[field_name] = decrypted_str

        return result

    def identify_sensitive_fields(self, data: dict) -> set[str]:
        """Identify potentially sensitive fields based on common patterns."""
        sensitive_patterns = {
            'password', 'passwd', 'pwd', 'secret', 'key', 'token', 'auth',
            'api_key', 'access_key', 'private_key', 'credential', 'auth_token',
            'session_token', 'jwt', 'bearer', 'oauth', 'ssn', 'social_security',
            'credit_card', 'ccn', 'card_number', 'account_number', 'pin',
            'email', 'phone', 'address', 'pii', 'personal'
        }

        sensitive_fields = set()

        for field_name in data.keys():
            field_lower = field_name.lower()
            if any(pattern in field_lower for pattern in sensitive_patterns):
                sensitive_fields.add(field_name)

        return sensitive_fields


class EncryptionConfig:
    """Configuration for encryption settings."""

    def __init__(
        self,
        enabled: bool = False,
        key_file_path: str = "./encryption.key",
        auto_encrypt_sensitive: bool = True,
        custom_sensitive_fields: Optional[set[str]] = None
    ):
        self.enabled = enabled
        self.key_file_path = key_file_path
        self.auto_encrypt_sensitive = auto_encrypt_sensitive
        self.custom_sensitive_fields = custom_sensitive_fields or set()


class EncryptionManager:
    """High-level encryption manager that integrates with storage."""

    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.key_manager = EncryptionKeyManager(config.key_file_path) if config.enabled else None
        self.encryption = LocalEncryption(self.key_manager) if config.enabled else None
        self.field_encryption = FieldEncryption(self.encryption) if config.enabled else None

    def initialize_encryption(self, generate_key: bool = True) -> bool:
        """Initialize encryption system, optionally generating new key."""
        if not self.config.enabled:
            return False

        try:
            if generate_key and not Path(self.config.key_file_path).exists():
                self.key_manager.generate_key()
                return True
            else:
                # Try to load existing key
                self.key_manager.load_key()
                return True
        except Exception:
            return False

    def encrypt_data(self, data: Union[str, bytes, dict]) -> Union[str, dict]:
        """Encrypt data based on type."""
        if not self.config.enabled or not self.encryption:
            return data

        if isinstance(data, dict):
            # Handle dictionary with potential sensitive fields
            sensitive_fields = set()

            if self.config.auto_encrypt_sensitive:
                sensitive_fields.update(self.field_encryption.identify_sensitive_fields(data))

            sensitive_fields.update(self.config.custom_sensitive_fields)

            if sensitive_fields:
                return self.field_encryption.encrypt_sensitive_fields(data, sensitive_fields)
            else:
                return data
        else:
            # Encrypt string or bytes directly
            return self.encryption.encrypt_to_string(data)

    def decrypt_data(self, encrypted_data: Union[str, dict]) -> Union[str, bytes, dict]:
        """Decrypt data based on type."""
        if not self.config.enabled or not self.encryption:
            return encrypted_data

        if isinstance(encrypted_data, dict):
            # Handle dictionary with potential encrypted fields
            return self.field_encryption.decrypt_sensitive_fields(encrypted_data)
        else:
            # Decrypt string directly
            return self.encryption.decrypt_from_string(encrypted_data)

    def rotate_encryption_key(self) -> bool:
        """Rotate the encryption key."""
        if not self.config.enabled or not self.key_manager:
            return False

        try:
            old_key, new_key = self.key_manager.rotate_key()

            # Clear cached cipher to use new key
            if self.encryption:
                self.encryption._cipher = None

            return True
        except Exception:
            return False


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def configure_encryption(config: EncryptionConfig) -> EncryptionManager:
    """Configure the global encryption manager."""
    global _encryption_manager
    _encryption_manager = EncryptionManager(config)
    return _encryption_manager


def get_encryption_manager() -> Optional[EncryptionManager]:
    """Get the global encryption manager instance."""
    return _encryption_manager


def encrypt_if_enabled(data: Union[str, bytes, dict]) -> Union[str, dict]:
    """Encrypt data if encryption is enabled, otherwise return as-is."""
    if _encryption_manager:
        return _encryption_manager.encrypt_data(data)
    return data


def decrypt_if_enabled(encrypted_data: Union[str, dict]) -> Union[str, bytes, dict]:
    """Decrypt data if encryption is enabled, otherwise return as-is."""
    if _encryption_manager:
        return _encryption_manager.decrypt_data(encrypted_data)
    return encrypted_data