from pydantic import BaseModel


class CrawlRequest(BaseModel):
    url: str


class CrawlResponse(BaseModel):
    url: str
    title: str
    text: str
    word_count: int
    is_mock: bool = False
