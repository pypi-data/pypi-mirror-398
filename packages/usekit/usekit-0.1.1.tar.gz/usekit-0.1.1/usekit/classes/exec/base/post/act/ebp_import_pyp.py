# Path: usekit.classes.exec.base.post.act.ebp_import_pyp.py
# -----------------------------------------------------------------------------------------------
#  Import PYP POST Layer - Actual Import Logic
#  Created by: THE Little Prince × ROP × FOP
#
#  Single Responsibility: Import Python module or functions
#  
#  Key features:
#  - Import entire module
#  - Import specific functions (multiple)
#  - Extract executable code for each function
#  - Register in global namespace
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys
import importlib.util

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.data.base.post.parser.parser_pyp import extract_executable


# ===============================================================================
# Imported Module Wrapper
# ===============================================================================

class ImportedModule:
    """
    Wrapper class for imported functions that supports both attribute and dict access.
    
    Provides dual access patterns:
    1. Object access: m.add(10, 20) or m['add'](10, 20)
    2. Global access: add(10, 20) - auto-injected by default
    
    Examples:
        >>> m = import_pyp(path, func_list=["add", "greet"])
        
        # Object attribute access
        >>> m.add(10, 20)
        30
        
        # Object dict access
        >>> m['add'](10, 20)
        30
        
        # Direct global call (auto-injected)
        >>> add(10, 20)
        30
        
        # Dict-like behavior
        >>> len(m)               # number of functions
        2
        >>> list(m)              # list of function names
        ['add', 'greet']
        >>> for name in m:       # iteration
        ...     print(name)
        add
        greet
    """
    
    def __init__(self, functions: Dict[str, Any], inject_globals: bool = False):
        """
        Initialize with function dictionary.
        
        Args:
            functions: Dict mapping function names to function objects
            inject_globals: If True, inject functions into global namespace
        """
        self._functions = functions
        
        if inject_globals:
            self._inject_to_globals()
    
    def _inject_to_globals(self):
        """Inject all functions into the caller's global namespace."""
        import inspect
        
        # Get the caller's frame
        frame = inspect.currentframe()
        if frame is None:
            return
        
        try:
            # Walk up the frame stack to find the right target
            # In Colab/IPython: we need to reach the __main__ module's globals
            # In script: we need the topmost user code frame
            
            target_frame = None
            current = frame
            
            # Strategy: find frame with __name__ == '__main__' or topmost frame
            while current is not None:
                if current.f_globals.get('__name__') == '__main__':
                    target_frame = current
                    break
                current = current.f_back
            
            # Fallback: use the topmost frame if __main__ not found
            if target_frame is None:
                current = frame
                while current.f_back is not None:
                    current = current.f_back
                target_frame = current
            
            if target_frame is None:
                return
            
            caller_globals = target_frame.f_globals
            
            # Inject each function into caller's globals
            for name, func in self._functions.items():
                caller_globals[name] = func
        finally:
            del frame
    
    def __getattr__(self, name: str) -> Any:
        """Enable attribute access: m.add"""
        if name.startswith('_'):
            # Private attributes access the actual __dict__
            return object.__getattribute__(self, name)
        if name in self._functions:
            return self._functions[name]
        raise AttributeError(f"Function '{name}' not found. Available: {list(self._functions.keys())}")
    
    def __getitem__(self, name: str) -> Any:
        """Enable dict access: m['add']"""
        return self._functions[name]
    
    def __contains__(self, name: str) -> bool:
        """Enable 'in' operator: 'add' in m"""
        return name in self._functions
    
    def __len__(self) -> int:
        """Enable len(): len(m)"""
        return len(self._functions)
    
    def __iter__(self):
        """Enable iteration: for name in m"""
        return iter(self._functions)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ImportedModule({list(self._functions.keys())})"
    
    def keys(self):
        """Dict-like keys()"""
        return self._functions.keys()
    
    def values(self):
        """Dict-like values()"""
        return self._functions.values()
    
    def items(self):
        """Dict-like items()"""
        return self._functions.items()
    
    def get(self, name: str, default=None):
        """Dict-like get()"""
        return self._functions.get(name, default)


# ===============================================================================
# Global Import Registry
# ===============================================================================

_IMPORT_REGISTRY: Dict[str, Any] = {}
"""
Global registry for imported modules and functions.

Structure:
{
    "module_name": <module_object>,
    "module_name.func1": <function_object>,
    "module_name.func2": <function_object>,
}

This allows:
- Persistent imports across sessions
- Quick lookup for re-imports
- Function-level tracking
- Direct function calls via call() helper
"""


def get_registry() -> Dict[str, Any]:
    """Get the import registry."""
    return _IMPORT_REGISTRY


def clear_registry():
    """Clear the import registry."""
    _IMPORT_REGISTRY.clear()


def call(func_path: str, *args, **kwargs) -> Any:
    """
    Call imported function directly from registry without global injection.
    
    This provides a clean way to call imported functions without polluting
    global namespace or using object attribute access.
    
    Args:
        func_path: Function path in format "module.func" or just "func"
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function
        
    Returns:
        Function return value
        
    Raises:
        KeyError: If function not found in registry
        
    Examples:
        >>> # Import functions (no global injection needed)
        >>> import_pyp(path, func_list=["add"], auto_inject=False)
        
        >>> # Call directly via registry
        >>> call("test_args.add", 10, 40)
        50
        
        >>> # Short form (searches all modules)
        >>> call("add", 10, 40)
        50
        
        >>> # With kwargs
        >>> call("greet", name="민식", greeting="안녕")
        '안녕, 민식!'
    """
    # Try exact match first (e.g., "test_args.add")
    if func_path in _IMPORT_REGISTRY:
        return _IMPORT_REGISTRY[func_path](*args, **kwargs)
    
    # Try short name search (e.g., "add" → search for "*.add")
    for key, func in _IMPORT_REGISTRY.items():
        if key.endswith(f".{func_path}"):
            return func(*args, **kwargs)
    
    # Not found
    available = [k for k in _IMPORT_REGISTRY.keys() if '.' in k]
    raise KeyError(
        f"Function '{func_path}' not found in registry. "
        f"Available: {available}"
    )


# ===============================================================================
# Module Import
# ===============================================================================

def _import_module(path: Path, debug: bool = False) -> Any:
    """
    Import a Python module from file path.
    
    Args:
        path: Python file path
        debug: Debug mode
        
    Returns:
        Imported module object
        
    Examples:
        >>> mod = _import_module(Path("utils.pyp"))
        >>> mod.add(1, 2)
        3
    """
    
    module_name = path.stem
    
    if debug:
        print(f"[IMPORT-PYP] Loading module: {module_name}")
    
    # Create module spec
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create module spec for: {path}")
    
    # Load module
    module = importlib.util.module_from_spec(spec)
    
    # Register in sys.modules (important for relative imports)
    sys.modules[module_name] = module
    
    # Execute module
    spec.loader.exec_module(module)
    
    # Register in our registry
    _IMPORT_REGISTRY[module_name] = module
    
    if debug:
        print(f"[IMPORT-PYP] Module loaded: {module_name}")
    
    return module


# ===============================================================================
# Function Import
# ===============================================================================

def _import_functions(
    path: Path,
    func_list: List[str],
    auto_inject: bool = True,
    debug: bool = False
) -> ImportedModule:
    """
    Import specific functions from a Python module.
    
    This creates individual executable blocks for each function,
    allowing selective import without loading entire module.
    
    ALWAYS provides both:
    - Object with attribute/dict access (m.add or m['add'])
    - Global namespace injection (add directly callable)
    
    Args:
        path: Python file path
        func_list: List of function names to import
        auto_inject: If True, inject functions into global namespace (default: True)
        debug: Debug mode
        
    Returns:
        ImportedModule wrapper supporting attribute and dict access
        
    Raises:
        ValueError: If any function not found
        
    Examples:
        >>> m = _import_functions(Path("utils.pyp"), ["add", "sub"])
        >>> m.add(1, 2)      # attribute access
        3
        >>> m['sub'](5, 3)   # dict access
        2
        >>> add(1, 2)        # also works - auto-injected!
        3
    """
    
    module_name = path.stem
    
    if debug:
        print(f"[IMPORT-PYP] Extracting functions from {module_name}: {func_list}")
    
    result = {}
    
    for func_name in func_list:
        if debug:
            print(f"[IMPORT-PYP] Processing function: {func_name}")
        
        # Extract executable code for this function
        # This includes function definition + required imports
        try:
            executable_code = extract_executable(
                file=path,
                func_names=func_name,  # Single function
                include_imports=True,
                include_decorators=True
            )
        except Exception as e:
            raise ValueError(
                f"Cannot extract function '{func_name}' from {path}: {e}"
            )
        
        if debug:
            print(f"[IMPORT-PYP] Executable code length: {len(executable_code)} chars")
        
        # Create isolated namespace for execution
        namespace = {}
        
        try:
            exec(executable_code, namespace)
        except Exception as e:
            raise RuntimeError(
                f"Cannot execute function '{func_name}' from {path}: {e}"
            )
        
        # Extract the function object
        if func_name not in namespace:
            raise ValueError(
                f"Function '{func_name}' not found in execution namespace"
            )
        
        func_obj = namespace[func_name]
        result[func_name] = func_obj
        
        # Register in global registry
        registry_key = f"{module_name}.{func_name}"
        _IMPORT_REGISTRY[registry_key] = func_obj
        
        if debug:
            print(f"[IMPORT-PYP] Function imported: {func_name}")
    
    if debug:
        print(f"[IMPORT-PYP] All functions imported: {list(result.keys())}")
    
    # Wrap in ImportedModule for attribute access
    # auto_inject will trigger global namespace injection if not assigned
    return ImportedModule(result, inject_globals=auto_inject)


# ===============================================================================
# Main Import Entry Point
# ===============================================================================

@log_and_raise
def import_pyp(
    path: Path,
    func_list: List[str] | None = None,
    from_list: List[str] | None = None,  # Future: from X import Y
    as_name: str | None = None,          # Future: import X as Y
    lazy: bool = False,                  # Future: lazy loading
    auto_inject: bool = True,            # Always inject to globals by default
    debug: bool = False,
    **kwargs
) -> Any:
    """
    Import Python module or functions.
    
    Single Responsibility: Perform actual import operation
    
    SUB layer guarantees:
    - path exists and is valid
    - func_list is parsed (["f1", "f2"] or None)
    - All parameters are validated
    
    POST layer responsibility:
    - Import module OR functions
    - Register in global namespace
    - Handle errors gracefully
    
    ALWAYS provides both (when auto_inject=True, default):
    - Object with attribute/dict access
    - Global namespace injection
    
    Args:
        path: Python file path (guaranteed to exist)
        func_list: List of function names (None = import entire module)
        from_list: Reserved for future use
        as_name: Reserved for future use
        lazy: Reserved for future use
        auto_inject: If True, inject functions to globals (default: True)
        debug: Debug mode
        **kwargs: Additional options
        
    Returns:
        - If func_list is None: module object
        - If func_list provided: ImportedModule wrapper (supports m.func() and m['func']())
        
    Raises:
        ImportError: If module cannot be imported
        ValueError: If any function not found
        
    Examples:
        # Import entire module
        >>> mod = import_pyp(Path("utils.pyp"))
        >>> mod.add(1, 2)
        3
        
        # Import specific functions - BOTH ways work!
        >>> m = import_pyp(Path("utils.pyp"), func_list=["add", "sub"])
        >>> m.add(1, 2)        # object attribute access
        3
        >>> add(1, 2)          # direct global call
        3
        >>> m['sub'](5, 3)     # object dict access
        2
        >>> sub(5, 3)          # direct global call
        2
        
        # Disable auto-inject if needed
        >>> m = import_pyp(Path("utils.pyp"), func_list=["add"], auto_inject=False)
        >>> m.add(1, 2)        # works
        3
        >>> add(1, 2)          # NameError - not injected
        
        # Multiple functions
        >>> m = import_pyp(Path("utils.pyp"), func_list=["add", "sub", "mul"])
        >>> len(m)
        3
        >>> list(m)
        ['add', 'sub', 'mul']
    """
    
    if debug:
        print(f"[IMPORT-PYP] Starting import from: {path}")
        if func_list:
            print(f"[IMPORT-PYP] Target functions: {func_list}")
    
    # Future features (not implemented yet)
    if from_list is not None:
        raise NotImplementedError("from_list is not yet supported")
    if as_name is not None:
        raise NotImplementedError("as_name is not yet supported")
    if lazy:
        raise NotImplementedError("lazy import is not yet supported")
    
    # Determine import mode
    if func_list is None or len(func_list) == 0:
        # Import entire module
        if debug:
            print("[IMPORT-PYP] Mode: full module import")
        result = _import_module(path, debug=debug)
    else:
        # Import specific functions
        if debug:
            print(f"[IMPORT-PYP] Mode: selective function import ({len(func_list)} functions)")
        result = _import_functions(path, func_list, auto_inject=auto_inject, debug=debug)
    
    if debug:
        print("[IMPORT-PYP] Import completed successfully")
    
    return result


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "import_pyp",
    "ImportedModule",
    "get_registry",
    "clear_registry",
    "call",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
