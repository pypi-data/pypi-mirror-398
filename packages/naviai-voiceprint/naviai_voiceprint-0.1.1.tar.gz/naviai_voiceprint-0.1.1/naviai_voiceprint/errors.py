class VoiceprintError(Exception):
    """声纹模块基础异常"""


class VoiceprintAuthError(VoiceprintError):
    """鉴权或能力未开通错误"""


class VoiceprintInputError(VoiceprintError):
    """输入音频或参数非法"""


class VoiceprintNotFoundError(VoiceprintError):
    """声纹或用户不存在"""


class VoiceprintLimitError(VoiceprintError):
    """配额或次数限制"""


class VoiceprintTimeoutError(VoiceprintError):
    """请求超时"""


class VoiceprintServiceError(VoiceprintError):
    """第三方服务或内部错误"""

