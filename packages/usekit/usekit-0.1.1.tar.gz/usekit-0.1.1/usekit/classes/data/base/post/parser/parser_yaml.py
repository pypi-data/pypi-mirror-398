# Path: usekit.classes.data.base.post.parser.parser_yaml.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready YAML parser with append/overwrite/safe modes
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
from typing import Any, Union, Iterable

try:
    import yaml
    try:
        from yaml import CLoader as Loader, CDumper as Dumper
    except ImportError:
        from yaml import Loader, Dumper
except ImportError:
    raise ImportError(
        "PyYAML is required for YAML support. "
        "Install it with: pip install pyyaml"
    )

# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _serialize_yaml(
    data: Any,
    default_flow_style: bool,
    sort_keys: bool,
    indent: int,
    width: int,
    allow_unicode: bool,
    **kwargs
) -> str:
    """Serialize data to YAML string."""
    return yaml.dump(
        data,
        Dumper=Dumper,
        default_flow_style=default_flow_style,
        sort_keys=sort_keys,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        **kwargs
    )


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
    """Auto-wrap simple values into dict if needed."""
    if not wrap:
        return data
    if isinstance(data, str) and ":" in data:
        key, value = map(str.strip, data.split(":", 1))
        return {key: value}
    if not isinstance(data, (dict, list)):
        return {"value": data}
    return data

def _try_parse_yaml_stream(text: str) -> list:
    """
    Try to parse text as YAML stream (multiple documents).
    Returns list of parsed documents if successful.
    """
    try:
        docs = list(yaml.load_all(text, Loader=Loader))
        return docs if len(docs) > 1 else docs[0] if docs else None
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing failed: {e}") from e

# ───────────────────────────────────────────────────────────────
# Load / Loads
# ───────────────────────────────────────────────────────────────

def load(file, encoding: str = "utf-8", stream: bool = False, **kwargs):
    """
    Read YAML from a file.
    
    Args:
        file: File path or file-like object
        encoding: File encoding
        stream: If True, load multiple YAML documents (returns list)
        **kwargs: Additional arguments passed to yaml.load
        
    Returns:
        Parsed YAML data (dict, list, or list of documents if stream=True)
    """
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding) as f:
            text = f.read()
    else:
        text = file.read()
    
    if stream:
        return list(yaml.load_all(text, Loader=Loader, **kwargs))
    
    return yaml.load(text, Loader=Loader, **kwargs)


def loads(text: str, stream: bool = False, **kwargs):
    """
    Parse YAML from string.
    
    Args:
        text: YAML string
        stream: If True, parse multiple YAML documents (returns list)
        **kwargs: Additional arguments passed to yaml.load
        
    Returns:
        Parsed YAML data
    """
    if stream:
        return list(yaml.load_all(text, Loader=Loader, **kwargs))
    
    return yaml.load(text, Loader=Loader, **kwargs)


# ───────────────────────────────────────────────────────────────
# Dump / Dumps
# ───────────────────────────────────────────────────────────────

def dump(
    data: Any,
    file,
    *,
    # formatting
    default_flow_style: bool = False,
    sort_keys: bool = False,
    indent: int = 2,
    width: int = 80,
    allow_unicode: bool = True,
    encoding: str = "utf-8",
    # behavior
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    append_mode: str = "auto",  # 'auto' | 'array' | 'object' | 'stream'
    # extra kwargs passed to yaml.dump
    **kwargs
) -> None:
    """
    Write YAML to file.
    
    Modes:
        overwrite=False : raise if file exists
        safe=True       : atomic write (temp file -> replace)
        append=True     : append according to append_mode:
            - 'array'  : maintain top-level list, append new data
            - 'object' : shallow-merge dict (existing.update(data))
            - 'stream' : append as new YAML document (--- separator)
            - 'auto'   : detect existing top-level (array/object), else fallback:
                         dict→object, list→array, otherwise→stream
    
    Args:
        data: Data to serialize
        file: File path or file-like object
        default_flow_style: Use flow style (inline) for collections
        sort_keys: Sort dictionary keys
        indent: Indentation spaces
        width: Max line width
        allow_unicode: Allow unicode characters (don't escape)
        encoding: File encoding
        wrap: Auto-wrap simple values into dict
        overwrite: Allow overwriting existing file
        safe: Use atomic write
        append: Enable append mode
        append_mode: How to append data
        **kwargs: Additional yaml.dump arguments
    """
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)
    
    data = _wrap_if_needed(data, wrap)
    
    # ── STREAM append (YAML multi-document)
    if append and append_mode == "stream":
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            yaml_doc = _serialize_yaml(
                data, default_flow_style, sort_keys, 
                indent, width, allow_unicode, **kwargs
            )
            # Append as new document with separator
            with path_obj.open("a", encoding=encoding) as f:
                if path_obj.stat().st_size > 0:
                    f.write("---\n")
                f.write(yaml_doc)
                if not yaml_doc.endswith("\n"):
                    f.write("\n")
        else:
            # file-like object
            yaml_doc = _serialize_yaml(
                data, default_flow_style, sort_keys,
                indent, width, allow_unicode, **kwargs
            )
            file.write("---\n" + yaml_doc)
        return
    
    # ── Non-STREAM flows require structured write
    if path_obj:
        # overwrite guard
        if path_obj.exists() and not overwrite and not append:
            raise FileExistsError(
                f"[yaml.dump] Target exists and overwrite=False: {path_obj}"
            )
        
        # append with array/object/auto
        if append:
            existing = None
            if path_obj.exists():
                try:
                    existing = load(path_obj, encoding=encoding, stream=False)
                except Exception:
                    # if not valid YAML, fall back to stream append
                    append_mode = "stream"
                    return dump(
                        data, path_obj,
                        default_flow_style=default_flow_style,
                        sort_keys=sort_keys,
                        indent=indent, width=width,
                        allow_unicode=allow_unicode,
                        encoding=encoding,
                        wrap=False, overwrite=True, safe=safe,
                        append=True, append_mode="stream", **kwargs
                    )
            
            mode = append_mode or "auto"
            
            # AUTO detection
            if mode == "auto":
                if isinstance(existing, list):
                    mode = "array"
                elif isinstance(existing, dict) and isinstance(data, dict):
                    mode = "object"
                elif existing is None:
                    # decide by incoming data
                    if isinstance(data, list):
                        mode = "array"
                    elif isinstance(data, dict):
                        mode = "object"
                    else:
                        mode = "stream"
                else:
                    mode = "stream"
            
            if mode == "array":
                if existing is None:
                    target = data if isinstance(data, list) else [data]
                else:
                    if not isinstance(existing, list):
                        raise TypeError(
                            "[yaml.dump] append_mode='array' requires existing top-level list"
                        )
                    target = existing
                    if isinstance(data, list):
                        target.extend(data)
                    else:
                        target.append(data)
                text = _serialize_yaml(
                    target, default_flow_style, sort_keys,
                    indent, width, allow_unicode, **kwargs
                )
            
            elif mode == "object":
                if not isinstance(data, dict):
                    raise TypeError(
                        "[yaml.dump] append_mode='object' requires dict data"
                    )
                if existing is None:
                    target = data
                else:
                    if not isinstance(existing, dict):
                        raise TypeError(
                            "[yaml.dump] append_mode='object' requires existing top-level dict"
                        )
                    target = existing
                    target.update(data)
                text = _serialize_yaml(
                    target, default_flow_style, sort_keys,
                    indent, width, allow_unicode, **kwargs
                )
            
            elif mode == "stream":
                # delegate to stream branch
                return dump(
                    data, path_obj,
                    default_flow_style=default_flow_style,
                    sort_keys=sort_keys,
                    indent=indent, width=width,
                    allow_unicode=allow_unicode,
                    encoding=encoding,
                    wrap=False, overwrite=True, safe=safe,
                    append=True, append_mode="stream", **kwargs
                )
            else:
                raise ValueError(f"[yaml.dump] Unknown append_mode: {mode}")
            
            if safe:
                _atomic_write_text(path_obj, text, encoding=encoding)
            else:
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                with path_obj.open("w", encoding=encoding) as f:
                    f.write(text)
            return
        
        # normal overwrite write
        text = _serialize_yaml(
            data, default_flow_style, sort_keys,
            indent, width, allow_unicode, **kwargs
        )
        if safe:
            _atomic_write_text(path_obj, text, encoding=encoding)
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding) as f:
                f.write(text)
        return
    
    # file-like object path (no path_obj)
    yaml.dump(
        data, file,
        Dumper=Dumper,
        default_flow_style=default_flow_style,
        sort_keys=sort_keys,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        **kwargs
    )


def dumps(
    data: Any,
    *,
    default_flow_style: bool = False,
    sort_keys: bool = False,
    indent: int = 2,
    width: int = 80,
    allow_unicode: bool = True,
    wrap: bool = False,
    stream: bool = False,
    **kwargs
) -> str:
    """
    Serialize to YAML string.
    
    Args:
        data: Data to serialize
        default_flow_style: Use flow style (inline) for collections
        sort_keys: Sort dictionary keys
        indent: Indentation spaces
        width: Max line width
        allow_unicode: Allow unicode characters
        wrap: Auto-wrap simple values into dict
        stream: Add document separator (---)
        **kwargs: Additional yaml.dump arguments
        
    Returns:
        YAML string
    """
    data = _wrap_if_needed(data, wrap)
    
    yaml_str = _serialize_yaml(
        data, default_flow_style, sort_keys,
        indent, width, allow_unicode, **kwargs
    )
    
    if stream:
        return "---\n" + yaml_str
    
    return yaml_str


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(base="sample.yaml"):
    """Test YAML parser functionality."""
    obj = {"msg": "Hello ROP", "n": 1}
    
    # overwrite
    dump(obj, base, allow_unicode=True, indent=2)
    print("[YAML] wrote:", base)
    
    # append as array (auto)
    dump({"n": 2}, base, append=True, append_mode="auto", allow_unicode=True, indent=2)
    print("[YAML] appended(auto):", load(base))
    
    # append as object (merge)
    dump({"extra": True}, base, append=True, append_mode="object", allow_unicode=True, indent=2)
    print("[YAML] appended(object):", load(base))
    
    # stream (multi-document)
    ys = Path("sample_stream.yaml")
    dump({"a": 1}, ys, append=True, append_mode="stream")
    dump({"a": 2}, ys, append=True, append_mode="stream")
    print("[YAML-STREAM] read:", load(ys, stream=True))


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------