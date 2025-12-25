# Path: usekit/classes/data/base/parse/md.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready MD (Markdown) parser with append/overwrite/safe modes
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
from typing import Any, Union, Optional

# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """
    Safe write: write to a temp file then atomically replace target.
    Works across most POSIX-like filesystems (and is fine on Colab).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _ensure_path(file: Union[str, Path]) -> Path:
    """Convert to Path object if needed."""
    return file if isinstance(file, Path) else Path(file)


def _wrap_if_needed(data: Any, wrap: bool) -> Any:
    """
    Auto-wrap non-string values if needed.
    Markdown에서도 txt와 동일하게 문자열 변환만 책임진다.
    """
    if not wrap:
        return data
    
    # Convert to string if not already
    if not isinstance(data, str):
        if isinstance(data, (dict, list)):
            # For complex types, use repr for readability
            return repr(data)
        else:
            return str(data)
    
    return data


# ───────────────────────────────────────────────────────────────
# Load / Loads
# ───────────────────────────────────────────────────────────────

def load(
    file,
    encoding: str = "utf-8",
    strip: bool = False,
    lines: bool = False,
    **kwargs
):
    """
    Read Markdown text from a file.
    
    Args:
        file: File path or file-like object
        encoding: File encoding
        strip: If True, strip whitespace from result
        lines: If True, return list of lines (with newlines removed)
        **kwargs: Reserved for future extension (e.g. front matter 옵션)
        
    Returns:
        String content or list of lines if lines=True
    """
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding) as f:
            text = f.read()
    else:
        text = file.read()
    
    if lines:
        # Return as list of lines
        result = text.splitlines()
        if strip:
            result = [line.strip() for line in result]
        return result
    
    if strip:
        text = text.strip()
    
    return text


def loads(
    text: str,
    strip: bool = False,
    lines: bool = False,
    **kwargs
):
    """
    Parse from string (for API consistency, just returns input).
    
    Args:
        text: Markdown string
        strip: If True, strip whitespace
        lines: If True, return list of lines
        **kwargs: Reserved for future use
        
    Returns:
        Text string or list of lines
    """
    if lines:
        result = text.splitlines()
        if strip:
            result = [line.strip() for line in result]
        return result
    
    if strip:
        text = text.strip()
    
    return text


# ───────────────────────────────────────────────────────────────
# Dump / Dumps
# ───────────────────────────────────────────────────────────────

def dump(
    data: Any,
    file,
    *,
    # formatting
    encoding: str = "utf-8",
    newline: Optional[str] = None,  # None = platform default, '' = no conversion, '\n' = Unix, '\r\n' = Windows
    # behavior
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    append_newline: bool = True,  # Add newline when appending
    # extra kwargs
    **kwargs
) -> None:
    """
    Write Markdown text to file.
    
    Modes:
        overwrite=False : raise if file exists
        safe=True       : atomic write (temp file -> replace)
        append=True     : append to existing file
    
    Args:
        data: Data to write (will be converted to string)
        file: File path or file-like object
        encoding: File encoding
        newline: Newline mode (None=platform, ''=no conversion, '\n'=Unix, '\r\n'=Windows)
        wrap: Auto-convert non-strings to string
        overwrite: Allow overwriting existing file
        safe: Use atomic write
        append: Append to existing file
        append_newline: Add newline before appending
        **kwargs: Reserved for future use
    """
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)
    
    # Convert data to string
    data = _wrap_if_needed(data, wrap)
    if not isinstance(data, str):
        data = str(data)
    
    # ── Append mode
    if append:
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("a", encoding=encoding, newline=newline) as f:
                if append_newline and path_obj.stat().st_size > 0:
                    # Add newline if file is not empty
                    if not data.startswith('\n'):
                        f.write('\n')
                f.write(data)
        else:
            # file-like object
            if append_newline:
                file.write('\n')
            file.write(data)
        return
    
    # ── Normal write mode
    if path_obj:
        # overwrite guard
        if path_obj.exists() and not overwrite:
            raise FileExistsError(
                f"[md.dump] Target exists and overwrite=False: {path_obj}"
            )
        
        if safe:
            # Atomic write
            _atomic_write_text(path_obj, data, encoding=encoding)
        else:
            # Direct write
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding, newline=newline) as f:
                f.write(data)
        return
    
    # file-like object
    file.write(data)


def dumps(
    data: Any,
    *,
    wrap: bool = False,
    **kwargs
) -> str:
    """
    Serialize to Markdown string.
    
    Args:
        data: Data to convert to string
        wrap: Auto-convert non-strings
        **kwargs: Reserved for future use
        
    Returns:
        String representation
    """
    data = _wrap_if_needed(data, wrap)
    if not isinstance(data, str):
        data = str(data)
    return data


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(base="sample.md"):
    """Test MD parser functionality."""
    
    # Simple write (Markdown)
    dump("# Title\n\nHello ROP\n\n- item 1\n- item 2", base)
    print("[MD] wrote:", base)
    
    # Read
    content = load(base)
    print("[MD] read:", repr(content))
    
    # Read as lines
    lines = load(base, lines=True)
    print("[MD] lines:", lines)
    
    # Append
    dump("## Section 2\n\nMore text.", base, append=True, append_newline=True)
    print("[MD] appended:", load(base))
    
    # Write with wrap
    dump({"key": "value"}, base, wrap=True)
    print("[MD] wrap dict:", load(base))
    
    dump(12345, base, wrap=True)
    print("[MD] wrap number:", load(base))


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------