from pydantic import BaseModel
from typing import List, Optional


class ArticleItem(BaseModel):
    title: str
    url: str
    source: str
    publish_date: Optional[str] = ""
    summary: Optional[str] = ""


class NewsSearchRequest(BaseModel):
    topic: str
    keywords: Optional[List[str]] = None
    limit: int = 5


class NewsSearchResponse(BaseModel):
    status: str
    topic: str
    data: List[ArticleItem]
