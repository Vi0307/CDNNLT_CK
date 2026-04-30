from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import CrawlRequest, CrawlResponse
from service import crawl_url
from config import settings

app = FastAPI(title="Content Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "content-service", "mock_mode": settings.use_mock}


@app.post("/crawl", response_model=CrawlResponse)
def crawl(request: CrawlRequest):
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL không hợp lệ.")
    return crawl_url(request.url)
