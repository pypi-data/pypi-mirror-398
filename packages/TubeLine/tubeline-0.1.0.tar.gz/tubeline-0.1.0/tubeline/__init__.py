import os

from .TubeLine import set
from .downloader import download_audio
from .stt import deepgram_stt
from .analyzer import analyze_gemini
from .config import AUDIO_FILE

def run(url: str, quality="low"):
    """
    YouTube URL →
    1) 오디오 다운로드
    2) Deepgram STT
    3) Gemini 분석
    """

    try:
        download_audio(url, quality)
        stt_data = deepgram_stt()
        result = analyze_gemini(stt_data)
        return result

    finally:
        if os.path.exists(AUDIO_FILE):
            try:
                os.remove(AUDIO_FILE)
                print(f"[CLEANUP] Deleted {AUDIO_FILE}")
            except Exception as e:
                print(f"[CLEANUP ERROR] {e}")
