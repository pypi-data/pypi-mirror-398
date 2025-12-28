import pytest

from naviai_voiceprint.error_mapper import map_error
from naviai_voiceprint.errors import VoiceprintInputError


class FakeTencentException(Exception):
    def __init__(self):
        self.code = "InvalidParameterValue.NoHumanVoice"
        self.message = "No human voice"
        self.request_id = "req-999"
        super().__init__(self.message)


def test_tencent_exception_extraction_and_mapping():
    e = map_error(
        vendor="tencent",
        operation="VoicePrintVerify",
        exception=FakeTencentException(),
    )
    assert isinstance(e, VoiceprintInputError)
    assert e.raw_code == "InvalidParameterValue.NoHumanVoice"
    assert e.request_id == "req-999"
    assert "No human voice" in (e.raw_message or "")

