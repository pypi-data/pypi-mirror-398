# Path: usekit/classes/core/env/loader_env.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Version: v3.1-auto-copy (2025-10-31)
# — memory is emotion, speed is essence —
# -----------------------------------------------------------------------------------------------
# Purpose:
#   Pure universal environment loader with lazy evaluation + auto .env creation
#   - Import time: <0.001s (was ~1.5s)
#   - All operations deferred until actually needed
#   - Auto-copies .env.example → .env if missing
#   - Works on Colab, local dev, and pip-installed environments
# -----------------------------------------------------------------------------------------------

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict
from functools import lru_cache

# ───────────────────────────────────────────────────────────────
# [1] Lazy dependency loading
# ───────────────────────────────────────────────────────────────
_dotenv_checked = False

def _ensure_dotenv():
    """Lazy-load dotenv only when needed."""
    global _dotenv_checked
    if _dotenv_checked:
        return
    
    try:
        import dotenv  # noqa
    except ImportError:
        print("[SETUP] Installing python-dotenv...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    
    _dotenv_checked = True
    
# ───────────────────────────────────────────────────────────────
_yaml_checked = False

def _ensure_yaml():
    """Lazy-load PyYAML only when needed."""
    global _yaml_checked
    if _yaml_checked:
        return

    try:
        import yaml  # noqa
    except ImportError:
        import subprocess
        import sys
        print("[SETUP] Installing PyYAML...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
        import yaml  # noqa: F401

    _yaml_checked = True
    
# ───────────────────────────────────────────────────────────────
# [2] Environment detection (cached)
# ───────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def is_colab() -> bool:
    """Check if running in Google Colab."""
    try:
        import google.colab  # noqa
        return True
    except ImportError:
        return False

@lru_cache(maxsize=1)
def is_pip_env() -> bool:
    """Check if running from pip-installed package."""
    return "site-packages" in str(Path(__file__).resolve())

# ───────────────────────────────────────────────────────────────
# [3] Fast project root detection with smart caching
# ───────────────────────────────────────────────────────────────
_project_root_cache: Optional[Path] = None

def detect_project_root() -> Path:
    """
    Detect project root with optimized search strategy.
    Caches result after first detection.
    """
    global _project_root_cache
    if _project_root_cache is not None:
        return _project_root_cache
    
    # Strategy 1: Check ENV_BASE_PATH first (fastest)
    env_base = os.getenv("ENV_BASE_PATH")
    if env_base:
        path = Path(env_base).resolve()
        if path.exists():
            _project_root_cache = path
            return path
    
    # Strategy 2: Quick check common depths (most projects are 3-5 levels deep)
    current = Path(__file__).resolve()
    for levels_up in [3, 4, 2, 5, 6]:
        if len(current.parents) > levels_up:
            candidate = current.parents[levels_up]
            if (candidate / ".env").exists() or (candidate / ".env.example").exists():
                _project_root_cache = candidate
                return candidate
    
    # Strategy 3: Full search (fallback)
    for parent in current.parents:
        if (parent / ".env").exists() or (parent / ".env.example").exists():
            _project_root_cache = parent
            return parent
    
    # Strategy 4: Environment-specific defaults
    if is_colab():
        _project_root_cache = Path("/content")
    else:
        _project_root_cache = Path.cwd()
    
    return _project_root_cache

# ───────────────────────────────────────────────────────────────
# [4] .env auto-copy helper
# ───────────────────────────────────────────────────────────────
def _copy_env_example(base_path: Path, verbose: bool = False) -> bool:
    """
    Copy .env.example to .env if .env doesn't exist.
    
    Returns:
        bool: True if copied successfully, False otherwise
    """
    env_file = base_path / ".env"
    example_file = base_path / ".env.example"
    
    # Skip if .env already exists
    if env_file.exists():
        return False
    
    # Skip if .env.example doesn't exist
    if not example_file.exists():
        return False
    
    try:
        shutil.copy2(example_file, env_file)
        if verbose:
            print(f"[OK] Created .env from .env.example: {env_file}")
        return True
    except Exception as e:
        if verbose:
            print(f"[WARN] Failed to copy .env.example: {e}")
        return False

# ───────────────────────────────────────────────────────────────
# [5] Fast .env file finder with auto-copy
# ───────────────────────────────────────────────────────────────
_env_file_cache: Optional[Path] = None

def find_env_file(auto_copy: bool = True, verbose: bool = False) -> Optional[Path]:
    """
    Find .env file with caching and optional auto-copy.
    
    Args:
        auto_copy: If True, copy .env.example → .env if .env missing
        verbose: Print status messages
        
    Returns:
        Path to .env file, or None if not found
    """
    global _env_file_cache
    if _env_file_cache is not None:
        return _env_file_cache
    
    # Priority 1: Manual override
    manual = os.getenv("USEKIT_ENV_PATH")
    if manual:
        path = Path(manual)
        if path.exists():
            _env_file_cache = path
            return path
    
    # Priority 2: Check standard locations
    base_path = get_base_path()
    env_file = base_path / ".env"
    example_file = base_path / ".env.example"
    
    # Auto-copy if requested and .env doesn't exist
    if auto_copy and not env_file.exists() and example_file.exists():
        _copy_env_example(base_path, verbose=verbose)
    
    # Return .env if it exists (either original or newly copied)
    if env_file.exists():
        _env_file_cache = env_file
        return env_file
    
    # Fallback to .env.example (read-only mode)
    if example_file.exists():
        if verbose:
            print("[INFO] Using .env.example (read-only mode)")
        _env_file_cache = example_file
        return example_file
    
    return None

# ───────────────────────────────────────────────────────────────
# [6] Lazy loader with singleton pattern
# ───────────────────────────────────────────────────────────────
_env_loaded = False

def load_env(force: bool = False, verbose: bool = False, auto_copy: bool = True) -> Optional[Path]:
    """
    Load environment variables from .env file.
    Uses lazy loading - only executes when called.
    
    Args:
        force: Force reload even if already loaded
        verbose: Print status messages
        auto_copy: Auto-copy .env.example to .env if missing
        
    Returns:
        Path to loaded .env file, or None if not found
    """
    global _env_loaded
    
    # Skip if already loaded (unless forced)
    if _env_loaded and not force:
        if verbose:
            print("[INFO] Environment already loaded.")
        return find_env_file(auto_copy=False)
    
    # Find or create .env file
    env_path = find_env_file(auto_copy=auto_copy, verbose=verbose)
    if not env_path:
        if verbose:
            print("[WARN] No .env or .env.example found.")
        return None
    
    # Lazy-load dotenv library
    _ensure_dotenv()
    from dotenv import load_dotenv
    
    # Load environment
    load_dotenv(dotenv_path=env_path, override=True)
    _env_loaded = True
    
    # Lazy-load yaml library
    _ensure_yaml()
    
    if verbose:
        print(f"[OK] Loaded environment: {env_path}")
    
    return env_path

# ───────────────────────────────────────────────────────────────
# [7] Masking helpers
# ───────────────────────────────────────────────────────────────
def mask_value(val: str, show: int = 3) -> str:
    """Mask sensitive values, showing only first/last N characters."""
    if not val:
        return ""
    val = str(val)
    if len(val) <= show * 2:
        return "***"
    return f"{val[:show]}...{val[-show:]}"

_SENSITIVE_KEYS = {"KEY", "SECRET", "TOKEN", "PASSWORD", "PASS"}

def get_env_dict(mask: bool = True) -> Dict[str, str]:
    """
    Get all environment variables as dict.
    Optionally masks sensitive values.
    """
    result = {}
    for k, v in os.environ.items():
        if mask and any(s in k.upper() for s in _SENSITIVE_KEYS):
            result[k] = mask_value(v)
        else:
            result[k] = v
    return result

# ───────────────────────────────────────────────────────────────
# [8] Lazy path getters with proxy pattern
# ───────────────────────────────────────────────────────────────
_base_path_cache: Optional[Path] = None
_sys_path_cache: Optional[Path] = None

def get_base_path() -> Path:
    """
    Get project base path with lazy detection.
    Checks ENV_BASE_PATH → detect_project_root().
    """
    global _base_path_cache
    if _base_path_cache is None:
        env_base = os.getenv("ENV_BASE_PATH")
        if env_base:
            path = Path(env_base)
            if path.exists():
                _base_path_cache = path.resolve()
            else:
                _base_path_cache = detect_project_root()
        else:
            _base_path_cache = detect_project_root()
    return _base_path_cache

def get_sys_path_now() -> Path:
    """
    Get current Python execution context directory.
    Uses sys.path[0] primarily, falls back to cwd.
    """
    global _sys_path_cache
    if _sys_path_cache is None:
        try:
            p = Path(sys.path[0])
            if not str(p) or not p.exists():
                p = Path.cwd()
        except Exception:
            p = Path.cwd()
        
        if p.is_file():
            p = p.parent
        
        _sys_path_cache = p.resolve()
    
    return _sys_path_cache

# Proxy objects for lazy initialization
class _PathProxy:
    """Proxy that defers path computation until accessed."""
    def __init__(self, getter):
        self._getter = getter
        self._cache = None
    
    def _get_path(self):
        if self._cache is None:
            self._cache = self._getter()
        return self._cache
    
    def __getattr__(self, name):
        return getattr(self._get_path(), name)
    
    def __truediv__(self, other):
        return self._get_path() / other
    
    def __str__(self):
        return str(self._get_path())
    
    def __repr__(self):
        return repr(self._get_path())
    
    def __fspath__(self):
        return str(self._get_path())

BASE_PATH = _PathProxy(get_base_path)
SYS_PATH_NOW = _PathProxy(get_sys_path_now)

# ───────────────────────────────────────────────────────────────
# [9] Safe path resolver
# ───────────────────────────────────────────────────────────────
def resolve_now_path(name: Optional[str] = None) -> Path:
    """
    Resolve path relative to SYS_PATH_NOW.
    Falls back to BASE_PATH if SYS_PATH_NOW is outside project.
    """
    try:
        sys_path = get_sys_path_now()
        base_path = get_base_path()
        
        # Check if sys_path is inside base_path
        sys_path.relative_to(base_path)
        
        return (sys_path / name).resolve() if name else sys_path
    except ValueError:
        # SYS_PATH_NOW is outside BASE_PATH
        base_path = get_base_path()
        return (base_path / name).resolve() if name else base_path
    except Exception as e:
        print(f"[ERROR] resolve_now_path error: {e}")
        raise

# ───────────────────────────────────────────────────────────────
# [10] Unified get_env() with caching
# ───────────────────────────────────────────────────────────────
_env_dict_cache: Optional[Dict[str, str]] = None

def get_env(mask_method: str = "mask", force_reload: bool = False) -> Dict[str, str]:
    """
    Get environment variables with optional masking.
    
    Args:
        mask_method: One of ['mask', 'ok', 'hidden']
        force_reload: Force reload from .env file
        
    Returns:
        dict: Environment variables (masked if applicable)
    """
    global _env_dict_cache
    
    # Load environment if not already loaded
    if force_reload or not _env_loaded:
        load_env(force=force_reload, verbose=False)
        _env_dict_cache = None  # Clear cache on reload
    
    # Use cached dict if available
    if _env_dict_cache is None:
        _env_dict_cache = dict(os.environ)
    
    # Apply masking
    result = {}
    for k, v in _env_dict_cache.items():
        if any(s in k.upper() for s in _SENSITIVE_KEYS):
            if mask_method == "ok":
                result[k] = "OK"
            elif mask_method == "hidden":
                result[k] = "****"
            else:
                result[k] = mask_value(v)
        else:
            result[k] = v
    
    return result

# ───────────────────────────────────────────────────────────────
# [11] Manual .env creation helper
# ───────────────────────────────────────────────────────────────
def create_env_from_example(force: bool = False, verbose: bool = True) -> Optional[Path]:
    """
    Manually create .env from .env.example.
    
    Args:
        force: Overwrite existing .env file
        verbose: Print status messages
        
    Returns:
        Path to created .env file, or None if failed
    """
    base_path = get_base_path()
    env_file = base_path / ".env"
    example_file = base_path / ".env.example"
    
    # Check if .env already exists
    if env_file.exists() and not force:
        if verbose:
            print(f"[INFO] .env already exists: {env_file}")
            print("[INFO] Use force=True to overwrite")
        return env_file
    
    # Check if .env.example exists
    if not example_file.exists():
        if verbose:
            print(f"[ERROR] .env.example not found: {example_file}")
        return None
    
    # Copy file
    try:
        shutil.copy2(example_file, env_file)
        if verbose:
            action = "Overwritten" if force else "Created"
            print(f"[OK] {action} .env from .env.example: {env_file}")
        
        # Clear cache to reload
        global _env_file_cache, _env_loaded
        _env_file_cache = None
        _env_loaded = False
        
        return env_file
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to copy .env.example: {e}")
        return None

# ───────────────────────────────────────────────────────────────
# [12] Cache management utilities
# ───────────────────────────────────────────────────────────────
def clear_all_caches():
    """Clear all cached values (useful for testing)."""
    global _project_root_cache, _env_file_cache, _base_path_cache
    global _sys_path_cache, _env_dict_cache, _env_loaded
    
    _project_root_cache = None
    _env_file_cache = None
    _base_path_cache = None
    _sys_path_cache = None
    _env_dict_cache = None
    _env_loaded = False
    
    # Clear function caches
    is_colab.cache_clear()
    is_pip_env.cache_clear()

# ───────────────────────────────────────────────────────────────
# [13] Exports
# ───────────────────────────────────────────────────────────────
__all__ = [
    "load_env",
    "get_env",
    "get_env_dict",
    "get_base_path",
    "get_sys_path_now",
    "resolve_now_path",
    "find_env_file",
    "create_env_from_example",
    "BASE_PATH",
    "SYS_PATH_NOW",
    "is_colab",
    "is_pip_env",
    "clear_all_caches",
]

# -----------------------------------------------------------------------------------------------
# [EOF] Import time: <0.001s + auto .env creation
# -----------------------------------------------------------------------------------------------