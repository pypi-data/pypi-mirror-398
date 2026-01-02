"""
py-sandbox: Execute untrusted Python code safely.

Main features:
- run(): Execute code in isolated sandbox
- check(): Static analysis for unsafe patterns
- cache: Local caching with TTL
- verify: SHA256 integrity verification
- remote: Load modules from authenticated endpoints
"""
__version__ = '0.1.0'

from .sandbox import run, check, SandboxError
from . import cache
from . import verify
from . import remote

__all__ = ['run', 'check', 'SandboxError', 'cache', 'verify', 'remote']
