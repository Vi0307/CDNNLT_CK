import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import NewsSearchRequest, NewsSearchResponse
from app.service import search_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="News Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "news-service"}


@app.post("/news/search", response_model=NewsSearchResponse)
def search(request: NewsSearchRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Chủ đề không được để trống")
    articles = search_news(request.topic, limit=request.limit)
    return NewsSearchResponse(status="success", data=articles, topic=request.topic)
