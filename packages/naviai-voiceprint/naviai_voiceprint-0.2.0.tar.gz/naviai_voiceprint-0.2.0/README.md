# naviai-voiceprint

Unified Voiceprint Recognition SDK for Python.

This SDK provides a unified interface for multiple voiceprint engines,
allowing upper-layer applications to switch vendors without changing business code.

## Supported Engines

### ✅ Xunfei Voiceprint (WebAPI)
- Create group (`createGroup`)
- Delete group (`deleteGroup`)
- Register feature (`createFeature`)
- Update feature (`updateFeature`)
- Delete feature (`deleteFeature`)
- Query feature list (`queryFeatureList`)
- 1:1 verification (`searchScoreFea`)
- 1:N identification (`searchFea`)

### ✅ Tencent Cloud ASR VoicePrint (2019-06-14)
- Enroll speaker (`VoicePrintEnroll`)  -> returns `VoicePrintId`
- Verify 1:1 (`VoicePrintVerify`)      -> score [0, 100]
- Verify 1:N (`VoicePrintGroupVerify`) -> topN results in group
- Update (`VoicePrintUpdate`)
- Delete (`VoicePrintDelete`)
- Compare audio (`VoicePrintCompare`)
- Count (`VoicePrintCount`)
> Note: Tencent "create_group" is not an explicit API. Use `GroupId` during enroll.

## Installation

```bash
pip install naviai-voiceprint
````

For Tencent engine, ensure dependency:

```bash
pip install "naviai-voiceprint[tencent]"
```

## Quick Start (Xunfei)

```python
from naviai_voiceprint import VoiceprintClient, VoiceprintConfig, VoiceprintError

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

with open("demo_audio.mp3", "rb") as f:
    audio = f.read()

try:
    vp.create_group()
    vp.register(audio, user_id="user_001", user_info="demo user")
    score = vp.verify_1to1(audio, user_id="user_001")
    print("Verify score:", score)
except VoiceprintError as e:
    print("Voiceprint failed:", e)
finally:
    vp.close()
```

## Quick Start (Tencent)

```python
from naviai_voiceprint import VoiceprintClient, VoiceprintConfig, VoiceprintError

config = VoiceprintConfig(
    engine="tencent",
    credentials={
        "secret_id": "YOUR_SECRET_ID",
        "secret_key": "YOUR_SECRET_KEY",
    },
    region="ap-beijing",
    group_id="group_A",
    voice_format=0,  # 0 pcm, 1 wav
    sample_rate=16000,
)

vp = VoiceprintClient(config)

with open("demo_audio.pcm", "rb") as f:
    audio = f.read()

try:
    # enroll returns VoicePrintId (not user_id)
    enroll = vp.register(audio, user_id="ross")
    vid = enroll["voice_print_id"]

    score = vp.verify_1to1(audio, user_id=vid)
    print("Verify score:", score)

    tops = vp.identify_1toN(audio, top_k=3)  # group verify
    print("TopN:", tops)

except VoiceprintError as e:
    print("Voiceprint failed:", e)
finally:
    vp.close()
```

## Error Handling

All errors inherit from `VoiceprintError` and preserve raw vendor context:

* `category` / `subtype` (SDK semantic)
* `raw_code` / `raw_message`
* `http_status`
* `request_id`
* `raw_response` (debug)

Upper-layer applications can catch only `VoiceprintError`.

## Project Status

* Failure contract v2.0: ✅ implemented (union, not intersection)
* Xunfei engine: ✅ full coverage of documented APIs
* Tencent engine: ✅ aligned with ASR VoicePrint APIs
* Python: ✅ 3.8+

