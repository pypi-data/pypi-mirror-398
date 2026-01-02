"""Integrity verification utilities."""
import hashlib

def sha256(content):
    """Calculate SHA256 hash of content."""
    if isinstance(content, str):
        content = content.encode()
    return hashlib.sha256(content).hexdigest()

def check(content, expected_hash):
    """Verify content matches expected SHA256 hash."""
    return sha256(content) == expected_hash.lower()

def sign(content):
    """Generate SHA256 hash for content."""
    return sha256(content)

def md5(content):
    """Calculate MD5 hash (for compatibility, prefer SHA256)."""
    if isinstance(content, str):
        content = content.encode()
    return hashlib.md5(content).hexdigest()
