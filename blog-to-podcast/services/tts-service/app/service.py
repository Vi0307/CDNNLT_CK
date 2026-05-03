import os
import uuid
import asyncio
import edge_tts
from app.config import settings

AUDIO_DIR = "audio_output"

async def generate_tts(text: str, language: str):
    """
    Sử dụng Edge-TTS để chuyển văn bản thành giọng nói thật.
    """
    if settings.use_mock:
        return generate_mock_tts()

    # Chọn giọng đọc dựa trên ngôn ngữ
    voice = "vi-VN-HoaiMyNeural" if language.lower() == "vietnamese" else "en-US-GuyNeural"
    
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    try:
        communicate = edge_tts.Communicate(text, voice)
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
        with open(filepath, 'wb') as f:
            f.write(b'\x00' * 100) # Tạo file mp3 giả
    return filename, filepath
