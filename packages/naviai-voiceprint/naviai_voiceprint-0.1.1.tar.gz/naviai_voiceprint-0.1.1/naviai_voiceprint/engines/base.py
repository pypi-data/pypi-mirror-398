from abc import ABC, abstractmethod
from typing import List, Dict
from naviai_voiceprint.config import VoiceprintConfig


class AbstractVoiceprintEngine(ABC):
    def __init__(self, config: VoiceprintConfig):
        self.config = config

    @abstractmethod
    def create_group(self, group_id: str):
        pass

    @abstractmethod
    def register(self, audio: bytes, user_id: str, user_info: str, group_id: str):
        pass

    @abstractmethod
    def verify_1to1(self, audio: bytes, user_id: str, group_id: str) -> float:
        pass

    @abstractmethod
    def identify_1toN(self, audio: bytes, top_k: int, group_id: str) -> List[Dict]:
        pass

    def close(self):
        pass

