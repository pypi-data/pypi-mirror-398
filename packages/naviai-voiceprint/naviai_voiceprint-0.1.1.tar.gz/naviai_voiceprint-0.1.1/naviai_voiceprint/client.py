from naviai_voiceprint.config import VoiceprintConfig
from naviai_voiceprint.engines.xunfei import XunfeiEngine


class VoiceprintClient:
    def __init__(self, config: VoiceprintConfig):
        if config.engine != "xunfei":
            raise ValueError("only xunfei engine is supported now")

        self.engine = XunfeiEngine(config)

    def create_group(self, group_id=None):
        return self.engine.create_group(group_id or self.engine.group_id)

    def register(self, audio, user_id, user_info=""):
        return self.engine.register(audio, user_id, user_info, self.engine.group_id)

    def verify_1to1(self, audio, user_id):
        return self.engine.verify_1to1(audio, user_id, self.engine.group_id)

    def identify_1toN(self, audio, top_k=5):
        return self.engine.identify_1toN(audio, top_k, self.engine.group_id)

    def close(self):
        self.engine.close()

