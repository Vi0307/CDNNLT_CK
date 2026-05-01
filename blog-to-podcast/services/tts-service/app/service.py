import os
import uuid
from gtts import gTTS
from app.config import AUDIO_DIR

def generate_audio_file(text: str, language: str) -> tuple[str, str]:
    """
    Sinh file audio từ text sử dụng gTTS.
    Trả về một tuple gồm: (filename, filepath).
    """
    # Tạo tên file ngẫu nhiên để không bị trùng lặp
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    
    # Tạo âm thanh bằng gTTS
    tts = gTTS(text=text, lang=language)
    tts.save(filepath)
    
    return filename, filepath
