from pydantic import BaseModel
from typing import Optional

class TTSRequest(BaseModel):
    text: str
    language: str = "vi" # Mặc định là tiếng Việt
    voice: Optional[str] = "vi-VN-Neural2-A" # Mặc định là giọng Neural2-A của Google TTS
    
class TTSResponse(BaseModel):
    status: str
    audio_url: str
    message: str
