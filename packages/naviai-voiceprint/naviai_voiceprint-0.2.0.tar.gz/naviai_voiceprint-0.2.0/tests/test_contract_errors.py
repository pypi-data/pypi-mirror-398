import pytest

from naviai_voiceprint.error_mapper import map_error
from naviai_voiceprint.errors import (
    VoiceprintAuthError,
    VoiceprintInputError,
    VoiceprintServiceError,
    VoiceprintError,
)


def test_http_401_maps_to_auth_and_preserves_raw():
    e = map_error(
        vendor="xunfei",
        operation="create_group",
        http_status=401,
        raw_message='{"message":"Unauthorized"}',
        raw_response={"message": "Unauthorized"},
    )
    assert isinstance(e, VoiceprintAuthError)
    d = e.to_dict()
    assert d["vendor"] == "xunfei"
    assert d["http_status"] == 401
    assert d["raw_message"] is not None
    assert "Unauthorized" in d["raw_message"]


def test_input_maps_and_preserves_union_fields():
    e = map_error(
        vendor="tencent",
        operation="verify_1to1",
        raw_code="InvalidParameterValue.NoHumanVoice",
        raw_message="音频内容没有人声或有效人声小于1秒",
        request_id="req-123",
        raw_response={"Response": {"Error": {"Code": "InvalidParameterValue.NoHumanVoice"}}},
    )
    assert isinstance(e, VoiceprintInputError)
    d = e.to_dict()
    # union: all raw info must be preserved
    assert d["raw_code"] is not None
    assert d["raw_message"] is not None
    assert d["request_id"] == "req-123"
    assert d["raw_response"] is not None


def test_5xx_maps_to_service_internal():
    e = map_error(
        vendor="xunfei",
        operation="any",
        http_status=503,
        raw_message="Service Unavailable",
    )
    assert isinstance(e, VoiceprintServiceError)
    assert e.http_status == 503


def test_voiceprint_error_is_catch_all_base():
    e = map_error(vendor="xunfei", raw_message="anything")
    assert isinstance(e, VoiceprintError)

