"""Local caching with TTL support."""
import os
import json
import time
import hashlib
from pathlib import Path

DEFAULT_CACHE_DIR = Path.home() / '.py_sandbox_cache'
DEFAULT_TTL = 3600

_cache_dir = DEFAULT_CACHE_DIR
_default_ttl = DEFAULT_TTL

def configure(cache_dir=None, default_ttl=None):
    """Configure cache directory and default TTL."""
    global _cache_dir, _default_ttl
    if cache_dir:
        _cache_dir = Path(cache_dir)
    if default_ttl:
        _default_ttl = default_ttl
    _cache_dir.mkdir(parents=True, exist_ok=True)

def _key_hash(key):
    return hashlib.sha256(key.encode()).hexdigest()[:16]

def get(key, default=None):
    """Get cached value if exists and not expired."""
    _cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_dir / f"{_key_hash(key)}.json"
    
    if not cache_file.exists():
        return default
    
    try:
        with open(cache_file) as f:
            data = json.load(f)
        if data.get('expires', 0) < time.time():
            cache_file.unlink()
            return default
        return data.get('value', default)
    except:
        return default

def set(key, value, ttl=None):
    """Store value in cache with TTL (seconds)."""
    _cache_dir.mkdir(parents=True, exist_ok=True)
    ttl = ttl or _default_ttl
    cache_file = _cache_dir / f"{_key_hash(key)}.json"
    
    data = {
        'key': key,
        'value': value,
        'created': time.time(),
        'expires': time.time() + ttl
    }
    
    with open(cache_file, 'w') as f:
        json.dump(data, f)

def delete(key):
    """Remove key from cache."""
    cache_file = _cache_dir / f"{_key_hash(key)}.json"
    if cache_file.exists():
        cache_file.unlink()

def clear():
    """Clear all cached items."""
    if _cache_dir.exists():
        for f in _cache_dir.glob('*.json'):
            f.unlink()

def stats():
    """Return cache statistics."""
    if not _cache_dir.exists():
        return {'count': 0, 'size_bytes': 0}
    files = list(_cache_dir.glob('*.json'))
    return {
        'count': len(files),
        'size_bytes': sum(f.stat().st_size for f in files)
    }
