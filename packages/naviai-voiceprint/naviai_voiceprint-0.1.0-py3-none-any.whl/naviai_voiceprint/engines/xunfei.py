import base64
import json
import hmac
import hashlib
import time
import requests
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

from naviai_voiceprint.engines.base import AbstractVoiceprintEngine
from naviai_voiceprint.errors import (
    VoiceprintInputError,
    VoiceprintAuthError,
    VoiceprintServiceError,
)


class XunfeiEngine(AbstractVoiceprintEngine):
    def __init__(self, config):
        super().__init__(config)

        creds = config.credentials
        self.appid = creds.get("appid")
        self.api_key = creds.get("api_key")
        self.api_secret = creds.get("api_secret")

        if not self.appid or not self.api_key or not self.api_secret:
            raise VoiceprintAuthError("missing xunfei credentials")

        self.api_url = config.api_url
        self.group_id = config.group_id
        self.timeout = config.timeout_sec

        self.session = requests.Session()

    def _auth_url(self):
        stidx = self.api_url.index("://")
        host = self.api_url[stidx + 3:]
        edidx = host.index("/")
        path = host[edidx:]
        host = host[:edidx]

        now = datetime.utcnow()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = (
            f"host: {host}\n"
            f"date: {date}\n"
            f"POST {path} HTTP/1.1"
        )

        signature_sha = hmac.new(
            self.api_secret.encode(),
            signature_origin.encode(),
            digestmod=hashlib.sha256,
        ).digest()

        signature = base64.b64encode(signature_sha).decode()

        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(
            authorization_origin.encode()
        ).decode()

        return self.api_url + "?" + urlencode(
            {"host": host, "date": date, "authorization": authorization}
        )

    def _post(self, body: dict) -> dict:
        try:
            resp = self.session.post(
                self._auth_url(),
                headers={
                    "content-type": "application/json",
                    "appid": self.appid,
                },
                data=json.dumps(body),
                timeout=self.timeout,
            )
        except requests.Timeout:
            raise VoiceprintServiceError("request timeout")
        except Exception as e:
            raise VoiceprintServiceError(str(e))

        result = resp.json()
        header = result.get("header", {})
        if header.get("code") != 0:
            raise VoiceprintServiceError(header.get("message", "xunfei error"))
        return result

    def create_group(self, group_id: str):
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                "s782b4996": {
                    "func": "createGroup",
                    "groupId": group_id,
                    "createGroupRes": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "json",
                    },
                }
            },
        }
        self._post(body)

    def register(self, audio: bytes, user_id: str, user_info: str, group_id: str):
        if not audio:
            raise VoiceprintInputError("empty audio")

        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                "s782b4996": {
                    "func": "createFeature",
                    "groupId": group_id,
                    "featureId": user_id,
                    "featureInfo": user_info or "",
                    "createFeatureRes": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "json",
                    },
                }
            },
            "payload": {
                "resource": {
                    "encoding": self.config.audio_encoding,
                    "sample_rate": self.config.sample_rate,
                    "channels": self.config.channels,
                    "bit_depth": self.config.bit_depth,
                    "status": 3,
                    "audio": base64.b64encode(audio).decode(),
                }
            },
        }
        self._post(body)

    def verify_1to1(self, audio: bytes, user_id: str, group_id: str) -> float:
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                "s782b4996": {
                    "func": "searchScoreFea",
                    "groupId": group_id,
                    "dstFeatureId": user_id,
                    "searchScoreFeaRes": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "json",
                    },
                }
            },
            "payload": {
                "resource": {
                    "encoding": self.config.audio_encoding,
                    "sample_rate": self.config.sample_rate,
                    "channels": self.config.channels,
                    "bit_depth": self.config.bit_depth,
                    "status": 3,
                    "audio": base64.b64encode(audio).decode(),
                }
            },
        }
        resp = self._post(body)
        payload = resp.get("payload", {}).get("searchScoreFeaRes", {})
        data = json.loads(base64.b64decode(payload.get("text", "")).decode())
        return float(data.get("score", 0.0))

    def identify_1toN(self, audio: bytes, top_k: int, group_id: str):
        body = {
            "header": {"app_id": self.appid, "status": 3},
            "parameter": {
                "s782b4996": {
                    "func": "searchFea",
                    "groupId": group_id,
                    "topK": top_k,
                    "searchFeaRes": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "json",
                    },
                }
            },
            "payload": {
                "resource": {
                    "encoding": self.config.audio_encoding,
                    "sample_rate": self.config.sample_rate,
                    "channels": self.config.channels,
                    "bit_depth": self.config.bit_depth,
                    "status": 3,
                    "audio": base64.b64encode(audio).decode(),
                }
            },
        }
        resp = self._post(body)
        payload = resp.get("payload", {}).get("searchFeaRes", {})
        data = json.loads(base64.b64decode(payload.get("text", "")).decode())
        return data.get("scoreList", [])

