"""
Cryptographic utilities for agent identity verification.

This module provides functions for generating and managing agent key pairs,
and for signing agent_id to prevent spoofing.
"""

from __future__ import annotations

import base64
import hashlib
import os
import time
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend


def generate_key_pair() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Generate a new RSA key pair for agent identity verification.
    
    Returns:
        Tuple of (private_key, public_key)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


def save_private_key(private_key: rsa.RSAPrivateKey, key_path: Path) -> None:
    """
    Save a private key to disk with secure permissions.
    
    Args:
        private_key: The private key to save
        key_path: Path where to save the key
    """
    key_path.parent.mkdir(parents=True, exist_ok=True)
    
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    key_path.write_bytes(pem)
    
    # Set restrictive permissions (owner read/write only)
    try:
        os.chmod(key_path, 0o600)
    except PermissionError:  # pragma: no cover - Windows
        pass


def load_private_key(key_path: Path) -> Optional[rsa.RSAPrivateKey]:
    """
    Load a private key from disk.
    
    Args:
        key_path: Path to the key file
        
    Returns:
        The private key if found, None otherwise
    """
    if not key_path.exists():
        return None
    
    try:
        pem_data = key_path.read_bytes()
        private_key = serialization.load_pem_private_key(
            pem_data,
            password=None,
            backend=default_backend()
        )
        if isinstance(private_key, rsa.RSAPrivateKey):
            return private_key
        return None
    except Exception:
        return None


def get_public_key_pem(public_key: rsa.RSAPublicKey) -> str:
    """
    Serialize a public key to PEM format string.
    
    Args:
        public_key: The public key to serialize
        
    Returns:
        PEM-encoded public key as string
    """
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')


def get_public_key_fingerprint(public_key: rsa.RSAPublicKey) -> str:
    """
    Get a fingerprint (SHA-256 hash) of a public key for identification.
    
    Args:
        public_key: The public key
        
    Returns:
        Base64-encoded SHA-256 fingerprint
    """
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    fingerprint = hashlib.sha256(pem).digest()
    return base64.b64encode(fingerprint).decode('utf-8')


def sign_agent_id(
    private_key: rsa.RSAPrivateKey,
    agent_id: str,
    api_key: str,
    timestamp: Optional[float] = None
) -> str:
    """
    Sign an agent_id and api_key with a timestamp to prevent replay attacks.
    
    Args:
        private_key: The agent's private key
        agent_id: The agent ID to sign
        api_key: The API key to sign
        timestamp: Unix timestamp (defaults to current time)
        
    Returns:
        Base64-encoded signature
    """
    if timestamp is None:
        timestamp = time.time()
    
    # Create message: agent_id + api_key + timestamp
    message = f"{agent_id}:{api_key}:{timestamp:.3f}".encode('utf-8')
    
    # Sign the message
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Return base64-encoded signature
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(
    public_key: rsa.RSAPublicKey,
    agent_id: str,
    api_key: str,
    timestamp: float,
    signature: str,
    max_age_seconds: float = 300.0
) -> bool:
    """
    Verify a signature for an agent_id, api_key and timestamp.
    
    Args:
        public_key: The agent's public key
        agent_id: The agent ID that was signed
        api_key: The API key that was signed
        timestamp: The timestamp that was signed
        signature: Base64-encoded signature
        max_age_seconds: Maximum age of signature in seconds (default: 5 minutes)
        
    Returns:
        True if signature is valid and not expired, False otherwise
    """
    # Check timestamp freshness
    current_time = time.time()
    age = current_time - timestamp
    if age < 0 or age > max_age_seconds:
        return False
    
    try:
        # Decode signature
        signature_bytes = base64.b64decode(signature)
        
        # Recreate message: agent_id + api_key + timestamp
        message = f"{agent_id}:{api_key}:{timestamp:.3f}".encode('utf-8')
        
        # Verify signature
        public_key.verify(
            signature_bytes,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


def load_public_key_from_pem(pem_data: str) -> Optional[rsa.RSAPublicKey]:
    """
    Load a public key from PEM format string.
    
    Args:
        pem_data: PEM-encoded public key string
        
    Returns:
        The public key if valid, None otherwise
    """
    try:
        public_key = serialization.load_pem_public_key(
            pem_data.encode('utf-8'),
            backend=default_backend()
        )
        if isinstance(public_key, rsa.RSAPublicKey):
            return public_key
        return None
    except Exception:
        return None

