# TubeLine.py

from . import config

def set(
    deepgram_api_key: str | None = None,
    gemini_api_key: str | None = None,
):
    """
    TubeLine API Key 설정
    """

    if deepgram_api_key:
        config.DG_API_KEY = deepgram_api_key

    if gemini_api_key:
        config.GEMINI_API_KEY = gemini_api_key
