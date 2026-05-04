from pydantic import BaseModel
from typing import Optional, Dict, Any

class AIRequest(BaseModel):
    prompt: str
    system_instruction: Optional[str] = None
    provider: Optional[str] = None # Allow overriding provider per request

class AIResponse(BaseModel):
    content: str
    provider: str
    model: str
    status: str = "success"
