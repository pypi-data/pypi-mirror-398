"""Remote module loading with authentication and fallback."""
import os
import sys
import tempfile
import importlib.util
import subprocess

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
    'fallback_package': os.getenv('PY_SANDBOX_FALLBACK', 'phi-linux-modules'),
}

def configure(endpoint=None, api_key=None, timeout=None, use_cache=None, 
              cache_ttl=None, fallback_package=None):
    """Configure remote loading settings."""
    if endpoint is not None: _config['endpoint'] = endpoint
    if api_key is not None: _config['api_key'] = api_key
    if timeout is not None: _config['timeout'] = timeout
    if use_cache is not None: _config['use_cache'] = use_cache
    if cache_ttl is not None: _config['cache_ttl'] = cache_ttl
    if fallback_package is not None: _config['fallback_package'] = fallback_package

def load(module_name, expected_hash=None, use_fallback=True, **kwargs):
    """
    Load and execute a remote module with automatic fallback.
    
    Args:
        module_name: Name of module to load
        expected_hash: Optional SHA256 for integrity
        use_fallback: If True, try PyPI fallback on failure
        **kwargs: Arguments passed to module's main()
    
    Flow:
        1. Try primary endpoint (n8n)
        2. On failure + use_fallback: try PyPI package
        3. Execute module.main(**kwargs)
    """
    # Try primary endpoint
    try:
        return _load_from_endpoint(module_name, expected_hash, **kwargs)
    except Exception as primary_error:
        if not use_fallback:
            raise
        
        # Try PyPI fallback
        try:
            return _load_from_pypi(module_name, **kwargs)
        except Exception as fallback_error:
            raise ConnectionError(
                f"All sources failed. Primary: {primary_error}, Fallback: {fallback_error}"
            )

def _load_from_endpoint(module_name, expected_hash=None, **kwargs):
    """Load from primary HTTP endpoint."""
    if not HAS_REQUESTS:
        raise ImportError('requests required: pip install requests')
    
    if not _config['endpoint']:
        raise ValueError('No endpoint configured')
    
    cache_key = f"{_config['endpoint']}:{module_name}"
    
    # Try cache first
    if _config['use_cache']:
        cached = _cache.get(cache_key)
        if cached:
            return _execute_code(cached, module_name, expected_hash, **kwargs)
    
    # Fetch from remote
    headers = {}
    if _config['api_key']:
        headers['Authorization'] = f"Bearer {_config['api_key']}"
    
    url = f"{_config['endpoint']}/{module_name}.py"
    resp = requests.get(url, headers=headers, timeout=_config['timeout'])
    resp.raise_for_status()
    code = resp.text
    
    # Cache it
    if _config['use_cache']:
        _cache.set(cache_key, code, _config['cache_ttl'])
    
    return _execute_code(code, module_name, expected_hash, **kwargs)

def _load_from_pypi(module_name, **kwargs):
    """
    Fallback: load from PyPI package.
    
    Expects package structure:
        phi-linux-modules/
            phi_linux_modules/
                heartbeat.py
                sync.py
                ...
    """
    pkg = _config['fallback_package']
    pkg_module = pkg.replace('-', '_')
    
    # Try to import, install if missing
    try:
        fallback_pkg = importlib.import_module(pkg_module)
    except ImportError:
        # Auto-install fallback package
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 
            '--quiet', '--break-system-packages', pkg
        ])
        fallback_pkg = importlib.import_module(pkg_module)
    
    # Import the specific module
    full_module_name = f"{pkg_module}.{module_name}"
    module = importlib.import_module(full_module_name)
    
    if hasattr(module, 'main'):
        return module.main(**kwargs)
    return module

def _execute_code(code, module_name, expected_hash=None, **kwargs):
    """Execute code string as module."""
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
            return load(module_name, use_fallback=False, **kwargs)
        except Exception as e:
            errors.append((endpoint, str(e)))
    
    # All endpoints failed, try PyPI
    try:
        return _load_from_pypi(module_name, **kwargs)
    except Exception as e:
        errors.append(('pypi_fallback', str(e)))
    
    raise ConnectionError(f'All sources failed: {errors}')

def status():
    """Check connectivity to all sources."""
    result = {'primary': None, 'fallback': None}
    
    # Check primary
    if _config['endpoint'] and HAS_REQUESTS:
        try:
            headers = {}
            if _config['api_key']:
                headers['Authorization'] = f"Bearer {_config['api_key']}"
            resp = requests.head(_config['endpoint'], headers=headers, timeout=5)
            result['primary'] = {'ok': resp.status_code < 400, 'code': resp.status_code}
        except Exception as e:
            result['primary'] = {'ok': False, 'error': str(e)}
    
    # Check fallback package availability
    pkg_module = _config['fallback_package'].replace('-', '_')
    try:
        importlib.import_module(pkg_module)
        result['fallback'] = {'ok': True, 'installed': True}
    except ImportError:
        result['fallback'] = {'ok': True, 'installed': False, 'note': 'Will auto-install on use'}
    
    return result
