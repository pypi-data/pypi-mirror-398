from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class VoiceprintConfig:
    """
    Unified config for voiceprint SDK.

    Notes:
    - Keep vendor-specific credentials in `credentials`.
    - Keep other vendor-specific options in `extra`.
    """
    engine: str
    credentials: Dict[str, Any]

    # Common
    group_id: Optional[str] = None
    timeout_sec: int = 30
    max_retry_times: int = 0
    retry_delay: float = 0.0

    # Xunfei specific
    api_url: Optional[str] = None  # e.g. https://api.xf-yun.com/v1/private/s782b4996
    audio_encoding: str = "lame"   # xunfei requires mp3 "lame"
    sample_rate: int = 16000
    channels: int = 1
    bit_depth: int = 16

    # Tencent specific
    region: Optional[str] = None  # e.g. ap-beijing
    voice_format: Optional[int] = None  # 0 pcm, 1 wav (Tencent)

    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.engine = (self.engine or "").strip().lower()

        if not isinstance(self.credentials, dict):
            raise ValueError("credentials must be a dict")

        if not isinstance(self.timeout_sec, int) or self.timeout_sec <= 0:
            raise ValueError("timeout_sec must be positive int")

        if self.engine not in ("xunfei", "tencent"):
            raise ValueError("engine must be one of: xunfei, tencent")

        if self.engine == "xunfei":
            if not self.api_url:
                raise ValueError("xunfei requires api_url")
            # group_id is required by almost all operations; allow None but then client must pass group_id explicitly
            # keep defaults for mp3
            if self.sample_rate != 16000:
                # xunfei doc says 16k
                pass

        if self.engine == "tencent":
            # region optional; Tencent Cloud SDK can work without explicit region in some configs but keep it
            if self.voice_format is None:
                # default pcm
                self.voice_format = 0
            if self.sample_rate != 16000:
                # Tencent voiceprint API currently supports 16000 only (per your doc)
                pass

