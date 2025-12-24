TubeLine

TubeLine is a Python library that analyzes YouTube videos by converting audio into text and automatically segmenting the video into topic-based time ranges.

It performs the following pipeline:

1. Download audio from a YouTube video


2. Transcribe speech using Deepgram (STT)


3. Analyze topic transitions using Google Gemini



The final output is a list of time ranges with concise topic descriptions.


---

Features

Automatic YouTube audio download

Korean speech-to-text using Deepgram

Topic segmentation based on video flow

Timestamped topic summaries

Simple and clean Python API



---

Installation

pip install TubeLine


---

Requirements

Python 3.10 or higher

FFmpeg (required by yt-dlp)


Install FFmpeg

macOS

brew install ffmpeg

Ubuntu / Debian

sudo apt install ffmpeg

Windows

Download from: https://ffmpeg.org/download.html

Make sure ffmpeg is available in your system PATH.


---

Usage

Basic Example

import TubeLine

TubeLine.set(
    deepgram_api_key="YOUR_DEEPGRAM_API_KEY",
    gemini_api_key="YOUR_GEMINI_API_KEY"
)

result = TubeLine.run("https://www.youtube.com/watch?v=VIDEO_ID")
print(result)


---

Output Format

The output is plain text in the following format:

<start_time~end_time> - topic description

Example:

00:00:00~00:02:15 - Introduction and stream opening
00:02:15~00:08:40 - Discussion about recent updates
00:08:40~00:15:10 - Main gameplay explanation

Time format: HH:MM:SS

Maximum number of segments: 8

Short consecutive segments may be merged automatically



---

API Reference

TubeLine.set()

Configure API keys at runtime.

TubeLine.set(
    deepgram_api_key: str | None,
    gemini_api_key: str | None
)

TubeLine.run()

Run the full pipeline on a YouTube URL.

TubeLine.run(url: str, quality: str = "low") -> str

quality: "low" (default) or "high"



---

Notes

API keys are not stored permanently and must be set at runtime.

STT output may contain recognition errors; Gemini compensates for these during analysis.

This library does not download or store video files, only audio.



---

License

MIT License
