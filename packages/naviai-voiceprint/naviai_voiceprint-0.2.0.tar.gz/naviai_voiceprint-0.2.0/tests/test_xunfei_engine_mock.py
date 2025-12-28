# tests/test_xunfei_engine_mock.py
import json
import pytest

from naviai_voiceprint.client import VoiceprintClient
from naviai_voiceprint.config import VoiceprintConfig
from naviai_voiceprint.errors import VoiceprintAuthError, VoiceprintServiceError


class DummyResp:
    def __init__(self, status_code: int, text: str, json_obj=None):
        self.status_code = status_code
        self.text = text
        self._json_obj = json_obj

    def json(self):
        if self._json_obj is None:
            raise ValueError("not json")
        return self._json_obj


def test_xunfei_401_auth_error(monkeypatch):
    cfg = VoiceprintConfig(
        engine="xunfei",
        credentials={"appid": "a", "api_key": "k", "api_secret": "s"},
        group_id="g",
        api_url="https://api.xf-yun.com/v1/private/s782b4996",
    )
    vp = VoiceprintClient(cfg)

    def fake_post(*args, **kwargs):
        return DummyResp(401, '{"message":"Unauthorized"}', json_obj={"message": "Unauthorized"})

    monkeypatch.setattr(vp.engine.session, "post", fake_post)

    with pytest.raises(VoiceprintAuthError) as ei:
        vp.create_group()

    e = ei.value
    assert e.http_status == 401
    assert "Unauthorized" in (e.raw_message or "")
    vp.close()


def test_xunfei_header_code_nonzero_maps(monkeypatch):
    cfg = VoiceprintConfig(
        engine="xunfei",
        credentials={"appid": "a", "api_key": "k", "api_secret": "s"},
        group_id="g",
        api_url="https://api.xf-yun.com/v1/private/s782b4996",
    )
    vp = VoiceprintClient(cfg)

    # emulate a valid JSON response but business error code != 0
    payload = {"header": {"code": 10160, "message": "parse request json error", "sid": "sid-1"}}
    def fake_post(*args, **kwargs):
        return DummyResp(200, json.dumps(payload, ensure_ascii=False), json_obj=payload)

    monkeypatch.setattr(vp.engine.session, "post", fake_post)

    with pytest.raises(VoiceprintServiceError) as ei:
        vp.create_group()

    e = ei.value
    # business error must preserve raw code + request id
    assert str(e.raw_code) == "10160"
    assert e.request_id == "sid-1"
    vp.close()

