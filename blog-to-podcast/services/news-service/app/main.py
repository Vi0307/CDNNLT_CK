import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import NewsSearchRequest, NewsSearchResponse
from app.service import search_news
from app.realtime import detect_realtime_type, fetch_realtime, format_realtime_text
from pydantic import BaseModel

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
    articles = search_news(request.topic, limit=request.limit, keywords=request.keywords)
    return NewsSearchResponse(status="success", data=articles, topic=request.topic)


class RealtimeRequest(BaseModel):
    query: str
    rtype: str  # gold | exchange_rate | fuel | weather


class RealtimeResponse(BaseModel):
    status: str
    rtype: str
    text: str
    source: str


@app.post("/realtime", response_model=RealtimeResponse)
def get_realtime(request: RealtimeRequest):
    """Lấy dữ liệu real-time: giá vàng, tỷ giá, giá xăng, thời tiết."""
    result = fetch_realtime(request.rtype, request.query)
    text   = format_realtime_text(result)
    return RealtimeResponse(
        status="success",
        rtype=request.rtype,
        text=text,
        source=result.get("source", ""),
    )


@app.get("/realtime/detect")
def detect_realtime(query: str):
    """Phát hiện query có phải real-time không."""
    rtype = detect_realtime_type(query)
    return {"rtype": rtype, "is_realtime": rtype is not None}
