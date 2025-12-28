from __future__ import annotations

from typing import Any, Optional, Tuple

from .errors import (
    VoiceprintAuthError,
    VoiceprintInputError,
    VoiceprintNotFoundError,
    VoiceprintLimitError,
    VoiceprintTimeoutError,
    VoiceprintServiceError,
)
from .error_types import (
    ErrorCategory,
    AuthErrorSubtype,
    InputErrorSubtype,
    NotFoundErrorSubtype,
    LimitErrorSubtype,
    TimeoutErrorSubtype,
    ServiceErrorSubtype,
)
from .utils import truncate_text, safe_json_loads, safe_get


def map_error(
    *,
    vendor: str,
    operation: Optional[str] = None,
    http_status: Optional[int] = None,
    raw_code: Optional[Any] = None,
    raw_message: Optional[str] = None,
    request_id: Optional[str] = None,
    raw_response: Optional[Any] = None,
    exception: Optional[Exception] = None,
) -> Exception:
    """
    The ONLY allowed place to interpret vendor/protocol errors.

    Always preserve raw info (union, not intersection).
    """

    # 0) Try to extract more info from exception (especially TencentCloud SDK)
    if exception is not None:
        ex_code, ex_msg, ex_req = _extract_from_exception(exception)
        raw_code = raw_code if raw_code is not None else ex_code
        raw_message = raw_message if raw_message is not None else ex_msg
        request_id = request_id if request_id is not None else ex_req

        # timeout-ish
        name = exception.__class__.__name__.lower()
        msg_lower = str(exception).lower()
        if "timeout" in name or "timed out" in msg_lower:
            return _build_exception(
                exc_cls=VoiceprintTimeoutError,
                category=ErrorCategory.TIMEOUT,
                subtype=TimeoutErrorSubtype.VENDOR_TIMEOUT,
                vendor=vendor,
                message="Request timed out",
                raw_code=raw_code,
                raw_message=str(exception),
                http_status=http_status,
                request_id=request_id,
                raw_response=raw_response,
                diagnostic_hint="Check network connectivity or increase timeout",
            )

    # 1) HTTP / protocol layer
    if http_status in (401, 403):
        subtype, hint = _auth_subtype_from_http(vendor, http_status, raw_message)
        return _build_exception(
            exc_cls=VoiceprintAuthError,
            category=ErrorCategory.AUTH,
            subtype=subtype,
            vendor=vendor,
            message="Authentication/authorization failed",
            raw_code=raw_code,
            raw_message=raw_message,
            http_status=http_status,
            request_id=request_id,
            raw_response=raw_response,
            diagnostic_hint=hint,
        )

    if http_status is not None and http_status >= 500:
        return _build_exception(
            exc_cls=VoiceprintServiceError,
            category=ErrorCategory.SERVICE,
            subtype=ServiceErrorSubtype.VENDOR_INTERNAL_ERROR,
            vendor=vendor,
            message="Vendor service internal error",
            raw_code=raw_code,
            raw_message=raw_message,
            http_status=http_status,
            request_id=request_id,
            raw_response=raw_response,
        )

    # 2) Semantic resolution from vendor raw info
    category = _resolve_category(vendor, raw_code, raw_message)
    subtype = _resolve_subtype(category, vendor, raw_code, raw_message)
    hint = _diagnostic_hint(category, subtype, vendor, raw_code, raw_message, operation)

    exc_cls = _category_to_exception(category)
    msg = _build_message(category, subtype, raw_message)

    return _build_exception(
        exc_cls=exc_cls,
        category=category,
        subtype=subtype,
        vendor=vendor,
        message=msg,
        raw_code=raw_code,
        raw_message=raw_message,
        http_status=http_status,
        request_id=request_id,
        raw_response=raw_response,
        diagnostic_hint=hint,
    )


def _extract_from_exception(exc: Exception) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    TencentCloud SDK exceptions often carry: code, message, request_id.
    We do best-effort extraction without hard dependency on class types.
    """
    code = getattr(exc, "code", None) or getattr(exc, "Code", None)
    msg = getattr(exc, "message", None) or getattr(exc, "Message", None)
    req = getattr(exc, "request_id", None) or getattr(exc, "RequestId", None)

    # Sometimes it's a string that contains JSON-like text
    if msg is None:
        msg = str(exc)

    # Try to parse JSON payload inside message if exists
    parsed = safe_json_loads(msg) if isinstance(msg, str) else None
    if isinstance(parsed, dict):
        code = code or safe_get(parsed, "Response", "Error", "Code")
        msg = msg or safe_get(parsed, "Response", "Error", "Message")
        req = req or safe_get(parsed, "Response", "RequestId")

    return (
        str(code) if code is not None else None,
        str(msg) if msg is not None else None,
        str(req) if req is not None else None,
    )


def _auth_subtype_from_http(vendor: str, http_status: int, raw_message: Optional[str]):
    m = (raw_message or "").lower()
    if http_status == 403 and ("date" in m or "x-date" in m or "clock" in m or "valid date" in m):
        return AuthErrorSubtype.TIMESTAMP_SKEW, "Check server time (UTC/GMT) and ensure < 5 min skew"
    if "signature does not match" in m:
        return AuthErrorSubtype.SIGNATURE_MISMATCH, "Check api_key/api_secret and signature string composition"
    if "unauthorized" in m or "missing authorization" in m:
        return AuthErrorSubtype.INVALID_CREDENTIAL, "Missing/invalid authorization parameters"
    return AuthErrorSubtype.PERMISSION_DENIED, None


def _resolve_category(vendor: str, raw_code: Any, raw_message: Optional[str]) -> ErrorCategory:
    code = (str(raw_code) if raw_code is not None else "").lower()
    msg = (raw_message or "").lower()

    # ---- Auth
    if "unauthorized" in msg or "signature" in msg or "permission" in msg or "auth" in msg:
        return ErrorCategory.AUTH
    if code.startswith("auth") or code.startswith("unauthorized"):
        return ErrorCategory.AUTH

    # ---- Input
    if "invalidparameter" in code or "invalidparameter" in msg or "missingparameter" in code:
        return ErrorCategory.INPUT
    if "invalidparameter" in msg or "missing parameter" in msg:
        return ErrorCategory.INPUT
    if "nohumanvoice" in code:
        return ErrorCategory.INPUT
    if "errorvoicedatatoolong" in code or "voicedata too long" in msg or "toolong" in code:
        return ErrorCategory.INPUT
    if "decode" in code and ("failed" in code or "failed" in msg):
        return ErrorCategory.INPUT

    # ---- Not found
    if "notexistent" in code or "not_existent" in code or "notexistentvoiceprintid" in code:
        return ErrorCategory.NOT_FOUND
    if code in ("23006", "23007"):
        return ErrorCategory.NOT_FOUND

    # ---- Limit
    if "limitexceeded" in code or "quota" in msg or code.startswith("limitexceeded"):
        return ErrorCategory.LIMIT

    # ---- Timeout
    if "timeout" in msg:
        return ErrorCategory.TIMEOUT

    return ErrorCategory.SERVICE


def _resolve_subtype(category: ErrorCategory, vendor: str, raw_code: Any, raw_message: Optional[str]):
    code = (str(raw_code) if raw_code is not None else "").lower()
    msg = (raw_message or "").lower()

    if category == ErrorCategory.AUTH:
        if "signature does not match" in msg:
            return AuthErrorSubtype.SIGNATURE_MISMATCH
        if "valid date" in msg or "x-date" in msg or "clock" in msg:
            return AuthErrorSubtype.TIMESTAMP_SKEW
        if "unauthorized" in msg:
            return AuthErrorSubtype.INVALID_CREDENTIAL
        return AuthErrorSubtype.AUTH_UNKNOWN

    if category == ErrorCategory.INPUT:
        if "nohumanvoice" in code:
            return InputErrorSubtype.NO_HUMAN_VOICE
        if "errorvoicedatatoolong" in code or "toolong" in code:
            return InputErrorSubtype.AUDIO_TOO_LONG
        if "decode" in code and "failed" in code:
            return InputErrorSubtype.AUDIO_DECODE_FAILED
        if "empty audio" in msg:
            return InputErrorSubtype.EMPTY_AUDIO
        return InputErrorSubtype.INPUT_UNKNOWN

    if category == ErrorCategory.NOT_FOUND:
        if "group" in code:
            return NotFoundErrorSubtype.GROUP_NOT_FOUND
        if "voiceprintid" in code or "feature" in code or "user" in code:
            return NotFoundErrorSubtype.USER_NOT_FOUND
        return NotFoundErrorSubtype.RESOURCE_NOT_FOUND

    if category == ErrorCategory.LIMIT:
        if "voiceprintfull" in code or "full" in code:
            return LimitErrorSubtype.QUOTA_EXCEEDED
        return LimitErrorSubtype.LIMIT_UNKNOWN

    if category == ErrorCategory.TIMEOUT:
        return TimeoutErrorSubtype.TIMEOUT_UNKNOWN

    if category == ErrorCategory.SERVICE:
        return ServiceErrorSubtype.SERVICE_UNKNOWN

    return None


def _diagnostic_hint(category, subtype, vendor, raw_code, raw_message, operation):
    if category == ErrorCategory.INPUT and subtype == InputErrorSubtype.NO_HUMAN_VOICE:
        return "Audio contains no human voice or effective voice < 1s; provide clear 3-5s speech"
    if category == ErrorCategory.INPUT and subtype == InputErrorSubtype.AUDIO_TOO_LONG:
        return "Audio too long; keep duration within vendor limit (e.g., Tencent <= 30s)"
    if category == ErrorCategory.AUTH and subtype == AuthErrorSubtype.TIMESTAMP_SKEW:
        return "Time skew detected; sync server time to UTC/GMT and ensure < 5 min difference"
    return None


def _category_to_exception(category: ErrorCategory):
    return {
        ErrorCategory.AUTH: VoiceprintAuthError,
        ErrorCategory.INPUT: VoiceprintInputError,
        ErrorCategory.NOT_FOUND: VoiceprintNotFoundError,
        ErrorCategory.LIMIT: VoiceprintLimitError,
        ErrorCategory.TIMEOUT: VoiceprintTimeoutError,
        ErrorCategory.SERVICE: VoiceprintServiceError,
    }[category]


def _build_message(category: ErrorCategory, subtype, raw_message: Optional[str]) -> str:
    if subtype is not None:
        return subtype.value.replace("_", " ").capitalize()
    if raw_message:
        return truncate_text(raw_message, 300) or f"{category.value} error"
    return f"{category.value} error"


def _build_exception(
    *,
    exc_cls,
    category: ErrorCategory,
    vendor: str,
    message: str,
    subtype=None,
    raw_code=None,
    raw_message=None,
    http_status=None,
    request_id=None,
    raw_response=None,
    diagnostic_hint=None,
):
    return exc_cls(
        category=category.value,
        subtype=subtype.value if subtype else None,
        vendor=vendor,
        message=message,
        raw_code=raw_code,
        raw_message=truncate_text(raw_message, 4000) if isinstance(raw_message, str) else raw_message,
        http_status=http_status,
        request_id=request_id,
        raw_response=raw_response,
        diagnostic_hint=diagnostic_hint,
    )

