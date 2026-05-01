import os
import uuid
import edge_tts
from app.config import AUDIO_DIR

async def generate_audio_file(text: str, language: str, voice: str = None) -> tuple[str, str]:
    """
    Sinh file audio từ text sử dụng edge-tts.
    Hỗ trợ thay đổi giọng đọc và ngôn ngữ.
    Trả về một tuple gồm: (filename, filepath).
    """
    if not voice:
        # Gán giọng đọc mặc định theo ngôn ngữ nếu không truyền
        if language == "vi":
            voice = "vi-VN-HoaiMyNeural" # Giọng nữ tiếng Việt mặc định
        elif language == "en":
            voice = "en-US-AriaNeural" # Giọng nữ tiếng Anh mặc định
        else:
            voice = "en-US-AriaNeural"

    # Tạo tên file ngẫu nhiên để không bị trùng lặp
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    
    # Tạo âm thanh bằng edge-tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)
    
    return filename, filepath
