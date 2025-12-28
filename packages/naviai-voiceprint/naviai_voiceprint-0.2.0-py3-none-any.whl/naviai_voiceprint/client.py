from __future__ import annotations

from typing import Dict, List, Optional

from naviai_voiceprint.config import VoiceprintConfig
from naviai_voiceprint.error_mapper import map_error
from naviai_voiceprint.engines.xunfei import XunfeiEngine
from naviai_voiceprint.engines.tencent import TencentEngine


class VoiceprintClient:
    def __init__(self, config: VoiceprintConfig):
        self.config = config
        engine = (config.engine or "").strip().lower()

        if engine == "xunfei":
            self.engine = XunfeiEngine(config)
        elif engine == "tencent":
            self.engine = TencentEngine(config)
        else:
            raise map_error(vendor="sdk", raw_message=f"unsupported engine: {engine}")

    # ---- Group ----
    def create_group(self, group_id: Optional[str] = None, *, group_name: str = "", group_info: str = "") -> Dict:
        gid = group_id or self.config.group_id
        if not gid:
            raise map_error(vendor="sdk", operation="create_group", raw_message="missing group_id")
        return self.engine.create_group(gid, group_name=group_name, group_info=group_info)

    def delete_group(self, group_id: Optional[str] = None) -> Dict:
        gid = group_id or self.config.group_id
        if not gid:
            raise map_error(vendor="sdk", operation="delete_group", raw_message="missing group_id")
        return self.engine.delete_group(gid)

    # ---- Users / features ----
    def register(self, audio: bytes, user_id: str, user_info: str = "", group_id: Optional[str] = None) -> Dict:
        return self.engine.register(audio, user_id, user_info, group_id or self.config.group_id)

    def update_user(self, audio: bytes, user_id: str, user_info: str = "", group_id: Optional[str] = None, *, cover: bool = True) -> Dict:
        return self.engine.update_user(audio, user_id, user_info, group_id or self.config.group_id, cover=cover)

    def delete_user(self, user_id: str, group_id: Optional[str] = None) -> Dict:
        return self.engine.delete_user(user_id, group_id or self.config.group_id)

    def list_users(self, group_id: Optional[str] = None) -> List[Dict]:
        return self.engine.list_users(group_id or self.config.group_id)

    # ---- Verify / identify ----
    def verify_1to1(self, audio: bytes, user_id: str, group_id: Optional[str] = None) -> float:
        return self.engine.verify_1to1(audio, user_id, group_id or self.config.group_id)

    def identify_1toN(self, audio: bytes, top_k: int = 5, group_id: Optional[str] = None) -> List[Dict]:
        return self.engine.identify_1toN(audio, int(top_k), group_id or self.config.group_id)

    # ---- Extra abilities ----
    def compare_audio(self, src_audio: bytes, dest_audio: bytes) -> float:
        return self.engine.compare_audio(src_audio, dest_audio)

    def count_users(self, group_id: Optional[str] = None) -> int:
        return self.engine.count_users(group_id or self.config.group_id)

    def close(self):
        self.engine.close()

