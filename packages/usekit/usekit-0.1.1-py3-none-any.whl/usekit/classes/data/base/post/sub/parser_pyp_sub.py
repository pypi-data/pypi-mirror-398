# Path: usekit.classes.data.base.post.sub.parser_pyp_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for PYP parser (Python source code specific utilities)
# Features:
#   - Function extraction: def/async def with decorators
#   - Class extraction: class with methods
#   - Import extraction: from/import statements
#   - Docstring handling: extract/strip/generate
#   - Code metrics: lines, complexity, parameters
#   - AST utilities: safe parsing with fallback to regex
# -----------------------------------------------------------------------------------------------

import re
import ast
from typing import Any, Dict, List, Optional, Tuple, Union


# ===============================================================================
# Constants
# ===============================================================================

PYTHON_KEYWORDS = {
    "def", "class", "import", "from", "async", "await",
    "if", "elif", "else", "for", "while", "try", "except", "finally",
    "with", "return", "yield", "lambda", "pass", "break", "continue"
}

DEFAULT_INDENT = 4


# ===============================================================================
# Function Extraction (핵심 기능)
# ===============================================================================

def _extract_functions(
    text: str,
    include_async: bool = True,
    include_decorators: bool = True,
    include_docstring: bool = True,
    include_body: bool = True
) -> List[Dict]:
    """
    Extract all function definitions from Python source.
    
    Args:
        text: Python source code
        include_async: Include async functions
        include_decorators: Include decorator lines
        include_docstring: Include docstring in body
        include_body: Include function body
        
    Returns:
        List of function info dicts:
        {
            "name": str,
            "signature": str,
            "decorators": List[str],
            "docstring": str,
            "body": str,
            "line_start": int,
            "line_end": int,
            "indent": int,
            "is_async": bool,
            "params": List[str],
            "returns": Optional[str]
        }
    """
    
    lines = text.splitlines()
    functions = []
    
    # Patterns
    def_pattern = re.compile(r'^(\s*)(async\s+)?def\s+(\w+)\s*\(')
    decorator_pattern = re.compile(r'^(\s*)@')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Collect decorators
        decorators = []
        decorator_indent = None
        while i < len(lines) and decorator_pattern.match(lines[i]):
            dec_line = lines[i]
            if decorator_indent is None:
                decorator_indent = len(dec_line) - len(dec_line.lstrip())
            decorators.append(dec_line)
            i += 1
        
        if i >= len(lines):
            break
        
        line = lines[i]
        
        # Match function definition
        def_match = def_pattern.match(line)
        if not def_match:
            i += 1
            continue
        
        indent_str = def_match.group(1)
        indent = len(indent_str)
        is_async = def_match.group(2) is not None
        func_name = def_match.group(3)
        
        # Skip async if not requested
        if is_async and not include_async:
            i += 1
            continue
        
        # Extract full signature (may span multiple lines)
        sig_lines = []
        sig_start = i
        paren_count = 0
        found_colon = False
        
        while i < len(lines):
            curr_line = lines[i]
            sig_lines.append(curr_line)
            
            # Count parentheses
            paren_count += curr_line.count('(') - curr_line.count(')')
            
            # Check for closing
            if paren_count == 0 and ':' in curr_line:
                found_colon = True
                break
            
            i += 1
        
        if not found_colon:
            i += 1
            continue
        
        signature = '\n'.join(sig_lines)
        
        # Extract parameters and return type
        params, returns = _parse_signature(signature)
        
        # Extract body
        body_lines = []
        docstring = None
        i += 1
        body_start = i
        
        # Find docstring
        if i < len(lines):
            first_body_line = lines[i].strip()
            if first_body_line.startswith('"""') or first_body_line.startswith("'''"):
                docstring_lines = []
                quote = '"""' if first_body_line.startswith('"""') else "'''"
                
                # Single line docstring
                if first_body_line.count(quote) >= 2:
                    docstring = first_body_line.strip(quote).strip()
                    i += 1
                else:
                    # Multi-line docstring
                    docstring_lines.append(first_body_line.strip(quote))
                    i += 1
                    while i < len(lines):
                        line_content = lines[i]
                        if quote in line_content:
                            docstring_lines.append(line_content[:line_content.index(quote)])
                            docstring = '\n'.join(docstring_lines).strip()
                            i += 1
                            break
                        docstring_lines.append(line_content)
                        i += 1
        
        # Extract rest of body
        while i < len(lines):
            curr_line = lines[i]
            
            # Empty line
            if not curr_line.strip():
                body_lines.append(curr_line)
                i += 1
                continue
            
            curr_indent = len(curr_line) - len(curr_line.lstrip())
            
            # Check if we've left the function (same or lower indent + keyword)
            if curr_indent <= indent:
                # Check if it's a new definition
                if def_pattern.match(curr_line) or re.match(r'^\s*class\s+\w+', curr_line):
                    break
                # Check if it's a decorator for next function
                if decorator_pattern.match(curr_line):
                    break
            
            body_lines.append(curr_line)
            i += 1
        
        # Build function info
        func_info = {
            "name": func_name,
            "signature": signature,
            "decorators": decorators if include_decorators else [],
            "docstring": docstring if include_docstring else None,
            "body": '\n'.join(body_lines) if include_body else "",
            "line_start": sig_start - len(decorators),
            "line_end": i - 1,
            "indent": indent,
            "is_async": is_async,
            "params": params,
            "returns": returns
        }
        
        functions.append(func_info)
    
    return functions


def _parse_signature(signature: str) -> Tuple[List[str], Optional[str]]:
    """
    Parse function signature to extract parameters and return type.
    
    Args:
        signature: Function signature string
        
    Returns:
        (parameter_names, return_type)
    """
    
    # Extract parameters
    params = []
    paren_start = signature.find('(')
    paren_end = signature.rfind(')')
    
    if paren_start >= 0 and paren_end > paren_start:
        params_str = signature[paren_start+1:paren_end]
        
        # Split by comma (simple parsing, doesn't handle nested defaults)
        if params_str.strip():
            for param in params_str.split(','):
                param = param.strip()
                if not param:
                    continue
                
                # Remove default value
                if '=' in param:
                    param = param[:param.index('=')].strip()
                
                # Remove type hint
                if ':' in param:
                    param = param[:param.index(':')].strip()
                
                # Skip *args, **kwargs markers
                param = param.lstrip('*')
                
                if param and param not in ('self', 'cls'):
                    params.append(param)
    
    # Extract return type
    returns = None
    arrow_idx = signature.find('->')
    if arrow_idx >= 0:
        returns = signature[arrow_idx+2:].split(':')[0].strip()
    
    return params, returns


# ===============================================================================
# Class Extraction
# ===============================================================================

def _extract_classes(
    text: str,
    include_methods: bool = True,
    include_decorators: bool = True,
    include_docstring: bool = True
) -> List[Dict]:
    """
    Extract all class definitions from Python source.
    
    Args:
        text: Python source code
        include_methods: Include method information
        include_decorators: Include class decorators
        include_docstring: Include class docstring
        
    Returns:
        List of class info dicts
    """
    
    lines = text.splitlines()
    classes = []
    
    class_pattern = re.compile(r'^(\s*)class\s+(\w+)(\(.*?\))?:')
    decorator_pattern = re.compile(r'^(\s*)@')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Collect decorators
        decorators = []
        while i < len(lines) and decorator_pattern.match(lines[i]):
            decorators.append(lines[i])
            i += 1
        
        if i >= len(lines):
            break
        
        line = lines[i]
        
        # Match class definition
        class_match = class_pattern.match(line)
        if not class_match:
            i += 1
            continue
        
        indent = len(class_match.group(1))
        class_name = class_match.group(2)
        bases = class_match.group(3) or "()"
        
        class_start = i
        signature = line
        
        # Extract docstring
        docstring = None
        i += 1
        
        if i < len(lines):
            first_line = lines[i].strip()
            if first_line.startswith('"""') or first_line.startswith("'''"):
                quote = '"""' if '"""' in first_line else "'''"
                if first_line.count(quote) >= 2:
                    docstring = first_line.strip(quote).strip()
                    i += 1
                else:
                    doc_lines = [first_line.strip(quote)]
                    i += 1
                    while i < len(lines):
                        if quote in lines[i]:
                            doc_lines.append(lines[i][:lines[i].index(quote)])
                            docstring = '\n'.join(doc_lines).strip()
                            i += 1
                            break
                        doc_lines.append(lines[i])
                        i += 1
        
        # Extract methods if requested
        methods = []
        body_start = i
        
        while i < len(lines):
            curr_line = lines[i]
            
            if not curr_line.strip():
                i += 1
                continue
            
            curr_indent = len(curr_line) - len(curr_line.lstrip())
            
            # Left the class
            if curr_indent <= indent:
                if class_pattern.match(curr_line):
                    break
            
            # Found a method
            if include_methods and re.match(r'^\s*def\s+\w+', curr_line):
                # Extract just the method signature
                method_sig = curr_line.strip()
                method_name = re.search(r'def\s+(\w+)', method_sig).group(1)
                methods.append({
                    "name": method_name,
                    "signature": method_sig,
                    "line": i
                })
            
            i += 1
        
        classes.append({
            "name": class_name,
            "signature": signature,
            "bases": bases.strip('()').split(',') if bases != "()" else [],
            "decorators": decorators if include_decorators else [],
            "docstring": docstring if include_docstring else None,
            "methods": methods,
            "line_start": class_start - len(decorators),
            "line_end": i - 1,
            "indent": indent
        })
    
    return classes


# ===============================================================================
# Import Extraction
# ===============================================================================

def _extract_imports(text: str) -> List[Dict]:
    """
    Extract all import statements from Python source.
    
    Args:
        text: Python source code
        
    Returns:
        List of import info dicts:
        {
            "type": "import" | "from",
            "module": str,
            "names": List[str],
            "alias": Dict[str, str],
            "line": int,
            "statement": str
        }
    """
    
    lines = text.splitlines()
    imports = []
    
    import_pattern = re.compile(r'^import\s+(.+)')
    from_pattern = re.compile(r'^from\s+(\S+)\s+import\s+(.+)')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # from X import Y
        from_match = from_pattern.match(line)
        if from_match:
            module = from_match.group(1)
            imports_str = from_match.group(2)
            
            # Parse imported names
            names = []
            aliases = {}
            
            for item in imports_str.split(','):
                item = item.strip()
                if ' as ' in item:
                    name, alias = item.split(' as ')
                    names.append(name.strip())
                    aliases[name.strip()] = alias.strip()
                else:
                    names.append(item)
            
            imports.append({
                "type": "from",
                "module": module,
                "names": names,
                "aliases": aliases,
                "line": i,
                "statement": line
            })
            continue
        
        # import X
        import_match = import_pattern.match(line)
        if import_match:
            imports_str = import_match.group(1)
            
            # Parse imported modules
            modules = []
            aliases = {}
            
            for item in imports_str.split(','):
                item = item.strip()
                if ' as ' in item:
                    mod, alias = item.split(' as ')
                    modules.append(mod.strip())
                    aliases[mod.strip()] = alias.strip()
                else:
                    modules.append(item)
            
            imports.append({
                "type": "import",
                "module": None,
                "names": modules,
                "aliases": aliases,
                "line": i,
                "statement": line
            })
    
    return imports


# ===============================================================================
# Docstring Utilities
# ===============================================================================

def _extract_docstring(body: str) -> Optional[str]:
    """
    Extract docstring from function/class body.
    
    Args:
        body: Function or class body
        
    Returns:
        Docstring text or None
    """
    
    lines = body.split('\n')
    if not lines:
        return None
    
    # Skip empty lines
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    
    if start >= len(lines):
        return None
    
    first_line = lines[start].strip()
    
    # Check for docstring
    if not (first_line.startswith('"""') or first_line.startswith("'''")):
        return None
    
    quote = '"""' if first_line.startswith('"""') else "'''"
    
    # Single line docstring
    if first_line.count(quote) >= 2 and len(first_line) > 6:
        return first_line.strip(quote).strip()
    
    # Multi-line docstring
    doc_lines = [first_line.strip(quote)]
    for line in lines[start+1:]:
        if quote in line:
            doc_lines.append(line[:line.index(quote)])
            break
        doc_lines.append(line)
    
    return '\n'.join(doc_lines).strip()


def _strip_docstring(body: str) -> str:
    """
    Remove docstring from function/class body.
    
    Args:
        body: Function or class body
        
    Returns:
        Body without docstring
    """
    
    lines = body.split('\n')
    if not lines:
        return body
    
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    
    if start >= len(lines):
        return body
    
    first_line = lines[start].strip()
    
    if not (first_line.startswith('"""') or first_line.startswith("'''")):
        return body
    
    quote = '"""' if first_line.startswith('"""') else "'''"
    
    # Single line docstring
    if first_line.count(quote) >= 2 and len(first_line) > 6:
        return '\n'.join(lines[start+1:])
    
    # Multi-line docstring
    end = start + 1
    while end < len(lines):
        if quote in lines[end]:
            return '\n'.join(lines[end+1:])
        end += 1
    
    return body


# ===============================================================================
# Code Metrics
# ===============================================================================

def _count_lines(text: str, count_type: str = "all") -> int:
    """
    Count lines in Python source.
    
    Args:
        text: Python source code
        count_type: "all", "code", "comment", "blank", "docstring"
        
    Returns:
        Line count
    """
    
    lines = text.splitlines()
    
    if count_type == "all":
        return len(lines)
    
    if count_type == "blank":
        return sum(1 for line in lines if not line.strip())
    
    if count_type == "comment":
        return sum(1 for line in lines if line.strip().startswith('#'))
    
    if count_type == "code":
        return len([
            line for line in lines
            if line.strip() and not line.strip().startswith('#')
        ])
    
    if count_type == "docstring":
        # Rough estimate
        in_docstring = False
        count = 0
        for line in lines:
            stripped = line.strip()
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                count += 1
            elif in_docstring:
                count += 1
        return count
    
    return 0


def _get_function_stats(func_info: Dict) -> Dict:
    """
    Calculate statistics for a function.
    
    Args:
        func_info: Function info dict from _extract_functions
        
    Returns:
        Stats dict with metrics
    """
    
    body = func_info.get("body", "")
    
    return {
        "name": func_info["name"],
        "lines_total": func_info["line_end"] - func_info["line_start"] + 1,
        "lines_code": _count_lines(body, "code"),
        "lines_blank": _count_lines(body, "blank"),
        "lines_comment": _count_lines(body, "comment"),
        "param_count": len(func_info.get("params", [])),
        "has_docstring": func_info.get("docstring") is not None,
        "is_async": func_info.get("is_async", False),
        "decorator_count": len(func_info.get("decorators", []))
    }


# ===============================================================================
# Formatting Utilities
# ===============================================================================

def _format_function(func_info: Dict, include_body: bool = True) -> str:
    """
    Format function info back to source code.
    
    Args:
        func_info: Function info dict
        include_body: Include function body
        
    Returns:
        Formatted source code
    """
    
    parts = []
    
    # Add decorators
    if func_info.get("decorators"):
        parts.extend(func_info["decorators"])
    
    # Add signature
    parts.append(func_info["signature"])
    
    # Add docstring
    if include_body and func_info.get("docstring"):
        indent = " " * (func_info.get("indent", 0) + DEFAULT_INDENT)
        parts.append(f'{indent}"""{func_info["docstring"]}"""')
    
    # Add body
    if include_body and func_info.get("body"):
        parts.append(func_info["body"])
    
    return '\n'.join(parts)


def _format_class(class_info: Dict, include_methods: bool = True) -> str:
    """
    Format class info back to source code.
    
    Args:
        class_info: Class info dict
        include_methods: Include method bodies (not implemented)
        
    Returns:
        Formatted source code
    """
    
    parts = []
    
    # Add decorators
    if class_info.get("decorators"):
        parts.extend(class_info["decorators"])
    
    # Add signature
    parts.append(class_info["signature"])
    
    # Add docstring
    if class_info.get("docstring"):
        indent = " " * (class_info.get("indent", 0) + DEFAULT_INDENT)
        parts.append(f'{indent}"""{class_info["docstring"]}"""')
    
    return '\n'.join(parts)


# ===============================================================================
# Dynamic Execution Utilities (for use.exec.pyp.base)
# ===============================================================================

def _extract_function_dependencies(func_info: Dict, all_imports: List[Dict]) -> List[str]:
    """
    Extract import names used in function body.
    
    Args:
        func_info: Function info dict from _extract_functions
        all_imports: All imports from _extract_imports
        
    Returns:
        List of imported names used in function
    """
    
    body = func_info.get("body", "")
    signature = func_info.get("signature", "")
    full_text = signature + "\n" + body
    
    used_imports = []
    
    for imp in all_imports:
        if imp["type"] == "from":
            # Check if any imported names are used
            for name in imp["names"]:
                # Simple word boundary check
                pattern = r'\b' + re.escape(name) + r'\b'
                if re.search(pattern, full_text):
                    used_imports.append(name)
        elif imp["type"] == "import":
            # Check if module name is used
            for name in imp["names"]:
                pattern = r'\b' + re.escape(name) + r'\b'
                if re.search(pattern, full_text):
                    used_imports.append(name)
    
    return used_imports


def _extract_function_with_imports(
    text: str,
    func_name: str,
    include_decorators: bool = True
) -> Optional[Dict]:
    """
    Extract a single function with its required imports.
    
    Args:
        text: Python source code
        func_name: Function name to extract
        include_decorators: Include decorators
        
    Returns:
        Dict with function info and required imports:
        {
            "function": {...},
            "imports": [...],
            "executable_code": str
        }
    """
    
    # Extract all functions and imports
    funcs = _extract_functions(text, include_decorators=include_decorators)
    imports = _extract_imports(text)
    
    # Find target function
    target = None
    for func in funcs:
        if func["name"] == func_name:
            target = func
            break
    
    if not target:
        return None
    
    # Find required imports
    required_imports = _extract_function_dependencies(target, imports)
    
    # Build required import statements
    import_stmts = []
    for imp in imports:
        if imp["type"] == "from":
            used_names = [n for n in imp["names"] if n in required_imports]
            if used_names:
                import_stmts.append(imp["statement"])
        elif imp["type"] == "import":
            used_modules = [n for n in imp["names"] if n in required_imports]
            if used_modules:
                import_stmts.append(imp["statement"])
    
    # Build executable code
    executable_parts = []
    if import_stmts:
        executable_parts.extend(import_stmts)
        executable_parts.append("")  # blank line
    executable_parts.append(_format_function(target, include_body=True))
    
    return {
        "function": target,
        "imports": import_stmts,
        "executable_code": "\n".join(executable_parts)
    }


def _parse_module_spec(spec: str) -> Dict:
    """
    Parse module specification string.
    
    Args:
        spec: Module spec like "mod.mod:fn" or "mod:fn1,fn2,fn3"
        
    Returns:
        Dict with parsed info:
        {
            "module_path": str,  # "mod.mod" or "mod"
            "functions": List[str]  # ["fn"] or ["fn1", "fn2", "fn3"]
        }
    
    Examples:
        "helpers.data:clean_text" -> {"module_path": "helpers.data", "functions": ["clean_text"]}
        "utils:fn1,fn2" -> {"module_path": "utils", "functions": ["fn1", "fn2"]}
    """
    
    if ":" not in spec:
        raise ValueError(f"Invalid spec format: {spec}. Expected 'module:function(s)'")
    
    module_path, func_spec = spec.split(":", 1)
    
    # Parse function names (comma-separated)
    if "," in func_spec:
        functions = [f.strip() for f in func_spec.split(",") if f.strip()]
    else:
        functions = [func_spec.strip()]
    
    return {
        "module_path": module_path,
        "functions": functions
    }


def _validate_function_exists(text: str, func_names: List[str]) -> Dict:
    """
    Validate that functions exist in source code.
    
    Args:
        text: Python source code
        func_names: List of function names to check
        
    Returns:
        Dict with validation results:
        {
            "valid": List[str],  # functions found
            "missing": List[str]  # functions not found
        }
    """
    
    funcs = _extract_functions(text)
    existing = {f["name"] for f in funcs}
    
    valid = [name for name in func_names if name in existing]
    missing = [name for name in func_names if name not in existing]
    
    return {
        "valid": valid,
        "missing": missing
    }


def _build_executable_block(
    text: str,
    func_names: List[str],
    include_decorators: bool = True,
    include_imports: bool = True
) -> str:
    """
    Build executable code block for multiple functions.
    
    Args:
        text: Python source code
        func_names: List of function names to extract
        include_decorators: Include decorators
        include_imports: Include required imports
        
    Returns:
        Executable Python code string
    """
    
    funcs = _extract_functions(text, include_decorators=include_decorators)
    imports = _extract_imports(text) if include_imports else []
    
    # Filter requested functions
    target_funcs = [f for f in funcs if f["name"] in func_names]
    
    if not target_funcs:
        return ""
    
    parts = []
    
    # Add imports if requested
    if include_imports and imports:
        # Collect all required imports
        all_required = set()
        for func in target_funcs:
            required = _extract_function_dependencies(func, imports)
            all_required.update(required)
        
        # Add import statements
        for imp in imports:
            if imp["type"] == "from":
                if any(n in all_required for n in imp["names"]):
                    parts.append(imp["statement"])
            elif imp["type"] == "import":
                if any(n in all_required for n in imp["names"]):
                    parts.append(imp["statement"])
        
        if parts:
            parts.append("")  # blank line after imports
    
    # Add functions
    for func in target_funcs:
        parts.append(_format_function(func, include_body=True))
        parts.append("")  # blank line between functions
    
    return "\n".join(parts).rstrip()


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "PYTHON_KEYWORDS",
    "DEFAULT_INDENT",
    "_extract_functions",
    "_parse_signature",
    "_extract_classes",
    "_extract_imports",
    "_extract_docstring",
    "_strip_docstring",
    "_count_lines",
    "_get_function_stats",
    "_format_function",
    "_format_class",
    "_extract_function_dependencies",
    "_extract_function_with_imports",
    "_parse_module_spec",
    "_validate_function_exists",
    "_build_executable_block",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
