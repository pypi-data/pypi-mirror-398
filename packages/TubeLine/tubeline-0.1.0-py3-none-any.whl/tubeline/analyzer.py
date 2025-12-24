from google import genai
from .config import GEMINI_API_KEY, GEMINI_IN, GM_OUT


def _format_time(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def analyze_gemini(dg_json):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Gemini API Key가 설정되지 않았습니다. TubeLine.set()을 호출하세요."
        )

    print("Running AI...")

    utterances = dg_json.get("results", {}).get("utterances", [])
    gemini_input_text = ""

    for u in utterances:
        start = _format_time(u["start"])
        end = _format_time(u["end"])
        transcript = u["transcript"].replace("\n", " ").strip()
        gemini_input_text += f"[{start}~{end}] {transcript}\n"

    with open(GEMINI_IN, "w", encoding="utf-8") as f:
        f.write(gemini_input_text)

    prompt = f"""
아래는 Deepgram이 인식한 유튜브 스트리머 영상의 음성 텍스트이다.
STT에는 오인식이 포함될 수 있으므로 유튜브 영상 스타일을 참고하여 적당히 보정하여 '주제 전환'을 판단하라.

출력 형식을 반드시 다음처럼 지켜라:
<시작시간~끝시간> - 주제설명

※ 절대 다른 문장, 설명, 코멘트, 인사말, 메모, 요약, 구분선, 제목 등을 출력하지 마라.
※ "주제"는 유튜브 영상 흐름 기반으로 의미 단위로 묶어라.
※ 시간이 짧게 여러 개 나올 경우 자연스럽게 합쳐서 하나의 구간으로 표현하라.
※ STT 오류는 자연스럽게 보정하라.
※ 시간:분:초 단위로 환산해라.
※ 내용을 최대한 간단하게 추려라.
※ 최대 장면 갯수는 8개 이다. 이 범위 내에서 장면을 분할해라.

음성 인식 결과:
{gemini_input_text}
"""

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    result_text = response.text

    with open(GM_OUT, "w", encoding="utf-8") as f:
        f.write(result_text)

    print("AI OK:", GM_OUT)
    return result_text
