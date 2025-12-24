import json
import requests
from .config import DG_API_KEY, AUDIO_FILE, DG_OUT

def deepgram_stt():
    if not DG_API_KEY:
        raise RuntimeError(
            "Deepgram API Key가 설정되지 않았습니다. TubeLine.set()을 호출하세요."
        )

    print("STT...")

    with open(AUDIO_FILE, "rb") as f:
        audio_bytes = f.read()

    url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DG_API_KEY}",
        "Content-Type": "audio/m4a",
    }

    params = {
        "model": "nova-2",
        "language": "ko",
        "smart_format": "true",
        "punctuate": "true",
        "diarize": "true",
        "utterances": "true",
        "timestamps": "true",
    }

    response = requests.post(url, headers=headers, params=params, data=audio_bytes)
    response.raise_for_status()

    data = response.json()

    with open(DG_OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("STT OK:", DG_OUT)
    return data
