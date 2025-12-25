"""
AES-256-GCM Encryption Service

Provides authenticated encryption with key rotation support.
"""

import base64
import secrets
import struct
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """
    AES-256-GCM encryption service with key rotation and context binding support.

    Features:
    - AES-256-GCM (Authenticated encryption with AAD support)
    - Key rotation (event-based, not time-based)
    - key_id embedded in ciphertext metadata
    - Context binding via Additional Authenticated Data (AAD)
    - No database storage of key_id

    Ciphertext format:
    [version:1byte][key_id:2bytes][nonce:12bytes][ciphertext][tag:16bytes]

    Security Best Practices:
    - ALWAYS use associated_data to bind encrypted data to its context
    - This prevents ciphertext from being copied to different records/users
    - Example contexts: user_id, record_id, table_name, field_name

    Example:
        ```python
        from mehdashti_encryption import EncryptionService

        # Initialize with keys (from environment variables)
        keys = {
            1: b"your-32-byte-key-here-000000000",
            2: b"new-32-byte-key-after-rotation-0"
        }
        service = EncryptionService(keys)

        # Encrypt with context binding (RECOMMENDED)
        context = f"user_id:{user.id}:field:email"
        encrypted = service.encrypt("user@example.com", associated_data=context)

        # Decrypt (automatically detects which key to use)
        plaintext = service.decrypt(encrypted, associated_data=context)

        # Without context binding (NOT RECOMMENDED for production)
        encrypted = service.encrypt("sensitive data")
        plaintext = service.decrypt(encrypted)
        ```
    """

    VERSION = 1  # Encryption version for future compatibility

    def __init__(self, keys: dict[int, bytes], current_key_id: Optional[int] = None):
        """
        Initialize encryption service with keys.

        Args:
            keys: Dictionary mapping key_id to 32-byte AES key
            current_key_id: ID of current key (defaults to highest key_id)

        Raises:
            ValueError: If keys are invalid

        Example:
            ```python
            keys = {
                1: base64.b64decode(os.getenv("ENCRYPTION_KEY_1")),
                2: base64.b64decode(os.getenv("ENCRYPTION_KEY_2")),
            }
            service = EncryptionService(keys)
            ```
        """
        if not keys:
            raise ValueError("At least one encryption key is required")

        # Validate all keys are 32 bytes
        for key_id, key in keys.items():
            if len(key) != 32:
                raise ValueError(f"Key {key_id} must be exactly 32 bytes (256 bits)")

        self.keys = keys
        self.current_key_id = current_key_id or max(keys.keys())

        if self.current_key_id not in self.keys:
            raise ValueError(f"Current key_id {self.current_key_id} not found in keys")

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a random 32-byte (256-bit) encryption key.

        Returns:
            32-byte random key suitable for AES-256

        Example:
            ```python
            import base64

            key = EncryptionService.generate_key()
            key_base64 = base64.b64encode(key).decode()
            print(f"ENCRYPTION_KEY_1={key_base64}")
            ```
        """
        return secrets.token_bytes(32)

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """
        Derive a 32-byte encryption key from password using PBKDF2.

        Args:
            password: Master password
            salt: Salt (should be at least 16 bytes)

        Returns:
            32-byte derived key

        Example:
            ```python
            salt = secrets.token_bytes(16)
            key = EncryptionService.derive_key_from_password("master-password", salt)
            ```

        Note:
            Store the salt! You need it to derive the same key later.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,  # OWASP recommendation
        )
        return kdf.derive(password.encode())

    def encrypt(
        self, plaintext: str | bytes, associated_data: Optional[str | bytes] = None
    ) -> str:
        """
        Encrypt plaintext using current key with optional context binding.

        Args:
            plaintext: String or bytes to encrypt
            associated_data: Optional context data (user_id, record_id, field_name, etc.)
                           This data is authenticated but NOT encrypted.
                           It binds the ciphertext to a specific context, preventing
                           replay attacks and ciphertext reuse across different contexts.

        Returns:
            Base64-encoded ciphertext with embedded metadata

        Security Note:
            Using associated_data is STRONGLY RECOMMENDED for production use.
            It prevents attacks where encrypted data is copied to different records/contexts.

        Example:
            ```python
            # Bind to specific user and field
            context = f"user_id:{user.id}:field:email"
            encrypted = service.encrypt("user@example.com", associated_data=context)

            # Or use structured context
            context = f"table:users:id:{user.id}:field:ssn"
            encrypted_ssn = service.encrypt(ssn, associated_data=context)
            ```

        Warning:
            If you encrypt with associated_data, you MUST provide the SAME associated_data
            when decrypting, otherwise decryption will fail. Store the context information
            alongside the ciphertext (it doesn't need to be secret).
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        # Convert associated_data to bytes if provided
        aad_bytes: Optional[bytes] = None
        if associated_data is not None:
            if isinstance(associated_data, str):
                aad_bytes = associated_data.encode("utf-8")
            else:
                aad_bytes = associated_data

        # Generate random 12-byte nonce (96 bits - recommended for GCM)
        nonce = secrets.token_bytes(12)

        # Get current key
        key = self.keys[self.current_key_id]
        aesgcm = AESGCM(key)

        # Encrypt and get ciphertext + tag (tag is appended by AESGCM)
        # AAD is authenticated but not encrypted - it binds ciphertext to context
        ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext, aad_bytes)

        # Build metadata: [version:1byte][key_id:2bytes][nonce:12bytes][ciphertext+tag]
        metadata = struct.pack("!BH", self.VERSION, self.current_key_id)
        full_ciphertext = metadata + nonce + ciphertext_and_tag

        # Encode to base64 for storage
        return base64.b64encode(full_ciphertext).decode("ascii")

    def decrypt(
        self, ciphertext: str, associated_data: Optional[str | bytes] = None
    ) -> str:
        """
        Decrypt ciphertext (automatically detects key from metadata).

        Args:
            ciphertext: Base64-encoded ciphertext from encrypt()
            associated_data: Optional context data (MUST match what was used in encrypt())
                           If the data was encrypted with associated_data, you MUST
                           provide the same value here, otherwise decryption will fail.

        Returns:
            Decrypted plaintext as string

        Raises:
            ValueError: If ciphertext is invalid, associated_data doesn't match,
                       or decryption fails

        Example:
            ```python
            # Decrypt with same context used during encryption
            context = f"user_id:{user.id}:field:email"
            plaintext = service.decrypt(encrypted, associated_data=context)
            ```

        Security Note:
            If decryption fails with "Decryption failed", it could mean:
            1. The ciphertext was tampered with
            2. The wrong associated_data was provided
            3. The wrong encryption key is being used
        """
        try:
            # Convert associated_data to bytes if provided
            aad_bytes: Optional[bytes] = None
            if associated_data is not None:
                if isinstance(associated_data, str):
                    aad_bytes = associated_data.encode("utf-8")
                else:
                    aad_bytes = associated_data

            # Decode from base64
            full_ciphertext = base64.b64decode(ciphertext)

            # Parse metadata: [version:1byte][key_id:2bytes][nonce:12bytes][ciphertext+tag]
            if len(full_ciphertext) < 15:  # 1 + 2 + 12 = 15 bytes minimum
                raise ValueError("Ciphertext too short")

            version, key_id = struct.unpack("!BH", full_ciphertext[:3])

            if version != self.VERSION:
                raise ValueError(f"Unsupported encryption version: {version}")

            if key_id not in self.keys:
                raise ValueError(f"Unknown key_id: {key_id}")

            # Extract nonce and ciphertext+tag
            nonce = full_ciphertext[3:15]
            ciphertext_and_tag = full_ciphertext[15:]

            # Decrypt with AAD verification
            # If AAD doesn't match what was used during encryption, this will fail
            key = self.keys[key_id]
            aesgcm = AESGCM(key)
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_and_tag, aad_bytes)

            return plaintext_bytes.decode("utf-8")

        except Exception as e:
            raise ValueError(f"Decryption failed: {e}") from e

    def re_encrypt_with_new_key(
        self,
        old_ciphertext: str,
        associated_data: Optional[str | bytes] = None,
    ) -> str:
        """
        Re-encrypt data with current key (for key rotation).

        Args:
            old_ciphertext: Ciphertext encrypted with old key
            associated_data: Optional context data (must match what was used originally)
                           If the original data was encrypted with associated_data,
                           you MUST provide the same value here.

        Returns:
            New ciphertext encrypted with current key

        Example:
            ```python
            # After adding a new key and updating current_key_id
            context = f"user_id:{user.id}:field:email"
            new_encrypted = service.re_encrypt_with_new_key(
                old_encrypted,
                associated_data=context
            )
            # Update database with new_encrypted
            ```
        """
        # Decrypt with old key (automatically detected)
        plaintext = self.decrypt(old_ciphertext, associated_data=associated_data)

        # Re-encrypt with current key using same associated_data
        return self.encrypt(plaintext, associated_data=associated_data)

    def rotate_key(self, new_key: bytes, new_key_id: int) -> None:
        """
        Add a new encryption key and set it as current.

        Args:
            new_key: New 32-byte encryption key
            new_key_id: ID for the new key (should be unique)

        Raises:
            ValueError: If key is invalid or key_id already exists

        Example:
            ```python
            # Generate new key
            new_key = EncryptionService.generate_key()

            # Add and activate
            service.rotate_key(new_key, new_key_id=3)

            # Re-encrypt existing data
            for record in db.query("SELECT id, encrypted_field FROM table"):
                new_encrypted = service.re_encrypt_with_new_key(record.encrypted_field)
                db.execute("UPDATE table SET encrypted_field = $1 WHERE id = $2",
                          new_encrypted, record.id)
            ```
        """
        if len(new_key) != 32:
            raise ValueError("New key must be exactly 32 bytes")

        if new_key_id in self.keys:
            raise ValueError(f"Key ID {new_key_id} already exists")

        self.keys[new_key_id] = new_key
        self.current_key_id = new_key_id
