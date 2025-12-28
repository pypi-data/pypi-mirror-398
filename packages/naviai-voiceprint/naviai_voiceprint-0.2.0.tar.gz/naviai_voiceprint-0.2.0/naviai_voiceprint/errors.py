from __future__ import annotations

from typing import Any, Dict, Optional


class VoiceprintError(Exception):
    """
    Base exception for naviai-voiceprint SDK.

    Semantic container:
    - category/subtype: SDK-defined semantic space
    - raw_* fields: vendor/protocol raw context (MUST be preserved)
    - diagnostic_hint: actionable guidance (optional, must not guess)
    """

    def __init__(
        self,
        *,
        category: str,
        message: str,
        vendor: str,
        subtype: Optional[str] = None,
        raw_code: Optional[Any] = None,
        raw_message: Optional[str] = None,
        http_status: Optional[int] = None,
        request_id: Optional[str] = None,
        diagnostic_hint: Optional[str] = None,
        raw_response: Optional[Any] = None,
    ):
        # message must be printable; but allow empty and fallback
        msg = message or "voiceprint error"
        super().__init__(msg)

        self.category = category
        self.subtype = subtype

        self.message = msg
        self.vendor = vendor

        self.raw_code = raw_code
        self.raw_message = raw_message
        self.http_status = http_status
        self.request_id = request_id
        self.raw_response = raw_response

        self.diagnostic_hint = diagnostic_hint

    def __str__(self) -> str:
        base = f"[{self.vendor}][{self.category}] {self.message}"
        if self.subtype:
            base += f" (subtype={self.subtype})"
        if self.raw_code is not None:
            base += f" [raw_code={self.raw_code}]"
        if self.http_status is not None:
            base += f" [http_status={self.http_status}]"
        if self.request_id:
            base += f" [request_id={self.request_id}]"
        if self.diagnostic_hint:
            base += f" [hint={self.diagnostic_hint}]"
        return base

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "subtype": self.subtype,
            "message": self.message,
            "vendor": self.vendor,
            "raw_code": self.raw_code,
            "raw_message": self.raw_message,
            "http_status": self.http_status,
            "request_id": self.request_id,
            "diagnostic_hint": self.diagnostic_hint,
            "raw_response": self.raw_response,
        }


class VoiceprintAuthError(VoiceprintError):
    pass


class VoiceprintInputError(VoiceprintError):
    pass


class VoiceprintNotFoundError(VoiceprintError):
    pass


class VoiceprintLimitError(VoiceprintError):
    pass


class VoiceprintTimeoutError(VoiceprintError):
    pass


class VoiceprintServiceError(VoiceprintError):
    pass

