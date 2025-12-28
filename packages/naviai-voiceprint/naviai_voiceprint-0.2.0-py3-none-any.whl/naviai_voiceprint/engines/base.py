from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from naviai_voiceprint.config import VoiceprintConfig


class AbstractVoiceprintEngine(ABC):
    def __init__(self, config: VoiceprintConfig):
        self.config = config

    # ---- Group / library ----
    @abstractmethod
    def create_group(self, group_id: str, *, group_name: str = "", group_info: str = "") -> Dict:
        pass

    @abstractmethod
    def delete_group(self, group_id: str) -> Dict:
        pass

    # ---- Feature / speaker ----
    @abstractmethod
    def register(self, audio: bytes, user_id: str, user_info: str, group_id: Optional[str]) -> Dict:
        pass

    @abstractmethod
    def update_user(self, audio: bytes, user_id: str, user_info: str, group_id: Optional[str], *, cover: bool = True) -> Dict:
        pass

    @abstractmethod
    def delete_user(self, user_id: str, group_id: Optional[str]) -> Dict:
        pass

    @abstractmethod
    def list_users(self, group_id: Optional[str]) -> List[Dict]:
        pass

    # ---- Verify / identify ----
    @abstractmethod
    def verify_1to1(self, audio: bytes, user_id: str, group_id: Optional[str]) -> float:
        pass

    @abstractmethod
    def identify_1toN(self, audio: bytes, top_k: int, group_id: Optional[str]) -> List[Dict]:
        pass

    # ---- Optional extra abilities ----
    def compare_audio(self, src_audio: bytes, dest_audio: bytes) -> float:
        """Some vendors provide audio-to-audio compare (Tencent VoicePrintCompare)."""
        raise NotImplementedError

    def count_users(self, group_id: Optional[str] = None) -> int:
        """Some vendors provide count (Tencent VoicePrintCount)."""
        raise NotImplementedError

    def close(self):
        pass

