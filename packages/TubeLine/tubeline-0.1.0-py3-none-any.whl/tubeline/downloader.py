import subprocess
from .config import AUDIO_FILE

def download_audio(url: str, quality="low"):
    print("Downloading Audio...")

    fmt = "139" if quality == "low" else "140"
    cmd = ["yt-dlp", "-f", fmt, "-o", AUDIO_FILE, url]

    subprocess.run(cmd, check=True)

    print("Download OK:", AUDIO_FILE)
