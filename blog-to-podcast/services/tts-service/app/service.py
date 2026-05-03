import os
import uuid
from typing import Optional

import edge_tts

from app.config import AUDIO_DIR, settings


def _default_voice(language: str, voice: Optional[str]) -> str:
    if voice:
        return voice
    lang = str(language).lower()
    if lang in ("vi", "vietnamese"):
        return "vi-VN-HoaiMyNeural"
    return "en-US-GuyNeural"


async def generate_audio_file(
    text: str,
    language: str,
    voice: Optional[str] = None,
):
    """Sinh file mp3; mock hoặc Edge-TTS."""
    if settings.use_mock:
        return generate_mock_tts()

    use_voice = _default_voice(language, voice)
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    try:
        communicate = edge_tts.Communicate(text, use_voice)
        await communicate.save(filepath)
        return filename, filepath
    except Exception as e:
        print(f"TTS Error: {e}")
        return generate_mock_tts()


def generate_mock_tts():
    filename = "mock_audio.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if not os.path.exists(filepath):
        with open(filepath, "wb") as f:
            f.write(b"\x00" * 100)
    return filename, filepath
