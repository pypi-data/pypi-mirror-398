# Path: usekit.classes.data.base.post.parser.parser_csv.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready CSV parser with append/overwrite/safe modes
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
import csv
from typing import Any, Union, Optional, List, Dict

# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _atomic_write_csv(path: Path, rows: List, encoding: str = "utf-8", **csv_kwargs) -> None:
    """
    Safe write: write to a temp file then atomically replace target.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding, newline=""
    ) as tmp:
        writer = csv.writer(tmp, **csv_kwargs)
        writer.writerows(rows)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _ensure_path(file: Union[str, Path]) -> Path:
    """Convert to Path object if needed."""
    return file if isinstance(file, Path) else Path(file)


# ───────────────────────────────────────────────────────────────
# Load / Loads
# ───────────────────────────────────────────────────────────────

def load(
    file,
    encoding: str = "utf-8",
    dialect: str = "excel",
    header: bool = True,
    **kwargs
):
    """
    Read CSV from a file.
    
    Args:
        file: File path or file-like object
        encoding: File encoding
        dialect: CSV dialect ('excel', 'unix', etc.)
        header: If True, return list of dicts with first row as keys
        **kwargs: Additional csv.reader options (delimiter, quotechar, etc.)
        
    Returns:
        List of dicts if header=True, else list of lists
    """
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding, newline="") as f:
            reader = csv.reader(f, dialect=dialect, **kwargs)
            rows = list(reader)
    else:
        reader = csv.reader(file, dialect=dialect, **kwargs)
        rows = list(reader)
    
    if not rows:
        return []
    
    if header:
        headers = rows[0]
        return [dict(zip(headers, row)) for row in rows[1:]]
    
    return rows


def loads(
    text: str,
    dialect: str = "excel",
    header: bool = True,
    **kwargs
):
    """
    Parse CSV from string.
    
    Args:
        text: CSV text string
        dialect: CSV dialect
        header: If True, return list of dicts
        **kwargs: Additional csv.reader options
        
    Returns:
        List of dicts if header=True, else list of lists
    """
    lines = text.splitlines()
    reader = csv.reader(lines, dialect=dialect, **kwargs)
    rows = list(reader)
    
    if not rows:
        return []
    
    if header:
        headers = rows[0]
        return [dict(zip(headers, row)) for row in rows[1:]]
    
    return rows


# ───────────────────────────────────────────────────────────────
# Dump / Dumps
# ───────────────────────────────────────────────────────────────

def dump(
    data: Union[List[List], List[Dict]],
    file,
    *,
    # formatting
    encoding: str = "utf-8",
    dialect: str = "excel",
    # behavior
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    header: Optional[List[str]] = None,
    # extra kwargs
    **kwargs
) -> None:
    """
    Write CSV to file.
    
    Modes:
        overwrite=False : raise if file exists
        safe=True       : atomic write (temp file -> replace)
        append=True     : append to existing file
    
    Args:
        data: List of lists or list of dicts
        file: File path or file-like object
        encoding: File encoding
        dialect: CSV dialect
        overwrite: Allow overwriting existing file
        safe: Use atomic write
        append: Append to existing file
        header: Custom header row (auto-detected from dicts if None)
        **kwargs: Additional csv.writer options (delimiter, quotechar, etc.)
    """
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)
    
    # Normalize data to list of lists
    rows = []
    if data and isinstance(data[0], dict):
        # List of dicts
        if header is None:
            header = list(data[0].keys())
        if not append or (path_obj and not path_obj.exists()):
            rows.append(header)
        rows.extend([list(row.values()) for row in data])
    else:
        # List of lists
        if header is not None and (not append or (path_obj and not path_obj.exists())):
            rows.append(header)
        rows.extend(data)
    
    # ── Append mode
    if append:
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("a", encoding=encoding, newline="") as f:
                writer = csv.writer(f, dialect=dialect, **kwargs)
                writer.writerows(rows)
        else:
            writer = csv.writer(file, dialect=dialect, **kwargs)
            writer.writerows(rows)
        return
    
    # ── Normal write mode
    if path_obj:
        # overwrite guard
        if path_obj.exists() and not overwrite:
            raise FileExistsError(
                f"[csv.dump] Target exists and overwrite=False: {path_obj}"
            )
        
        if safe:
            # Atomic write
            _atomic_write_csv(path_obj, rows, encoding=encoding, dialect=dialect, **kwargs)
        else:
            # Direct write
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding, newline="") as f:
                writer = csv.writer(f, dialect=dialect, **kwargs)
                writer.writerows(rows)
        return
    
    # file-like object
    writer = csv.writer(file, dialect=dialect, **kwargs)
    writer.writerows(rows)


def dumps(
    data: Union[List[List], List[Dict]],
    *,
    dialect: str = "excel",
    header: Optional[List[str]] = None,
    **kwargs
) -> str:
    """
    Serialize to CSV string.
    
    Args:
        data: List of lists or list of dicts
        dialect: CSV dialect
        header: Custom header row
        **kwargs: Additional csv.writer options
        
    Returns:
        CSV string
    """
    import io
    output = io.StringIO()
    
    # Normalize data
    rows = []
    if data and isinstance(data[0], dict):
        if header is None:
            header = list(data[0].keys())
        rows.append(header)
        rows.extend([list(row.values()) for row in data])
    else:
        if header is not None:
            rows.append(header)
        rows.extend(data)
    
    writer = csv.writer(output, dialect=dialect, **kwargs)
    writer.writerows(rows)
    return output.getvalue()


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(base="sample.csv"):
    """Test CSV parser functionality."""
    
    # Write list of dicts
    data = [
        {"name": "Alice", "age": "30", "city": "Seoul"},
        {"name": "Bob", "age": "25", "city": "Busan"}
    ]
    dump(data, base)
    print("[CSV] wrote dicts:", base)
    
    # Read with header
    content = load(base)
    print("[CSV] read:", content)
    
    # Append
    dump([{"name": "Charlie", "age": "35", "city": "Jeju"}], base, append=True)
    print("[CSV] appended:", load(base))
    
    # Write list of lists
    rows = [["x", "y"], [1, 2], [3, 4]]
    dump(rows, "coords.csv", header=None)
    print("[CSV] wrote lists:", load("coords.csv", header=False))
    
    # dumps test
    csv_str = dumps(data)
    print("[CSV] dumps:\n", csv_str)
    
    # loads test
    parsed = loads(csv_str)
    print("[CSV] loads:", parsed)

# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------