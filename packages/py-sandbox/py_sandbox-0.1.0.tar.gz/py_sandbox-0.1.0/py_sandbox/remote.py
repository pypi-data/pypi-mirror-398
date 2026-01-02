"""Remote module loading with authentication."""
import os
import sys
import tempfile
import importlib.util

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from . import cache as _cache
from . import verify as _verify

_config = {
    'endpoint': os.getenv('PY_SANDBOX_ENDPOINT', ''),
    'api_key': os.getenv('PY_SANDBOX_KEY', ''),
    'timeout': 30,
    'use_cache': True,
    'cache_ttl': 3600,
}

def configure(endpoint=None, api_key=None, timeout=None, use_cache=None, cache_ttl=None):
    """Configure remote loading settings."""
    if endpoint is not None: _config['endpoint'] = endpoint
    if api_key is not None: _config['api_key'] = api_key
    if timeout is not None: _config['timeout'] = timeout
    if use_cache is not None: _config['use_cache'] = use_cache
    if cache_ttl is not None: _config['cache_ttl'] = cache_ttl

def load(module_name, expected_hash=None, **kwargs):
    """
    Load and execute a remote module.
    
    Args:
        module_name: Name of module to load
        expected_hash: Optional SHA256 for integrity check
        **kwargs: Arguments passed to module's main()
    
    Returns:
        Module's main() return value or module object
    """
    if not HAS_REQUESTS:
        raise ImportError('requests required: pip install requests')
    
    if not _config['endpoint']:
        raise ValueError('No endpoint. Use configure() or set PY_SANDBOX_ENDPOINT')
    
    cache_key = f"{_config['endpoint']}:{module_name}"
    
    if _config['use_cache']:
        cached = _cache.get(cache_key)
        if cached:
            return _execute(cached, module_name, expected_hash, **kwargs)
    
    headers = {}
    if _config['api_key']:
        headers['Authorization'] = f"Bearer {_config['api_key']}"
    
    url = f"{_config['endpoint']}/{module_name}.py"
    resp = requests.get(url, headers=headers, timeout=_config['timeout'])
    resp.raise_for_status()
    code = resp.text
    
    if _config['use_cache']:
        _cache.set(cache_key, code, _config['cache_ttl'])
    
    return _execute(code, module_name, expected_hash, **kwargs)

def _execute(code, module_name, expected_hash=None, **kwargs):
    if expected_hash and not _verify.check(code, expected_hash):
        raise ValueError(f'Hash mismatch for {module_name}')
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, temp_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, 'main'):
            return module.main(**kwargs)
        return module
    finally:
        os.unlink(temp_path)

def fallback(module_name, endpoints, **kwargs):
    """Try multiple endpoints, use first that responds."""
    errors = []
    for endpoint, api_key in endpoints:
        try:
            configure(endpoint=endpoint, api_key=api_key)
            return load(module_name, **kwargs)
        except Exception as e:
            errors.append((endpoint, str(e)))
    raise ConnectionError(f'All endpoints failed: {errors}')
