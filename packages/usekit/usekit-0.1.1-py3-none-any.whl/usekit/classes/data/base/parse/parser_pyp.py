# Path: usekit/classes/data/base/parse/pyp.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Python source (pyp/py) text parser - txt/md와 동일한 순수 텍스트 IO
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
from typing import Any, Union, Optional

# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _ensure_path(file: Union[str, Path]) -> Path:
    return file if isinstance(file, Path) else Path(file)


def _wrap_if_needed(data: Any, wrap: bool) -> Any:
    """
    pyp도 txt/md와 동일하게:
    - 문자열이면 그대로
    - 아니면 str()/repr()로 변환
    """
    if not wrap:
        return data

    if not isinstance(data, str):
        if isinstance(data, (dict, list)):
            return repr(data)
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
    Python(.pyp/.py) 소스를 그대로 읽어오는 단순 로더.
    """
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding) as f:
            text = f.read()
    else:
        text = file.read()

    if lines:
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
    문자열 기반 API. txt/md와 동일하게 그대로 반환.
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
    encoding: str = "utf-8",
    newline: Optional[str] = None,
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    append_newline: bool = True,
    **kwargs
) -> None:
    """
    Python 소스 쓰기. txt/md와 동일한 옵션:
      - overwrite / safe / append / append_newline
    """
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)

    data = _wrap_if_needed(data, wrap)
    if not isinstance(data, str):
        data = str(data)

    # append 모드
    if append:
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("a", encoding=encoding, newline=newline) as f:
                if append_newline and path_obj.exists() and path_obj.stat().st_size > 0:
                    if not data.startswith("\n"):
                        f.write("\n")
                f.write(data)
        else:
            if append_newline:
                file.write("\n")
            file.write(data)
        return

    # 일반 쓰기
    if path_obj:
        if path_obj.exists() and not overwrite:
            raise FileExistsError(
                f"[pyp.dump] Target exists and overwrite=False: {path_obj}"
            )

        if safe:
            _atomic_write_text(path_obj, data, encoding=encoding)
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding, newline=newline) as f:
                f.write(data)
        return

    file.write(data)


def dumps(
    data: Any,
    *,
    wrap: bool = False,
    **kwargs
) -> str:
    """
    Python 소스를 문자열로 직렬화 (사실상 str()).
    """
    data = _wrap_if_needed(data, wrap)
    if not isinstance(data, str):
        data = str(data)
    return data


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(base="sample.py"):
    dump("print('hello ROP')\n", base)
    print("[PYP] wrote:", base)
    print("[PYP] read:", repr(load(base)))
    print("[PYP] lines:", load(base, lines=True))
    dump("# appended", base, append=True)
    print("[PYP] appended:", load(base))