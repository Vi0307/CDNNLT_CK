from pydantic import BaseModel

class TTSRequest(BaseModel):
    text: str
    language: str = "vi" # Mặc định là tiếng Việt
    
class TTSResponse(BaseModel):
    status: str
    audio_url: str
    message: str
