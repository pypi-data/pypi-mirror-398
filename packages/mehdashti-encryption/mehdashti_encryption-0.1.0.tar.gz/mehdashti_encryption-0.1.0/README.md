# mehdashti-encryption

AES-256-GCM encryption with key rotation support for securing sensitive data.

## Features

- ✅ **AES-256-GCM**: Authenticated encryption (confidentiality + integrity)
- ✅ **Key Rotation**: Seamless key rotation without downtime
- ✅ **Automatic Key Detection**: Decrypts with correct key automatically
- ✅ **No Database Changes**: Key ID embedded in ciphertext
- ✅ **Version Support**: Future-proof encryption format
- ✅ **Type Safe**: Full type hints for Python 3.13+

## Installation

```bash
pip install mehdashti-encryption
# or
uv add mehdashti-encryption
```

## Quick Start

### Basic Usage

```python
import os
import base64
from mehdashti_encryption import EncryptionService

# Load keys from environment
keys = {
    1: base64.b64decode(os.getenv("ENCRYPTION_KEY_1")),
    2: base64.b64decode(os.getenv("ENCRYPTION_KEY_2")),
}

# Initialize service
service = EncryptionService(keys)

# Encrypt
encrypted = service.encrypt("my secret password")
print(encrypted)  # Base64 string

# Decrypt
plaintext = service.decrypt(encrypted)
print(plaintext)  # "my secret password"
```

### Generate Encryption Keys

```python
from mehdashti_encryption import EncryptionService
import base64

# Generate a new random key
key = EncryptionService.generate_key()
key_base64 = base64.b64encode(key).decode()

print(f"ENCRYPTION_KEY_1={key_base64}")
# Add to .env file
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from mehdashti_encryption import EncryptionService
import os
import base64

app = FastAPI()

def get_encryption_service() -> EncryptionService:
    keys = {
        1: base64.b64decode(os.getenv("ENCRYPTION_KEY_1")),
        2: base64.b64decode(os.getenv("ENCRYPTION_KEY_2")),
    }
    return EncryptionService(keys)

@app.post("/connections")
async def create_connection(
    password: str,
    encryption: EncryptionService = Depends(get_encryption_service)
):
    # Encrypt password before storing
    encrypted_password = encryption.encrypt(password)

    # Store in database
    await db.execute(
        "INSERT INTO connections (password_encrypted) VALUES ($1)",
        encrypted_password
    )

    return {"status": "created"}

@app.get("/connections/{id}")
async def get_connection(
    id: int,
    encryption: EncryptionService = Depends(get_encryption_service)
):
    # Fetch from database
    result = await db.fetchone(
        "SELECT password_encrypted FROM connections WHERE id = $1", id
    )

    # Decrypt password
    password = encryption.decrypt(result["password_encrypted"])

    return {"password": password}
```

## Key Rotation

### 1. Generate New Key

```python
from mehdashti_encryption import EncryptionService
import base64

new_key = EncryptionService.generate_key()
print(f"ENCRYPTION_KEY_3={base64.b64encode(new_key).decode()}")
```

### 2. Add to Environment

```bash
# .env
ENCRYPTION_KEY_1=old_key_base64
ENCRYPTION_KEY_2=old_key_base64
ENCRYPTION_KEY_3=new_key_base64  # New!
```

### 3. Rotate Keys

```python
import os
import base64
from mehdashti_encryption import EncryptionService

# Initialize with all keys
keys = {
    1: base64.b64decode(os.getenv("ENCRYPTION_KEY_1")),
    2: base64.b64decode(os.getenv("ENCRYPTION_KEY_2")),
    3: base64.b64decode(os.getenv("ENCRYPTION_KEY_3")),  # New key
}
service = EncryptionService(keys)

# Add new key and set as current
new_key = base64.b64decode(os.getenv("ENCRYPTION_KEY_3"))
service.rotate_key(new_key, new_key_id=3)

# Re-encrypt existing data
async def migrate_encryption():
    records = await db.fetch("SELECT id, password_encrypted FROM connections")

    for record in records:
        # Re-encrypt with new key
        new_encrypted = service.re_encrypt_with_new_key(record["password_encrypted"])

        # Update database
        await db.execute(
            "UPDATE connections SET password_encrypted = $1 WHERE id = $2",
            new_encrypted, record["id"]
        )

    print(f"Re-encrypted {len(records)} records")
```

### 4. Remove Old Keys (Optional)

After all data is re-encrypted, you can remove old keys:

```python
# Remove old keys from environment
# Keep only ENCRYPTION_KEY_3

keys = {
    3: base64.b64decode(os.getenv("ENCRYPTION_KEY_3")),
}
service = EncryptionService(keys)
```

## Password-Derived Keys

Instead of random keys, derive from a master password:

```python
import secrets
from mehdashti_encryption import EncryptionService

# Generate salt (store this!)
salt = secrets.token_bytes(16)

# Derive key from password
master_password = "your-strong-master-password"
key = EncryptionService.derive_key_from_password(master_password, salt)

# Use derived key
keys = {1: key}
service = EncryptionService(keys)
```

**⚠️ Important**: Store the salt securely! You need it to derive the same key later.

## Ciphertext Format

The encrypted output is base64-encoded with this structure:

```
[version:1byte][key_id:2bytes][nonce:12bytes][ciphertext][tag:16bytes]
```

- **version**: Encryption format version (currently 1)
- **key_id**: Which key was used (for rotation)
- **nonce**: Random nonce (96 bits)
- **ciphertext**: Encrypted data
- **tag**: Authentication tag (128 bits)

This allows:
- Automatic key detection during decryption
- Future format upgrades
- No database schema changes for key rotation

## API Reference

### `EncryptionService`

Main encryption service class.

#### `__init__(keys: dict[int, bytes], current_key_id: Optional[int] = None)`

Initialize with encryption keys.

- **keys**: Dictionary mapping key_id to 32-byte key
- **current_key_id**: ID of current key (defaults to max)

#### `encrypt(plaintext: str | bytes) -> str`

Encrypt plaintext.

- **plaintext**: String or bytes to encrypt
- **Returns**: Base64-encoded ciphertext

#### `decrypt(ciphertext: str) -> str`

Decrypt ciphertext (automatically detects key).

- **ciphertext**: Base64 ciphertext from encrypt()
- **Returns**: Decrypted plaintext

#### `re_encrypt_with_new_key(old_ciphertext: str) -> str`

Re-encrypt with current key.

- **old_ciphertext**: Ciphertext encrypted with old key
- **Returns**: New ciphertext with current key

#### `rotate_key(new_key: bytes, new_key_id: int) -> None`

Add new key and set as current.

- **new_key**: New 32-byte encryption key
- **new_key_id**: Unique ID for new key

#### `@staticmethod generate_key() -> bytes`

Generate random 32-byte encryption key.

#### `@staticmethod derive_key_from_password(password: str, salt: bytes) -> bytes`

Derive key from password using PBKDF2.

## Security Considerations

### ✅ Best Practices

1. **Use Random Keys**: Generate with `generate_key()`
2. **Rotate Regularly**: Update keys every 6-12 months
3. **Store Keys Securely**: Use environment variables or secret managers
4. **Never Log Keys**: Don't print or log encryption keys
5. **Use HTTPS**: Always transmit encrypted data over HTTPS

### ⚠️ Important Notes

- **AES-GCM is authenticated**: Tampering is detected automatically
- **Nonces are random**: Safe for concurrent encryption
- **Keys are 256-bit**: Quantum-resistant for foreseeable future
- **PBKDF2 iterations**: 600,000 (OWASP 2023 recommendation)

### ❌ Don't

- ❌ Don't reuse keys across environments (dev/prod)
- ❌ Don't store keys in source code
- ❌ Don't use weak passwords for key derivation
- ❌ Don't decrypt on client side (keep keys server-side)

## Use Cases

### 1. Database Connection Passwords

```python
# Encrypt before storing
encrypted_password = service.encrypt(user_password)
await db.execute(
    "INSERT INTO connections (password_encrypted) VALUES ($1)",
    encrypted_password
)

# Decrypt when needed
password = service.decrypt(row["password_encrypted"])
connection = connect_to_oracle(username, password)
```

### 2. API Keys

```python
# Store encrypted API key
encrypted_key = service.encrypt(api_key)

# Use when making requests
api_key = service.decrypt(encrypted_key)
response = requests.get(url, headers={"Authorization": f"Bearer {api_key}"})
```

### 3. Personal Data (GDPR Compliance)

```python
# Encrypt PII
encrypted_ssn = service.encrypt(user_ssn)
encrypted_email = service.encrypt(user_email)

# Store encrypted
await db.execute(
    "INSERT INTO users (ssn_encrypted, email_encrypted) VALUES ($1, $2)",
    encrypted_ssn, encrypted_email
)
```

## Requirements

- Python 3.13+
- cryptography 44.0+

## License

MIT License

## Author

Mahdi Ashti <mahdi@mehdashti.com>

## Links

- **Repository**: https://github.com/mehdashti/smart-platform
- **Issues**: https://github.com/mehdashti/smart-platform/issues
