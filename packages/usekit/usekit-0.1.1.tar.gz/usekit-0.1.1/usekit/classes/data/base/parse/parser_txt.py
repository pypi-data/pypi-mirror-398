# Path: usekit.classes.data.base.parse.parser_txt.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready TXT parser with comprehensive text processing capabilities
# Features:
#   - Basic I/O: load/loads/dump/dumps with atomic writes
#   - Advanced search: grep-like with regex support
#   - Tail operations: head/tail/mid viewing modes
#   - Replace: sed-like in-place text replacement
#   - Safe writes: atomic operations, append modes
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
import re
import warnings
from typing import Any, Union, Optional, List, TextIO, Tuple


# ===============================================================================
# Constants
# ===============================================================================

DEFAULT_TAIL_VALUES = {
    "tail_all": None,   # None = show all lines
    "tail_top": 10,
    "tail_mid": 10,
    "tail_bottom": 10,
}


# ===============================================================================
# Utilities
# ===============================================================================

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
    """Auto-wrap non-string values if needed."""
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


# ===============================================================================
# Tail Mode Detection & Operations
# ===============================================================================

def _detect_tail_mode(**kwargs) -> tuple[str, dict]:
    """
    Auto-detect tail mode from provided options.
    Upper wrapper already resolved aliases - we only receive full names.
    
    Returns:
        (tail_mode, filtered_opts)
    """
    
    # Collect tail_* options
    tail_opts = {
        k: v for k, v in kwargs.items()
        if k.startswith("tail_") and isinstance(v, int) and v > 0
    }
    
    # Auto-detect mode (first wins)
    tail_mode = None
    for mode in ("tail_all", "tail_top", "tail_mid", "tail_bottom"):
        if mode in tail_opts:
            tail_mode = mode
            break
    
    # Default: tail_all (show all)
    if tail_mode is None:
        tail_mode = "tail_all"
    
    return tail_mode, tail_opts


def _apply_tail_cut(
    lines: List[str],
    tail_mode: str,
    opts: dict,
    warn_large: bool = True
) -> Tuple[List[str], int, int]:
    """
    Apply tail-style line cutting.
    
    Returns:
        (cut_lines, start_index, end_index)
        - Indices are needed for replace to update correct lines
    """
    
    if not lines:
        return [], 0, 0
    
    size = len(lines)
    
    # Get values with defaults
    all_n = opts.get("tail_all", size)
    top_n = opts.get("tail_top", DEFAULT_TAIL_VALUES["tail_top"])
    mid_n = opts.get("tail_mid", DEFAULT_TAIL_VALUES["tail_mid"])
    bot_n = opts.get("tail_bottom", DEFAULT_TAIL_VALUES["tail_bottom"])
    
    # Validation
    for name, val in [("all", all_n), ("top", top_n), ("mid", mid_n), ("bot", bot_n)]:
        if val < 0:
            raise ValueError(f"tail_{name} must be non-negative, got {val}")
        if warn_large and val > size * 2:
            warnings.warn(f"tail_{name}={val} exceeds file size ({size})")
    
    # Apply mode and track indices
    if tail_mode == "tail_top":
        end = min(top_n, size)
        return lines[:end], 0, end
    
    if tail_mode == "tail_mid":
        mid = size // 2
        half_before = mid_n // 2
        half_after = mid_n - half_before
        start = max(0, mid - half_before)
        end = min(size, mid + half_after)
        return lines[start:end], start, end
    
    if tail_mode == "tail_bottom":
        start = max(0, size - bot_n)
        return lines[start:], start, size
    
    # tail_all (default)
    end = min(all_n, size) if all_n else size
    return lines[:end], 0, end


# ===============================================================================
# Search Operations
# ===============================================================================

def _search_keydata(
    lines: List[str],
    keydata: str,
    regex: bool = False,
    case_sensitive: bool = False,
    invert_match: bool = False
) -> List[str]:
    """
    Search lines for keydata pattern (grep-like functionality).
    
    Args:
        lines: List of text lines to search
        keydata: Search pattern (string or regex)
        regex: Treat keydata as regular expression
        case_sensitive: Case-sensitive matching
        invert_match: Return lines that do NOT match
    
    Returns:
        List of matching lines
    """
    
    if not keydata:
        return lines
    
    # Regex mode
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(keydata, flags)
            matches = [ln for ln in lines if pattern.search(ln)]
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{keydata}': {e}")
    else:
        # Simple substring search
        if case_sensitive:
            matches = [ln for ln in lines if keydata in ln]
        else:
            kd_lower = keydata.lower()
            matches = [ln for ln in lines if kd_lower in ln.lower()]
    
    # Invert match
    if invert_match:
        matches = [ln for ln in lines if ln not in matches]
    
    return matches


# ===============================================================================
# Replace Operations
# ===============================================================================

def _replace_in_lines(
    lines: List[str],
    keydata: str,
    data: str,
    regex: bool = False,
    case_sensitive: bool = False,
    replace_all: bool = True,
    max_count: Optional[int] = None
) -> Tuple[List[str], int]:
    """
    Replace keydata with data in lines (sed-like functionality).
    
    Args:
        lines: List of text lines
        keydata: Pattern to search for (old value)
        data: Replacement string (new value)
        regex: Use regex for keydata
        case_sensitive: Case-sensitive matching
        replace_all: Replace all occurrences (False = first only)
        max_count: Maximum number of replacements (None = unlimited)
    
    Returns:
        (modified_lines, replacement_count)
    """
    
    if not keydata:
        return lines, 0
    
    result = []
    count = 0
    max_reached = False
    
    # Regex mode
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(keydata, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{keydata}': {e}")
        
        for line in lines:
            if max_count and count >= max_count:
                result.append(line)
                continue
            
            if replace_all:
                # Replace all in line
                new_line, n = pattern.subn(data, line)
                count += n
                result.append(new_line)
            else:
                # Replace first occurrence only
                if not max_reached and pattern.search(line):
                    new_line = pattern.sub(data, line, count=1)
                    result.append(new_line)
                    count += 1
                    max_reached = True
                else:
                    result.append(line)
    
    # Simple string replacement
    else:
        search_str = keydata
        if not case_sensitive:
            # Case-insensitive requires line-by-line checking
            for line in lines:
                if max_count and count >= max_count:
                    result.append(line)
                    continue
                
                # Find case-insensitive match
                lower_line = line.lower()
                lower_key = keydata.lower()
                
                if lower_key in lower_line:
                    if replace_all:
                        # Replace all occurrences (preserve case of replacement)
                        new_line = line
                        while lower_key in new_line.lower():
                            # Find position
                            idx = new_line.lower().find(lower_key)
                            new_line = new_line[:idx] + data + new_line[idx + len(keydata):]
                            count += 1
                            if max_count and count >= max_count:
                                break
                        result.append(new_line)
                    else:
                        # Replace first occurrence only
                        if not max_reached:
                            idx = lower_line.find(lower_key)
                            new_line = line[:idx] + data + line[idx + len(keydata):]
                            result.append(new_line)
                            count += 1
                            max_reached = True
                        else:
                            result.append(line)
                else:
                    result.append(line)
        else:
            # Case-sensitive: simple str.replace
            for line in lines:
                if max_count and count >= max_count:
                    result.append(line)
                    continue
                
                if keydata in line:
                    if replace_all:
                        new_line = line.replace(keydata, data)
                        count += line.count(keydata)
                        result.append(new_line)
                    else:
                        if not max_reached:
                            new_line = line.replace(keydata, data, 1)
                            result.append(new_line)
                            count += 1
                            max_reached = True
                        else:
                            result.append(line)
                else:
                    result.append(line)
    
    return result, count


# ===============================================================================
# Load Functions
# ===============================================================================

def load(
    file,
    encoding: str = "utf-8",
    strip: bool = False,
    lines: bool = False,
    # Advanced search options
    keydata: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    invert_match: bool = False,
    # Display options
    strip_empty: bool = False,
    line_numbers: bool = False,
    # Tail options
    tail_all: Optional[int] = None,
    tail_top: Optional[int] = None,
    tail_mid: Optional[int] = None,
    tail_bottom: Optional[int] = None,
    **kwargs
):
    """
    Read text from a file with advanced processing options.
    
    Basic Usage:
        text = load("file.txt")                    # Simple read
        lines = load("file.txt", lines=True)       # Read as list
        text = load("file.txt", strip=True)        # Strip whitespace
    
    Advanced Search (grep-like):
        text = load("file.txt", keydata="ERROR")                    # Find lines with ERROR
        text = load("file.txt", keydata="^ERROR", regex=True)       # Regex search
        text = load("file.txt", keydata="error", case_sensitive=False)  # Case-insensitive
        text = load("file.txt", keydata="DEBUG", invert_match=True) # Lines without DEBUG
    
    Tail Operations (head/tail-like):
        text = load("file.txt", tail_top=10)     # First 10 lines (head)
        text = load("file.txt", tail_bottom=10)  # Last 10 lines (tail)
        text = load("file.txt", tail_mid=20)     # 20 lines around middle
        text = load("file.txt", tail_all=100)    # First 100 lines
    
    Combination:
        text = load("file.txt", 
                   keydata="ERROR", 
                   tail_bottom=100,      # Search last 100 lines
                   line_numbers=True)    # Show line numbers
    
    Args:
        file: File path or file-like object
        encoding: File encoding (default: utf-8)
        strip: Strip whitespace from result
        lines: Return list of lines instead of string
        
        keydata: Search pattern (grep-like)
        regex: Treat keydata as regular expression
        case_sensitive: Case-sensitive search (default: False)
        invert_match: Return lines that do NOT match
        
        strip_empty: Remove empty lines before processing
        line_numbers: Prefix lines with numbers
        
        tail_all: Show first N lines (default: all)
        tail_top: Show first N lines (head equivalent)
        tail_mid: Show N lines around middle
        tail_bottom: Show last N lines (tail equivalent)
        
    Returns:
        String content or list of lines if lines=True
    """
    
    # Handle file-like objects or paths
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding) as f:
            content = f.read()
    else:
        content = file.read()
    
    # If advanced features not used, use simple mode
    has_advanced = any([
        keydata, tail_all, tail_top, tail_mid, tail_bottom,
        strip_empty, line_numbers, invert_match
    ])
    
    if not has_advanced:
        # Simple mode (original behavior)
        if lines:
            result = content.splitlines()
            if strip:
                result = [line.strip() for line in result]
            return result
        
        if strip:
            content = content.strip()
        
        return content
    
    # Advanced mode
    text_lines = content.splitlines()
    
    # Strip empty lines if requested
    if strip_empty:
        text_lines = [ln for ln in text_lines if ln.strip()]
    
    # 1) Detect and apply tail mode
    tail_mode, tail_opts = _detect_tail_mode(
        tail_all=tail_all,
        tail_top=tail_top,
        tail_mid=tail_mid,
        tail_bottom=tail_bottom
    )
    
    area, _, _ = _apply_tail_cut(text_lines, tail_mode, tail_opts)
    
    # 2) Search for keydata
    if keydata:
        result = _search_keydata(
            area, keydata, regex,
            case_sensitive, invert_match
        )
    else:
        result = area
    
    # 3) Add line numbers if requested
    if line_numbers:
        result = [f"{i+1:5d} | {ln}" for i, ln in enumerate(result)]
    
    # 4) Apply strip if requested
    if strip:
        result = [ln.strip() for ln in result]
    
    # 5) Return as list or string
    if lines:
        return result
    
    return "\n".join(result)


def loads(
    text: str,
    strip: bool = False,
    lines: bool = False,
    # Advanced options (same as load)
    keydata: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    invert_match: bool = False,
    strip_empty: bool = False,
    line_numbers: bool = False,
    tail_all: Optional[int] = None,
    tail_top: Optional[int] = None,
    tail_mid: Optional[int] = None,
    tail_bottom: Optional[int] = None,
    **kwargs
):
    """
    Parse from string (same API as load).
    
    Args:
        text: Text string to process
        (All other args same as load function)
        
    Returns:
        Processed text string or list of lines
    """
    import io
    return load(
        io.StringIO(text),
        strip=strip,
        lines=lines,
        keydata=keydata,
        regex=regex,
        case_sensitive=case_sensitive,
        invert_match=invert_match,
        strip_empty=strip_empty,
        line_numbers=line_numbers,
        tail_all=tail_all,
        tail_top=tail_top,
        tail_mid=tail_mid,
        tail_bottom=tail_bottom,
        **kwargs
    )


# ===============================================================================
# Dump Functions
# ===============================================================================

def dump(
    data: Any,
    file,
    *,
    # Formatting
    encoding: str = "utf-8",
    newline: Optional[str] = None,  # None = platform default, '' = no conversion, '\n' = Unix, '\r\n' = Windows
    # Behavior
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    append_newline: bool = True,
    # Replace options (for update/replace operations)
    keydata: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    replace_all: bool = True,
    max_count: Optional[int] = None,
    # Tail options (for scoped replace)
    tail_all: Optional[int] = None,
    tail_top: Optional[int] = None,
    tail_mid: Optional[int] = None,
    tail_bottom: Optional[int] = None,
    **kwargs
) -> Optional[int]:
    """
    Write text to file with multiple operation modes.
    
    Basic Write Modes:
        dump("text", "file.txt")                           # Simple write
        dump("text", "file.txt", overwrite=False)          # Fail if exists
        dump("text", "file.txt", safe=False)               # Fast write (no atomic)
        dump("text", "file.txt", append=True)              # Append to file
        dump("text", "file.txt", append=True, append_newline=False)  # Append without newline
    
    Replace Mode (sed-like):
        count = dump("new", "file.txt", keydata="old")                    # Replace all "old" with "new"
        count = dump("new", "file.txt", keydata="old", replace_all=False) # Replace first only
        count = dump("new", "file.txt", keydata="old", max_count=5)       # Replace max 5
        count = dump("new", "file.txt", keydata="^ERROR", regex=True)     # Regex replace
    
    Scoped Replace:
        count = dump("FIXED", "file.txt", 
                    keydata="ERROR",
                    tail_bottom=100)  # Replace only in last 100 lines
    
    Data Conversion:
        dump({"key": "val"}, "file.txt", wrap=True)  # Auto-convert dict to string
        dump(12345, "file.txt", wrap=True)           # Auto-convert number to string
    
    Args:
        data: Data to write (or replacement string if keydata provided)
        file: File path or file-like object
        
        encoding: File encoding
        newline: Newline mode (None=platform, ''=no conversion, '\n'=Unix, '\r\n'=Windows)
        
        wrap: Auto-convert non-strings to string
        overwrite: Allow overwriting existing file
        safe: Use atomic write (temp file + replace)
        append: Append to existing file
        append_newline: Add newline before appending
        
        keydata: Pattern to search and replace (enables replace mode)
        regex: Use regex for keydata
        case_sensitive: Case-sensitive matching
        replace_all: Replace all occurrences (False = first only)
        max_count: Maximum replacements (None = unlimited)
        
        tail_*: Limit replacement scope to specific area
        
    Returns:
        None (normal write/append) or int (replacement count in replace mode)
    """
    
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)
    
    # Convert data to string
    data = _wrap_if_needed(data, wrap)
    if not isinstance(data, str):
        data = str(data)
    
    # ── Replace mode (keydata provided)
    if keydata:
        # Read existing content
        if path_obj:
            if not path_obj.exists():
                raise FileNotFoundError(f"Replace mode requires existing file: {path_obj}")
            with path_obj.open("r", encoding=encoding) as f:
                content = f.read()
        else:
            file.seek(0)
            content = file.read()
        
        lines = content.splitlines()
        
        # Detect tail mode
        tail_mode, tail_opts = _detect_tail_mode(
            tail_all=tail_all,
            tail_top=tail_top,
            tail_mid=tail_mid,
            tail_bottom=tail_bottom
        )
        
        # Apply tail cut to get scope + indices
        area, start_idx, end_idx = _apply_tail_cut(lines, tail_mode, tail_opts)
        
        # Replace in scoped area
        modified_area, count = _replace_in_lines(
            area, keydata, data,
            regex, case_sensitive,
            replace_all, max_count
        )
        
        # Reconstruct full content
        result_lines = lines[:start_idx] + modified_area + lines[end_idx:]
        result_text = "\n".join(result_lines)
        
        # Write back
        if path_obj:
            if safe:
                _atomic_write_text(path_obj, result_text, encoding=encoding)
            else:
                with path_obj.open("w", encoding=encoding, newline=newline) as f:
                    f.write(result_text)
        else:
            file.seek(0)
            file.truncate()
            file.write(result_text)
        
        return count
    
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
        return None
    
    # ── Normal write mode
    if path_obj:
        # overwrite guard
        if path_obj.exists() and not overwrite:
            raise FileExistsError(
                f"[txt.dump] Target exists and overwrite=False: {path_obj}"
            )
        
        if safe:
            # Atomic write
            _atomic_write_text(path_obj, data, encoding=encoding)
        else:
            # Direct write
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding, newline=newline) as f:
                f.write(data)
        return None
    
    # file-like object
    file.write(data)
    return None


def dumps(
    data: Any,
    *,
    wrap: bool = False,
    **kwargs
) -> str:
    """
    Serialize to string (for API consistency).
    
    Args:
        data: Data to convert to string
        wrap: Auto-convert non-strings
        
    Returns:
        String representation
    """
    data = _wrap_if_needed(data, wrap)
    if not isinstance(data, str):
        data = str(data)
    return data


# ===============================================================================
# Test Helper
# ===============================================================================

def _test(base="sample.txt"):
    """Test TXT parser functionality."""
    from pathlib import Path
    
    print("\n=== Basic I/O Tests ===")
    
    # 1) Simple write
    dump("Hello ROP\nLine 2\nLine 3", base)
    print(f"[1] Wrote basic content to {base}")
    
    # 2) Read
    content = load(base)
    print(f"[2] Read: {repr(content)}")
    
    # 3) Read as lines
    lines = load(base, lines=True)
    print(f"[3] Lines: {lines}")
    
    # 4) Append
    dump("Line 4", base, append=True, append_newline=True)
    print(f"[4] Appended line 4")
    
    print("\n=== Advanced Features Tests ===")
    
    # 5) Search
    result = load(base, keydata="Line", line_numbers=True)
    print(f"[5] Search 'Line':\n{result}")
    
    # 6) Tail operations
    dump("Line 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10", base, append=True)
    top3 = load(base, tail_top=3)
    print(f"[6] First 3 lines:\n{top3}")
    
    bot3 = load(base, tail_bottom=3)
    print(f"[6] Last 3 lines:\n{bot3}")
    
    # 7) Replace
    count = dump("MODIFIED", base, keydata="Line 2", replace_all=True)
    print(f"[7] Replaced 'Line 2' -> 'MODIFIED': {count} replacements")
    print(f"    Content: {load(base)}")
    
    # 8) Regex replace
    dump("test line 1\ntest line 2\nother line", base)
    count = dump("REPLACED", base, keydata="^test", regex=True, replace_all=True)
    print(f"[8] Regex replace '^test': {count} replacements")
    print(f"    Content: {load(base)}")
    
    # 9) Scoped replace (tail_bottom)
    dump("\n".join([f"Line {i}" for i in range(1, 21)]), base)
    count = dump("FIXED", base, keydata="Line", tail_bottom=5, replace_all=True)
    print(f"[9] Scoped replace (last 5 lines): {count} replacements")
    print(f"    Last 5 lines: {load(base, tail_bottom=5)}")
    
    # 10) Complex operation
    dump("\n".join([f"ERROR: Issue {i}" for i in range(1, 11)]), base)
    result = load(base, keydata="ERROR", regex=True, tail_top=5, line_numbers=True)
    print(f"[10] Search 'ERROR' in first 5 lines:\n{result}")
    
    print("\n=== Cleanup ===")
    Path(base).unlink(missing_ok=True)
    print(f"Removed {base}")


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "load",
    "loads",
    "dump", 
    "dumps",
    "DEFAULT_TAIL_VALUES",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------