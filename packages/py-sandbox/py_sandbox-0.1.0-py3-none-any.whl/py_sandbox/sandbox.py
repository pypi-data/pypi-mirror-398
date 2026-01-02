"""Sandbox execution for untrusted code."""
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

BLOCKED_IMPORTS = {'os', 'subprocess', 'shutil', 'socket', 'requests', 'urllib', 'pathlib'}

class SandboxError(Exception):
    """Raised when sandbox detects unsafe operation."""
    pass

def run(code, timeout=5, allowed_imports=None, expose=None):
    """
    Execute code in isolated environment.
    
    Args:
        code: Python code string to execute
        timeout: Max execution time in seconds (planned)
        allowed_imports: Set of module names to allow (default: none)
        expose: Dict of variables to expose to sandbox
    
    Returns:
        dict with keys:
            - stdout: Captured standard output
            - stderr: Captured standard error  
            - result: Value of 'result' variable if set
            - success: True if execution completed without error
    
    Example:
        >>> result = run("print(2+2)")
        >>> result['stdout']
        '4'
        >>> result['success']
        True
    """
    allowed = allowed_imports or set()
    
    safe_builtins = {
        'print': print, 'len': len, 'range': range, 'str': str,
        'int': int, 'float': float, 'bool': bool, 'list': list,
        'dict': dict, 'set': set, 'tuple': tuple, 'sorted': sorted,
        'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round,
        'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
        'isinstance': isinstance, 'type': type, 'hasattr': hasattr,
        'getattr': getattr, 'setattr': setattr, 'callable': callable,
        'repr': repr, 'hash': hash, 'id': id, 'input': lambda *a: '',
        'True': True, 'False': False, 'None': None,
        'Exception': Exception, 'ValueError': ValueError,
        'TypeError': TypeError, 'KeyError': KeyError,
    }
    
    original_import = __builtins__.__dict__['__import__'] if isinstance(__builtins__, dict) == False else __builtins__['__import__']
    
    def restricted_import(name, *args, **kwargs):
        if name.split('.')[0] in BLOCKED_IMPORTS and name not in allowed:
            raise SandboxError(f"Import '{name}' blocked for security")
        return original_import(name, *args, **kwargs)
    
    safe_builtins['__import__'] = restricted_import
    
    sandbox_globals = {'__builtins__': safe_builtins}
    if expose:
        sandbox_globals.update(expose)
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    result = None
    success = False
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, sandbox_globals)
        result = sandbox_globals.get('result', None)
        success = True
    except SandboxError as e:
        stderr_capture.write(str(e))
    except Exception as e:
        stderr_capture.write(f"{type(e).__name__}: {e}")
    
    return {
        'stdout': stdout_capture.getvalue(),
        'stderr': stderr_capture.getvalue(),
        'result': result,
        'success': success
    }

def check(code):
    """
    Static analysis to detect potentially unsafe patterns.
    
    Args:
        code: Python code string
    
    Returns:
        dict with keys:
            - safe: True if no obvious dangers detected
            - warnings: List of potential issues found
    """
    warnings = []
    danger_patterns = [
        ('import os', 'OS access attempt'),
        ('import subprocess', 'Subprocess access attempt'),
        ('import socket', 'Network access attempt'),
        ('eval(', 'Dynamic eval detected'),
        ('exec(', 'Dynamic exec detected'),
        ('__import__', 'Dynamic import detected'),
        ('open(', 'File access attempt'),
        ('compile(', 'Code compilation detected'),
    ]
    
    for pattern, warning in danger_patterns:
        if pattern in code:
            warnings.append(warning)
    
    return {
        'safe': len(warnings) == 0,
        'warnings': warnings
    }
