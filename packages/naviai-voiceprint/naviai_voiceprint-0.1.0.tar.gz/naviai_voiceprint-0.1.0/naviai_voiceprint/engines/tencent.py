import base64
import time
from typing import List, Dict

from naviai_voiceprint.engines.base import AbstractVoiceprintEngine
from naviai_voiceprint.errors import (
    VoiceprintInputError,
    VoiceprintAuthError,
    VoiceprintServiceError,
    VoiceprintNotFoundError,
)

#  使用腾讯云官方 SDK
try:
    from tencentcloud.common import credential
    from tencentcloud.trtc.v20190722 import trtc_client, models
except ImportError:
    raise ImportError(
        "请先安装腾讯云 SDK: pip install tencentcloud-sdk-python"
    )


class TencentEngine(AbstractVoiceprintEngine):
    """
    腾讯云 TRTC 声纹引擎实现（v2.0）

    说明：
    - 以 VoicePrintId 作为 user_id
    - 不支持 verify_1to1 / identify_1toN（AI 对话声纹属于后续能力）
    """

    def __init__(self, config):
        super().__init__(config)

        creds = config.credentials
        self.secret_id = creds.get("secret_id")
        self.secret_key = creds.get("secret_key")
        self.region = creds.get("region", "ap-beijing")

        if not self.secret_id or not self.secret_key:
            raise VoiceprintAuthError("missing tencent credentials")

        cred = credential.Credential(self.secret_id, self.secret_key)
        self.client = trtc_client.TrtcClient(cred, self.region)

    # ---------- group 接口（腾讯不需要，直接忽略） ----------

    def create_group(self, group_id: str):
        # 腾讯无 group 概念，安全忽略
        return None

    # ---------- 声纹注册 ----------

    def register(self, audio: bytes, user_id: str, user_info: str, group_id: str):
        if not audio:
            raise VoiceprintInputError("empty audio")

        req = models.RegisterVoicePrintRequest()
        req.Audio = base64.b64encode(audio).decode()
        req.AudioFormat = 0  # wav
        req.AudioName = user_id
        req.AudioMetaInfo = user_info or ""
        req.ReqTimestamp = int(time.time() * 1000)

        try:
            resp = self.client.RegisterVoicePrint(req)
        except Exception as e:
            raise VoiceprintServiceError(str(e))

        return resp.VoicePrintId

    # ---------- 查询声纹 ----------

    def identify_1toN(self, audio: bytes, top_k: int, group_id: str):
        raise VoiceprintServiceError(
            "Tencent voiceprint identification is not supported in SDK v2.0"
        )

    def verify_1to1(self, audio: bytes, user_id: str, group_id: str):
        raise VoiceprintServiceError(
            "Tencent voiceprint verification is not supported in SDK v2.0"
        )

    # ---------- 删除声纹 ----------

    def delete_user(self, user_id: str, group_id: str):
        req = models.DeleteVoicePrintRequest()
        req.VoicePrintId = user_id

        try:
            self.client.DeleteVoicePrint(req)
        except Exception as e:
            if "NotFound" in str(e):
                raise VoiceprintNotFoundError(str(e))
            raise VoiceprintServiceError(str(e))

    # ---------- 查询列表 ----------

    def list_users(self, group_id: str) -> List[Dict]:
        req = models.DescribeVoicePrintRequest()
        req.DescribeMode = 1
        req.PageIndex = 1
        req.PageSize = 20

        try:
            resp = self.client.DescribeVoicePrint(req)
        except Exception as e:
            raise VoiceprintServiceError(str(e))

        return [
            {
                "user_id": item.VoicePrintId,
                "audio_name": item.AudioName,
                "meta": item.VoicePrintMetaInfo,
            }
            for item in (resp.Data or [])
        ]

