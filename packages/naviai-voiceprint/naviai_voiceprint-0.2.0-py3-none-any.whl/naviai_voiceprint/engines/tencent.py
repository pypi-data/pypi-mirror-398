from __future__ import annotations

import base64
from typing import Dict, List, Optional

from naviai_voiceprint.engines.base import AbstractVoiceprintEngine
from naviai_voiceprint.error_mapper import map_error
from naviai_voiceprint.error_types import ErrorCategory, ServiceErrorSubtype
from naviai_voiceprint.utils import ensure_audio_bytes, b64encode_bytes

# TencentCloud ASR VoicePrint APIs (2019-06-14)
try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.asr.v20190614 import asr_client, models
except ImportError as e:
    raise ImportError("Please install tencentcloud-sdk-python: pip install tencentcloud-sdk-python") from e


class TencentEngine(AbstractVoiceprintEngine):
    VENDOR = "tencent"

    def __init__(self, config):
        super().__init__(config)

        creds = config.credentials or {}
        self.secret_id = creds.get("secret_id")
        self.secret_key = creds.get("secret_key")
        self.region = config.region or creds.get("region") or "ap-beijing"

        if not self.secret_id or not self.secret_key:
            raise map_error(vendor=self.VENDOR, raw_message="missing credentials")

        # Setup client with timeout
        http_profile = HttpProfile()
        http_profile.reqTimeout = int(config.timeout_sec)

        client_profile = ClientProfile(httpProfile=http_profile)

        cred = credential.Credential(self.secret_id, self.secret_key)
        self.client = asr_client.AsrClient(cred, self.region, client_profile)

        self.group_id = config.group_id
        self.voice_format = int(config.voice_format or 0)  # 0 pcm, 1 wav
        self.sample_rate = int(config.sample_rate or 16000)

    # ---- Helpers ----
    def _call(self, fn, req, *, operation: str):
        try:
            return fn(req)
        except Exception as e:
            raise map_error(vendor=self.VENDOR, operation=operation, exception=e)

    # ---- Group / library ----
    # Tencent does NOT have "create group" in the same sense; groupId is provided during enroll
    def create_group(self, group_id: str, *, group_name: str = "", group_info: str = "") -> Dict:
        raise map_error(
            vendor=self.VENDOR,
            operation="create_group",
            raw_message="Tencent VoicePrint API does not provide explicit create_group; use GroupId in enroll",
            raw_code="NotSupported",
        )

    def delete_group(self, group_id: str) -> Dict:
        """
        Tencent deletes group via VoicePrintDelete with DelMod=2 (delete group only).
        """
        req = models.VoicePrintDeleteRequest()
        req.GroupId = group_id
        req.DelMod = 2
        resp = self._call(self.client.VoicePrintDelete, req, operation="delete_group")
        # Response: Data { VoicePrintId, SpeakerNick } maybe empty; still return dict
        return {
            "group_id": group_id,
            "request_id": getattr(resp, "RequestId", None),
        }

    # ---- Feature / speaker ----
    def register(self, audio: bytes, user_id: str, user_info: str, group_id: Optional[str]) -> Dict:
        """
        Tencent: VoicePrintEnroll returns VoicePrintId (speaker id).
        Note: Tencent API does NOT accept a custom user_id as VoicePrintId.
              We keep user_id as a 'SpeakerNick' (human readable label).
        """
        audio_b = ensure_audio_bytes(audio)
        if not audio_b:
            raise map_error(vendor=self.VENDOR, operation="register", raw_message="empty audio")

        req = models.VoicePrintEnrollRequest()
        req.VoiceFormat = self.voice_format
        req.SampleRate = self.sample_rate
        req.Data = b64encode_bytes(audio_b)
        req.SpeakerNick = user_id  # map SDK user_id -> Tencent SpeakerNick (best effort)
        if group_id or self.group_id:
            req.GroupId = group_id or self.group_id

        resp = self._call(self.client.VoicePrintEnroll, req, operation="register")

        data = getattr(resp, "Data", None)
        return {
            "voice_print_id": getattr(data, "VoicePrintId", None) if data else None,
            "speaker_nick": getattr(data, "SpeakerNick", None) if data else None,
            "request_id": getattr(resp, "RequestId", None),
        }

    def update_user(self, audio: bytes, user_id: str, user_info: str, group_id: Optional[str], *, cover: bool = True) -> Dict:
        """
        Tencent: VoicePrintUpdate requires VoicePrintId.
        For SDK consistency: user_id should be Tencent VoicePrintId here.
        """
        audio_b = ensure_audio_bytes(audio)
        if not audio_b:
            raise map_error(vendor=self.VENDOR, operation="update_user", raw_message="empty audio")

        req = models.VoicePrintUpdateRequest()
        req.VoiceFormat = self.voice_format
        req.SampleRate = self.sample_rate
        req.VoicePrintId = user_id
        req.Data = b64encode_bytes(audio_b)
        if user_info:
            req.SpeakerNick = user_info[:32]

        resp = self._call(self.client.VoicePrintUpdate, req, operation="update_user")

        data = getattr(resp, "Data", None)
        return {
            "voice_print_id": getattr(data, "VoicePrintId", None) if data else None,
            "speaker_nick": getattr(data, "SpeakerNick", None) if data else None,
            "request_id": getattr(resp, "RequestId", None),
        }

    def delete_user(self, user_id: str, group_id: Optional[str]) -> Dict:
        """
        Tencent: VoicePrintDelete.
        DelMod:
          0: delete voiceprint
          1: remove from group only
        We'll use DelMod=0 by default.
        """
        req = models.VoicePrintDeleteRequest()
        req.VoicePrintId = user_id
        if group_id or self.group_id:
            req.GroupId = group_id or self.group_id
        req.DelMod = 0

        resp = self._call(self.client.VoicePrintDelete, req, operation="delete_user")
        data = getattr(resp, "Data", None)
        return {
            "voice_print_id": getattr(data, "VoicePrintId", None) if data else None,
            "speaker_nick": getattr(data, "SpeakerNick", None) if data else None,
            "request_id": getattr(resp, "RequestId", None),
        }

    def list_users(self, group_id: Optional[str]) -> List[Dict]:
        """
        Tencent docs you pasted don't include "list users" API in this excerpt.
        If you have one elsewhere, we can implement it. For now: not supported.
        """
        raise map_error(
            vendor=self.VENDOR,
            operation="list_users",
            raw_message="Tencent VoicePrint API list operation is not implemented in this SDK version",
            raw_code="NotSupported",
        )

    # ---- Verify / identify ----
    def verify_1to1(self, audio: bytes, user_id: str, group_id: Optional[str]) -> float:
        """
        Tencent: VoicePrintVerify requires VoicePrintId.
        """
        audio_b = ensure_audio_bytes(audio)
        if not audio_b:
            raise map_error(vendor=self.VENDOR, operation="verify_1to1", raw_message="empty audio")

        req = models.VoicePrintVerifyRequest()
        req.VoiceFormat = self.voice_format
        req.SampleRate = self.sample_rate
        req.Data = b64encode_bytes(audio_b)
        req.VoicePrintId = user_id

        resp = self._call(self.client.VoicePrintVerify, req, operation="verify_1to1")
        data = getattr(resp, "Data", None)
        # score in docs is "60.0" string, range [0,100]
        try:
            return float(getattr(data, "Score", 0.0)) if data else 0.0
        except Exception:
            return 0.0

    def identify_1toN(self, audio: bytes, top_k: int, group_id: Optional[str]) -> List[Dict]:
        """
        Tencent: VoicePrintGroupVerify returns TopN results inside a group.
        """
        audio_b = ensure_audio_bytes(audio)
        if not audio_b:
            raise map_error(vendor=self.VENDOR, operation="identify_1toN", raw_message="empty audio")

        gid = group_id or self.group_id
        if not gid:
            raise map_error(vendor=self.VENDOR, operation="identify_1toN", raw_message="missing group_id")

        req = models.VoicePrintGroupVerifyRequest()
        req.VoiceFormat = self.voice_format
        req.SampleRate = self.sample_rate
        req.Data = b64encode_bytes(audio_b)
        req.GroupId = gid
        req.TopN = int(top_k)

        resp = self._call(self.client.VoicePrintGroupVerify, req, operation="identify_1toN")
        data = getattr(resp, "Data", None)
        verify_tops = getattr(data, "VerifyTops", None) if data else None
        if not verify_tops:
            return []

        out: List[Dict] = []
        for item in verify_tops:
            out.append(
                {
                    "score": float(getattr(item, "Score", 0.0)),
                    "speaker_id": getattr(item, "SpeakerId", None),
                    "voice_print_id": getattr(item, "VoicePrintId", None),
                }
            )
        return out

    # ---- Optional extra abilities ----
    def compare_audio(self, src_audio: bytes, dest_audio: bytes) -> float:
        src = ensure_audio_bytes(src_audio)
        dst = ensure_audio_bytes(dest_audio)
        if not src or not dst:
            raise map_error(vendor=self.VENDOR, operation="compare_audio", raw_message="empty audio")

        req = models.VoicePrintCompareRequest()
        req.VoiceFormat = self.voice_format
        req.SampleRate = self.sample_rate
        req.SrcAudioData = b64encode_bytes(src)
        req.DestAudioData = b64encode_bytes(dst)

        resp = self._call(self.client.VoicePrintCompare, req, operation="compare_audio")
        data = getattr(resp, "Data", None)
        try:
            return float(getattr(data, "Score", 0.0)) if data else 0.0
        except Exception:
            return 0.0

    def count_users(self, group_id: Optional[str] = None) -> int:
        req = models.VoicePrintCountRequest()
        if group_id:
            req.GroupId = group_id
            req.CountMod = 1
        else:
            req.CountMod = 0

        resp = self._call(self.client.VoicePrintCount, req, operation="count_users")
        data = getattr(resp, "Data", None)
        try:
            return int(getattr(data, "Total", 0)) if data else 0
        except Exception:
            return 0

