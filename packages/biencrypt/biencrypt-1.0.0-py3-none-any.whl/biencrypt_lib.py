"""
Unified Encryption Library
Supports: Adjacent Swap, XOR+Base64, and AES-256-GCM encryption
Cross-platform: Compatible with JavaScript implementation

Installation:
    pip install cryptography

Usage:
    from biencrypt_lib import adjacentEncrypt, xorEncrypt, aesEncrypt
"""

__version__ = "1.0.0"
__author__ = ""
__all__ = [
    # Adjacent Swap
    'adjacent_encrypt',
    'adjacent_decrypt',
    
    # XOR
    'xor_encrypt',
    'xor_decrypt',
    
    # AES-256-GCM
    'aes_encrypt',
    'aes_decrypt',
    'aes_encrypt_with_key',
    'aes_decrypt_with_key',
    'generate_aes_key',
]

# ============================================================================
# ADJACENT SWAP ENCRYPTION (Deterministic Character Swapping)
# ============================================================================

def adjacent_encrypt(text, seed=0):
    """
    Encrypts text by swapping adjacent character pairs with optional rotation.
    
    Args:
        text (str): Plain text to encrypt
        seed (int): Optional seed for rotation (default: 0)
        
    Returns:
        str: Encrypted text
    """
    if not text:
        return ""
    
    chars = list(text)
    
    try:
        n = int(seed)
    except Exception:
        n = 0
    
    length = len(chars)
    rot = (n % length) if length > 0 else 0
    
    # Rotate right by rot
    if rot:
        chars = chars[-rot:] + chars[:-rot]
    
    # Swap adjacent pairs
    for i in range(0, len(chars) - 1, 2):
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
    
    return ''.join(chars)


def adjacent_decrypt(text, seed=0):
    """
    Decrypts text encrypted with adjacent_encrypt.
    
    Args:
        text (str): Encrypted text
        seed (int): Optional seed used during encryption (default: 0)
        
    Returns:
        str: Decrypted text
    """
    if not text:
        return ""
    
    chars = list(text)
    
    # Swap adjacent pairs
    for i in range(0, len(chars) - 1, 2):
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
    
    try:
        n = int(seed)
    except Exception:
        n = 0
    
    length = len(chars)
    rot = (n % length) if length > 0 else 0
    
    # Rotate left by rot
    if rot:
        chars = chars[rot:] + chars[:rot]
    
    return ''.join(chars)


# ============================================================================
# XOR + BASE64 ENCRYPTION
# ============================================================================

import base64


def xor_encrypt(text, key):
    """
    Encrypts text using XOR cipher with a repeating key, then encodes to Base64.
    
    Args:
        text (str): Plain text to encrypt
        key (str): Encryption key
        
    Returns:
        str: Base64-encoded encrypted text
    """
    if not text:
        return ""
    
    if not key:
        raise ValueError("Key cannot be empty")
    
    text_bytes = text.encode('utf-8')
    key_bytes = key.encode('utf-8')
    
    xored = bytearray()
    for i, byte in enumerate(text_bytes):
        key_byte = key_bytes[i % len(key_bytes)]
        xored.append(byte ^ key_byte)
    
    return base64.b64encode(xored).decode('utf-8')


def xor_decrypt(encrypted_text, key):
    """
    Decrypts Base64-encoded XOR-encrypted text.
    
    Args:
        encrypted_text (str): Base64-encoded encrypted text
        key (str): Decryption key
        
    Returns:
        str: Decrypted plain text
    """
    if not encrypted_text:
        return ""
    
    if not key:
        raise ValueError("Key cannot be empty")
    
    try:
        encrypted_bytes = base64.b64decode(encrypted_text)
    except Exception as e:
        raise ValueError(f"Invalid Base64 input: {e}")
    
    key_bytes = key.encode('utf-8')
    
    decrypted = bytearray()
    for i, byte in enumerate(encrypted_bytes):
        key_byte = key_bytes[i % len(key_bytes)]
        decrypted.append(byte ^ key_byte)
    
    return decrypted.decode('utf-8')


# ============================================================================
# AES-256-GCM ENCRYPTION (Production-grade)
# ============================================================================

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import os
    import json
    
    AES_AVAILABLE = True
except ImportError:
    AES_AVAILABLE = False


def _check_aes_available():
    """Check if AES encryption dependencies are available."""
    if not AES_AVAILABLE:
        raise ImportError(
            "AES encryption requires 'cryptography' package. "
            "Install it with: pip install cryptography"
        )


def _derive_key(password, salt=None):
    """
    Derive a 256-bit key from a password using PBKDF2.
    
    Args:
        password (str): User-provided password
        salt (bytes): Optional salt
        
    Returns:
        tuple: (derived_key, salt)
    """
    _check_aes_available()
    
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode('utf-8'))
    return key, salt


def aes_encrypt(plaintext, password):
    """
    Encrypt plaintext using AES-256-GCM with password-based key derivation.
    
    Args:
        plaintext (str): Text to encrypt
        password (str): Password for encryption
        
    Returns:
        str: Base64-encoded JSON containing salt, nonce, and ciphertext
    """
    _check_aes_available()
    
    key, salt = _derive_key(password)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    
    result = {
        'salt': base64.b64encode(salt).decode('utf-8'),
        'nonce': base64.b64encode(nonce).decode('utf-8'),
        'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
    }
    
    return base64.b64encode(json.dumps(result).encode('utf-8')).decode('utf-8')


def aes_decrypt(encrypted_data, password):
    """
    Decrypt AES-256-GCM encrypted data.
    
    Args:
        encrypted_data (str): Base64-encoded JSON from aes_encrypt
        password (str): Password for decryption
        
    Returns:
        str: Decrypted plaintext
        
    Raises:
        Exception: If decryption fails
    """
    _check_aes_available()
    
    try:
        json_data = base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
        data = json.loads(json_data)
        
        salt = base64.b64decode(data['salt'])
        nonce = base64.b64decode(data['nonce'])
        ciphertext = base64.b64decode(data['ciphertext'])
        
        key, _ = _derive_key(password, salt)
        aesgcm = AESGCM(key)
        
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")


def aes_encrypt_with_key(plaintext, key_b64):
    """
    Encrypt using a pre-generated Base64-encoded 256-bit key.
    
    Args:
        plaintext (str): Text to encrypt
        key_b64 (str): Base64-encoded 32-byte key
        
    Returns:
        str: Base64-encoded JSON with nonce and ciphertext
    """
    _check_aes_available()
    
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (256 bits)")
    
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    
    result = {
        'nonce': base64.b64encode(nonce).decode('utf-8'),
        'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
    }
    
    return base64.b64encode(json.dumps(result).encode('utf-8')).decode('utf-8')


def aes_decrypt_with_key(encrypted_data, key_b64):
    """
    Decrypt using a pre-generated Base64-encoded 256-bit key.
    
    Args:
        encrypted_data (str): Base64-encoded JSON from aes_encrypt_with_key
        key_b64 (str): Base64-encoded 32-byte key
        
    Returns:
        str: Decrypted plaintext
    """
    _check_aes_available()
    
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (256 bits)")
    
    json_data = base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
    data = json.loads(json_data)
    
    nonce = base64.b64decode(data['nonce'])
    ciphertext = base64.b64decode(data['ciphertext'])
    
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    
    return plaintext.decode('utf-8')


def generate_aes_key():
    """
    Generate a random 256-bit key.
    
    Returns:
        str: Base64-encoded 32-byte key
    """
    _check_aes_available()
    
    key = AESGCM.generate_key(bit_length=256)
    return base64.b64encode(key).decode('utf-8')
