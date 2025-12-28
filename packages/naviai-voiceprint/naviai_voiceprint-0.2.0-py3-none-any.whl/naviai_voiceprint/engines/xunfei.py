from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime
from time import mktime
from typing import Dict, List, Optional
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import requests

from naviai_voiceprint.engines.base import AbstractVoiceprintEngine
from naviai_voiceprint.error_mapper import map_error
from naviai_voiceprint.utils import (
    b64decode_to_text,
    b64encode_bytes,
    ensure_audio_bytes,
    safe_json_loads,
    safe_get,
)


class XunfeiEngine(AbstractVoiceprintEngine):
    VENDOR = "xunfei"
    XF_HOST = "api.xf-yun.com"
    FUNC_NS = "s782b4996"

    def __init__(self, config):
        super().__init__(config)

        creds = config.credentials or {}
        self.appid = creds.get("appid")
        self.api_key = creds.get("api_key")
        self.api_secret = creds.get("api_secret")

        if not self.appid or not self.api_key or not self.api_secret:
            raise map_error(vendor=self.VENDOR, raw_message="missing credentials")

        self.api_url = config.api_url
        self.group_id = config.group_id
        self.timeout = config.timeout_sec

        self.session = requests.Session()

    def _auth_url(self) -> str:
        stidx = self.api_url.index("://")
        host = self.api_url[stidx + 3:]
        edidx = host.index("/")
        path = host[edidx:]
        host_only = host[:edidx]

        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))  # NOTE: to follow your existing code path

        signature_origin = (
            f"host: {host_only}\n"
            f"date: {date}\n"
            f"POST {path} HTTP/1.1"
        )

        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        signature = base64.b64encode(signature_sha).decode("utf-8")

        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

        return self.api_url + "?" + urlencode({"host": host_only, "date": date, "authorization": authorization})

    def _post(self, body: dict, *, operation: str) -> Dict:
        try:
            resp = self.session.post(
                self._auth_url(),
                headers={
                    "content-type": "application/json",
                    "appid": self.appid,
                    "host": self.XF_HOST,
                },
                data=json.dumps(body, ensure_ascii=False),
                timeout=self.timeout,
            )
        except Exception as e:
            raise map_error(vendor=self.VENDOR, operation=operation, exception=e)

        http_status = resp.status_code
        text = resp.text

        # Protocol auth failure: doc says 401/403 may return {"message": "..."} with no header
        if http_status in (401, 403):
            # try parse JSON for message field
            parsed = safe_json_loads(text) if isinstance(text, str) else None
            msg = None
            if isinstance(parsed, dict):
                msg = parsed.get("message") or parsed.get("Message")
            raise map_error(
                vendor=self.VENDOR,
                operation=operation,
                http_status=http_status,
                raw_message=msg or text,
                raw_response=parsed or text,
            )

        # Try JSON parse (business response)
        try:
            result = resp.json()
        except Exception:
            raise map_error(
                vendor=self.VENDOR,
                operation=operation,
                http_status=http_status,
                raw_message=text,
                raw_response=text,
            )

        header = result.get("header", {}) if isinstance(result, dict) else {}
        code = header.get("code", None)
        message = header.get("message")
        sid = header.get("sid")

        if code == 0:
            return result

        raise map_error(
            vendor=self.VENDOR,
            operation=operation,
            http_status=http_status,
            raw_code=code,
            raw_message=message,
            request_id=sid,
            raw_response=result,
        )

    def _resource_payload(self, audio: bytes) -> Dict:
        return {
            "resource": {
                "encoding": self.config.audio_encoding,
                "sample_rate": self.config.sample_rate,
                "channels": self.config.channels,
                "bit_depth": self.config.bit_depth,
                "status": 3,
                "audio": b64encode_bytes(audio),
            }
        }

    def _decode_payload_text(self, resp: Dict, key: str) -> Dict:
        payload = safe_get(resp, "payload", key, default={})
        text_b64 = payload.get("text", "")
        decoded = b64decode_to_text(text_b64)
        data = safe_json_loads(decoded)
        if data is None:
            raise map_error(
                vendor=self.VENDOR,
                operation=f"decode_{key}",
                raw_message="failed to decode payload text as json",
                raw_response={"decoded_text": decoded, "payload": payload, "resp": resp},
            )
        return data

    # 1) create group
    def create_group(self, group_id: str, *, group_name: str = "", group_info: str = "") -> Dict:
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                self.FUNC_NS: {
                    "func": "createGroup",
                    "groupId": group_id,
                    "groupName": group_name or "",
                    "groupInfo": group_info or "",
                    "createGroupRes": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
        }
        resp = self._post(body, operation="create_group")
        return self._decode_payload_text(resp, "createGroupRes")

    # 8) delete group
    def delete_group(self, group_id: str) -> Dict:
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                self.FUNC_NS: {
                    "func": "deleteGroup",
                    "groupId": group_id,
                    "deleteGroupRes": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
        }
        resp = self._post(body, operation="delete_group")
        return self._decode_payload_text(resp, "deleteGroupRes")

    # 2) create feature
    def register(self, audio: bytes, user_id: str, user_info: str, group_id: Optional[str]) -> Dict:
        audio_b = ensure_audio_bytes(audio)
        if not audio_b:
            raise map_error(vendor=self.VENDOR, operation="register", raw_message="empty audio")

        gid = group_id or self.group_id
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                self.FUNC_NS: {
                    "func": "createFeature",
                    "groupId": gid,
                    "featureId": user_id,
                    "featureInfo": user_info or "",
                    "createFeatureRes": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
            "payload": self._resource_payload(audio_b),
        }
        resp = self._post(body, operation="register")
        return self._decode_payload_text(resp, "createFeatureRes")

    # 6) update feature
    def update_user(self, audio: bytes, user_id: str, user_info: str, group_id: Optional[str], *, cover: bool = True) -> Dict:
        audio_b = ensure_audio_bytes(audio)
        if not audio_b:
            raise map_error(vendor=self.VENDOR, operation="update_user", raw_message="empty audio")

        gid = group_id or self.group_id
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                self.FUNC_NS: {
                    "func": "updateFeature",
                    "groupId": gid,
                    "featureId": user_id,
                    "featureInfo": user_info or "",
                    "cover": bool(cover),
                    "updateFeatureRes": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
            "payload": self._resource_payload(audio_b),
        }
        resp = self._post(body, operation="update_user")
        return self._decode_payload_text(resp, "updateFeatureRes")

    # 7) delete feature
    def delete_user(self, user_id: str, group_id: Optional[str]) -> Dict:
        gid = group_id or self.group_id
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                self.FUNC_NS: {
                    "func": "deleteFeature",
                    "groupId": gid,
                    "featureId": user_id,
                    "deleteFeatureRes": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
        }
        resp = self._post(body, operation="delete_user")
        return self._decode_payload_text(resp, "deleteFeatureRes")

    # 5) query feature list
    def list_users(self, group_id: Optional[str]) -> List[Dict]:
        gid = group_id or self.group_id
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                self.FUNC_NS: {
                    "func": "queryFeatureList",
                    "groupId": gid,
                    "queryFeatureListRes": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
        }
        resp = self._post(body, operation="list_users")
        data = self._decode_payload_text(resp, "queryFeatureListRes")
        return data if isinstance(data, list) else []

    # 3) 1:1 score
    def verify_1to1(self, audio: bytes, user_id: str, group_id: Optional[str]) -> float:
        audio_b = ensure_audio_bytes(audio)
        if not audio_b:
            raise map_error(vendor=self.VENDOR, operation="verify_1to1", raw_message="empty audio")

        gid = group_id or self.group_id
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                self.FUNC_NS: {
                    "func": "searchScoreFea",
                    "groupId": gid,
                    "dstFeatureId": user_id,
                    "searchScoreFeaRes": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
            "payload": self._resource_payload(audio_b),
        }
        resp = self._post(body, operation="verify_1to1")
        data = self._decode_payload_text(resp, "searchScoreFeaRes")
        try:
            return float(data.get("score", 0.0))
        except Exception:
            return 0.0

    # 4) 1:N search
    def identify_1toN(self, audio: bytes, top_k: int, group_id: Optional[str]) -> List[Dict]:
        audio_b = ensure_audio_bytes(audio)
        if not audio_b:
            raise map_error(vendor=self.VENDOR, operation="identify_1toN", raw_message="empty audio")

        gid = group_id or self.group_id
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                self.FUNC_NS: {
                    "func": "searchFea",
                    "groupId": gid,
                    "topK": int(top_k),
                    "searchFeaRes": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
            "payload": self._resource_payload(audio_b),
        }
        resp = self._post(body, operation="identify_1toN")
        data = self._decode_payload_text(resp, "searchFeaRes")
        score_list = data.get("scoreList", [])
        return score_list if isinstance(score_list, list) else []

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

