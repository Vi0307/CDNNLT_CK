from pydantic import BaseModel
from typing import Optional

class TTSRequest(BaseModel):
    text: str
    language: str = "vi" # Mặc định là tiếng Việt
    voice: Optional[str] = "vi-VN-HoaiMyNeural" # Mặc định là giọng nữ tiếng Việt
    
class TTSResponse(BaseModel):
    status: str
    audio_url: str
    message: str
