# naviai-voiceprint

Unified Voiceprint Recognition SDK for Python.

This SDK provides a unified interface for multiple voiceprint engines,
allowing upper-layer applications to switch vendors without changing business code.

---

## Supported Engines

### ✅ Xunfei Voiceprint (Fully Supported)
- Create group
- Register voiceprint
- 1:1 verification
- 1:N identification

### ⚠️ Tencent Voiceprint (Management APIs Only)
- Register voiceprint
- Delete voiceprint
- Query voiceprint list

> Tencent voiceprint verification / identification is not yet available in SDK v0.1.x.

---

## Installation

```bash
pip install naviai-voiceprint
```

---

## Quick Start (Xunfei)

```python
from naviai_voiceprint.client import VoiceprintClient
from naviai_voiceprint.config import VoiceprintConfig
from naviai_voiceprint.errors import VoiceprintError

config = VoiceprintConfig(
    engine="xunfei",
    credentials={
        "appid": "YOUR_APPID",
        "api_key": "YOUR_API_KEY",
        "api_secret": "YOUR_API_SECRET",
    },
    group_id="demo_group",
    api_url="https://api.xf-yun.com/v1/private/s782b4996",
)

vp = VoiceprintClient(config)

with open("demo_audio.pcm", "rb") as f:
    audio = f.read()

try:
    vp.register(audio, user_id="user_001", user_info="demo user")
    score = vp.verify_1to1(audio, user_id="user_001")
    print("Verify score:", score)

except VoiceprintError as e:
    print("Voiceprint failed:", e)

finally:
    vp.close()
```

---

## Error Handling

All errors inherit from `VoiceprintError`.

- VoiceprintInputError
- VoiceprintAuthError
- VoiceprintNotFoundError
- VoiceprintLimitError
- VoiceprintTimeoutError
- VoiceprintServiceError

Upper-layer applications only need to handle this unified error class.

---

## Project Status

- SDK architecture: ✅ Stable
- Xunfei engine: ✅ Production-ready
- Tencent engine: ⚠️ Partial support (management APIs)
- API compatibility: ✅ Python 3.8+

This project is under active development.
