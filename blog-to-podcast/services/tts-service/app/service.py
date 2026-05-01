import os
import uuid
try:
    import edge_tts
except ImportError:
    edge_tts = None
from app.config import AUDIO_DIR

async def generate_audio_file(text: str, language: str, voice: str = None) -> tuple[str, str]:
    if not voice:
        if language == "vi":
            voice = "vi-VN-HoaiMyNeural"
        elif language == "en":
            voice = "en-US-AriaNeural"
        else:
            voice = "en-US-AriaNeural"

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    if edge_tts is None:
        # Create a dummy silent/empty mp3 file for mock testing
        with open(filepath, 'wb') as f:
            pass
        return filename, filepath

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)
    return filename, filepath
