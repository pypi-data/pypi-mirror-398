from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional


def b64encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def b64decode_to_text(b64: str) -> str:
    if not b64:
        return ""
    return base64.b64decode(b64).decode("utf-8", errors="replace")


def safe_json_loads(text: str) -> Any:
    if text is None:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def safe_get(d: Any, *path: str, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
    return cur if cur is not None else default


def truncate_text(s: Optional[str], limit: int = 2000) -> Optional[str]:
    if s is None:
        return None
    if len(s) <= limit:
        return s
    return s[:limit] + "...(truncated)"


def ensure_audio_bytes(audio: Any) -> bytes:
    """
    Accept:
    - bytes
    - bytearray
    - memoryview
    """
    if audio is None:
        return b""
    if isinstance(audio, bytes):
        return audio
    if isinstance(audio, bytearray):
        return bytes(audio)
    if isinstance(audio, memoryview):
        return audio.tobytes()
    raise TypeError(f"audio must be bytes-like, got {type(audio)}")


def validate_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive int, got {value!r}")


def validate_non_empty_str(name: str, value: Optional[str]) -> None:
    if value is None or not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")

