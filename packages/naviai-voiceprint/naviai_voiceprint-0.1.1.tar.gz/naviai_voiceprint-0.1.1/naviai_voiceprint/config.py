class VoiceprintConfig:
    """
    声纹 SDK 的统一配置对象
    """

    def __init__(
        self,
        engine: str,
        credentials: dict,
        group_id: str = None,
        api_url: str = None,
        audio_encoding: str = "lame",
        sample_rate: int = 16000,
        channels: int = 1,
        bit_depth: int = 16,
        timeout_sec: int = 30,
        max_retry_times: int = 3,
        retry_delay: int = 1,
    ):
        self.engine = engine
        self.credentials = credentials

        self.group_id = group_id
        self.api_url = api_url

        self.audio_encoding = audio_encoding
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth

        self.timeout_sec = timeout_sec
        self.max_retry_times = max_retry_times
        self.retry_delay = retry_delay

