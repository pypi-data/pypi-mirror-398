# Path: usekit.classes.data.base.post.parser.parser_pkl.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Pickle binary parser - 객체 직렬화/역직렬화 전용
# -----------------------------------------------------------------------------------------------

import os
import tempfile
import pickle
from pathlib import Path
from typing import Any, Union, Optional


# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _ensure_path(file: Union[str, Path]) -> Path:
    """Path 객체 보장"""
    return file if isinstance(file, Path) else Path(file)


def _atomic_write_binary(path: Path, data: bytes) -> None:
    """임시 파일에 먼저 쓰고 os.replace로 교체하는 원자적 바이너리 쓰기"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


# ───────────────────────────────────────────────────────────────
# Load / Loads
# ───────────────────────────────────────────────────────────────

def load(file, **kwargs) -> Any:
    """
    피클 파일 로딩 (binary → 객체 복원)
    - file 이 Path/str 이면 경로로 취급
    - file 이 file-like (read() 가진 객체)이면 그대로 pickle.load
    """
    # file-like 객체 (Binary I/O)
    if hasattr(file, "read") and not isinstance(file, (str, Path)):
        return pickle.load(file)

    # 경로 기반
    path = _ensure_path(file)
    with path.open("rb") as f:
        return pickle.load(f)


def loads(binary: bytes, **kwargs) -> Any:
    """메모리 상의 바이너리에서 객체 복원"""
    return pickle.loads(binary)


# ───────────────────────────────────────────────────────────────
# Dump / Dumps
# ───────────────────────────────────────────────────────────────

def dump(
    data: Any,
    file,
    *,
    protocol: Optional[int] = None,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    **kwargs
) -> None:
    """
    객체를 피클 파일로 저장 (객체 → binary)

    - file 이 file-like 이면 그대로 pickle.dump
    - file 이 Path/str 이면 실제 .pkl 파일로 저장
    - overwrite=False 이면 기존 파일 있을 때 예외
    - safe=True 이면 원자적 쓰기 사용
    - append=True 이면 기존 값을 리스트로 묶어 누적 저장
    """
    # 1) file-like 객체 (Binary I/O)
    if hasattr(file, "write") and not isinstance(file, (str, Path)):
        # 여기서는 호출하는 쪽에서 반드시 "wb" 모드로 열었다고 가정
        pickle.dump(data, file, protocol=protocol)
        return

    # 2) Path/str → 실제 파일 경로
    path = _ensure_path(file)

    if path.exists() and not overwrite:
        raise FileExistsError(f"[pkl.dump] Target exists and overwrite=False: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    # append 모드: 기존 데이터를 불러와 리스트로 누적
    if append and path.exists():
        try:
            with path.open("rb") as f:
                old = pickle.load(f)
            if isinstance(old, list):
                old.append(data)
            else:
                old = [old, data]
            data = old
        except Exception:
            data = [data]

    binary = pickle.dumps(data, protocol=protocol)

    if safe:
        _atomic_write_binary(path, binary)
    else:
        with path.open("wb") as f:
            f.write(binary)


def dumps(data: Any, *, protocol: Optional[int] = None, **kwargs) -> bytes:
    """
    객체를 바이너리로 직렬화 (메모리 상)
    """
    return pickle.dumps(data, protocol=protocol)


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(base="sample.pkl"):
    sample_data = {
        "name": "DSL",
        "version": "0.1.0",
        "features": ["pickle", "routing", "dsl", "ext"]
    }

    dump(sample_data, base)
    print("[PKL] wrote:", base)

    loaded = load(base)
    print("[PKL] read:", loaded)

    dump({"extra": 123}, base, append=True)
    print("[PKL] append:", load(base))

    binary = dumps(sample_data)
    print("[PKL] dumps:", binary[:40], "...")

    restored = loads(binary)
    print("[PKL] loads:", restored)