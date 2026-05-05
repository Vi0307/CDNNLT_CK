from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PodcastBase(BaseModel):
    title: str
    original_url: str
    audio_url: str
    summary: Optional[str] = None

class PodcastCreate(PodcastBase):
    pass

class Podcast(PodcastBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True # For older pydantic versions compatibility
        # Note: from_attributes is for Pydantic V2, orm_mode is for V1.
