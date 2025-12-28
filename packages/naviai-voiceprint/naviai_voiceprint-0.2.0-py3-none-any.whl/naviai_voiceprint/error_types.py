# naviai_voiceprint/error_types.py
from enum import Enum, unique


@unique
class ErrorCategory(str, Enum):
    AUTH = "auth"
    INPUT = "input"
    NOT_FOUND = "not_found"
    LIMIT = "limit"
    TIMEOUT = "timeout"
    SERVICE = "service"


@unique
class AuthErrorSubtype(str, Enum):
    INVALID_CREDENTIAL = "invalid_credential"
    SIGNATURE_MISMATCH = "signature_mismatch"
    TIMESTAMP_SKEW = "timestamp_skew"
    PERMISSION_DENIED = "permission_denied"
    CREDENTIAL_EXPIRED = "credential_expired"
    AUTH_UNKNOWN = "auth_unknown"


@unique
class InputErrorSubtype(str, Enum):
    EMPTY_AUDIO = "empty_audio"
    AUDIO_TOO_SHORT = "audio_too_short"
    AUDIO_TOO_LONG = "audio_too_long"
    AUDIO_FORMAT_UNSUPPORTED = "audio_format_unsupported"
    AUDIO_DECODE_FAILED = "audio_decode_failed"
    NO_HUMAN_VOICE = "no_human_voice"

    INVALID_SAMPLE_RATE = "invalid_sample_rate"
    INVALID_CHANNEL_CONFIG = "invalid_channel_config"
    INVALID_BIT_DEPTH = "invalid_bit_depth"

    INVALID_GROUP_ID = "invalid_group_id"
    INVALID_USER_ID = "invalid_user_id"
    INVALID_PARAMETER = "invalid_parameter"

    INPUT_UNKNOWN = "input_unknown"


@unique
class NotFoundErrorSubtype(str, Enum):
    GROUP_NOT_FOUND = "group_not_found"
    USER_NOT_FOUND = "user_not_found"
    FEATURE_NOT_FOUND = "feature_not_found"
    RESOURCE_NOT_FOUND = "resource_not_found"


@unique
class LimitErrorSubtype(str, Enum):
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMITED = "rate_limited"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    LIMIT_UNKNOWN = "limit_unknown"


@unique
class TimeoutErrorSubtype(str, Enum):
    CONNECT_TIMEOUT = "connect_timeout"
    READ_TIMEOUT = "read_timeout"
    VENDOR_TIMEOUT = "vendor_timeout"
    TIMEOUT_UNKNOWN = "timeout_unknown"


@unique
class ServiceErrorSubtype(str, Enum):
    VENDOR_INTERNAL_ERROR = "vendor_internal_error"
    DEPENDENCY_FAILURE = "dependency_failure"

    FEATURE_CREATION_FAILED = "feature_creation_failed"
    FEATURE_UPDATE_FAILED = "feature_update_failed"
    FEATURE_DELETE_FAILED = "feature_delete_failed"

    GROUP_CREATION_FAILED = "group_creation_failed"
    GROUP_DELETE_FAILED = "group_delete_failed"

    INCONSISTENT_STATE = "inconsistent_state"
    SERVICE_UNKNOWN = "service_unknown"

