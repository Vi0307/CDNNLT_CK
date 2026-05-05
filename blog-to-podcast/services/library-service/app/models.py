from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    original_url = Column(String)
    audio_url = Column(String)
    summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
