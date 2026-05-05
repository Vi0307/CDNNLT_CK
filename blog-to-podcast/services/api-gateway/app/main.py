import os
import logging
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Blog2Cast API Gateway",
    description="Gateway điều phối toàn bộ pipeline: Crawl → AI Process → TTS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Internal service URLs (Docker internal network)
CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://content-service:8001")
PROCESS_SERVICE_URL = os.getenv("PROCESS_SERVICE_URL", "http://process-service:8002")
TTS_SERVICE_URL     = os.getenv("TTS_SERVICE_URL",     "http://tts-service:8003")

TTS_SAFE_MAX_CHARS = 4500


# ---------- Schemas ----------

class ConvertRequest(BaseModel):
    url: str
    language: str = "vi"
    voice: Optional[str] = None


class ConvertResponse(BaseModel):
    status: str
    audio_url: str
    message: str
    summary: str
    source: str


# ---------- Health ----------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "api-gateway",
        "upstream": {
            "content": CONTENT_SERVICE_URL,
            "process": PROCESS_SERVICE_URL,
            "tts":     TTS_SERVICE_URL,
        },
    }


# ---------- Main Pipeline ----------

@app.post("/convert", response_model=ConvertResponse)
async def convert(request: ConvertRequest):
    """
    Pipeline đầy đủ: URL → Crawl → AI Script → TTS → audio_url
    Frontend chỉ cần gọi endpoint này duy nhất.
    """
    timeout = httpx.Timeout(120.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:

        # ── STEP 1: Crawl ──────────────────────────────────────────────
        logger.info(f"[CRAWL] Fetching: {request.url}")
        try:
            crawl_res = await client.post(
                f"{CONTENT_SERVICE_URL}/crawl",
                json={"url": request.url},
            )
            crawl_res.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = _extract_detail(e.response)
            raise HTTPException(status_code=502, detail=f"[Crawl] {detail}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"[Crawl] Không kết nối được content-service: {e}")

        crawl_data = crawl_res.json()
        raw_text = crawl_data.get("text", "")
        if not raw_text:
            raise HTTPException(status_code=422, detail="Không thể trích xuất nội dung từ URL này.")

        # ── STEP 2: AI Process ─────────────────────────────────────────
        logger.info(f"[PROCESS] text length={len(raw_text)}, lang={request.language}")
        try:
            process_res = await client.post(
                f"{PROCESS_SERVICE_URL}/process",
                json={"text": raw_text, "language": request.language},
            )
            process_res.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = _extract_detail(e.response)
            raise HTTPException(status_code=502, detail=f"[Process] {detail}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"[Process] Không kết nối được process-service: {e}")

        process_data = process_res.json()
        script = process_data.get("script", "")
        summary = process_data.get("summary", "")
        source = process_data.get("source", "unknown")
        if not script:
            raise HTTPException(status_code=422, detail="AI xử lý thất bại, không có kịch bản.")

        # ── STEP 3: TTS ────────────────────────────────────────────────
        tts_text = _prepare_tts_text(script)
        voice    = _resolve_voice(request.language, request.voice)

        logger.info(f"[TTS] tts_text length={len(tts_text)}, voice={voice}")
        try:
            tts_res = await client.post(
                f"{TTS_SERVICE_URL}/tts",
                json={"text": tts_text, "language": request.language, "voice": voice},
            )
            tts_res.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = _extract_detail(e.response)
            raise HTTPException(status_code=502, detail=f"[TTS] {detail}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"[TTS] Không kết nối được tts-service: {e}")

        tts_data = tts_res.json()
        audio_url = tts_data.get("audio_url", "")
        if not audio_url:
            raise HTTPException(status_code=502, detail="TTS không trả về audio_url.")

        # audio_url dạng /download/<filename> — trả về đường dẫn qua gateway
        return ConvertResponse(
            status="success",
            audio_url=audio_url,
            message="Tạo podcast thành công",
            summary=summary,
            source=source,
        )


# ---------- Audio proxy (forward /download/* về tts-service) ----------

@app.get("/download/{filename}")
async def proxy_download(filename: str):
    """Proxy file audio từ tts-service về browser."""
    from fastapi.responses import StreamingResponse

    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            upstream = await client.get(f"{TTS_SERVICE_URL}/download/{filename}")
            upstream.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="File không tồn tại.")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không lấy được file audio: {e}")

    return StreamingResponse(
        content=iter([upstream.content]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------- Helpers ----------

def _extract_detail(response: httpx.Response) -> str:
    try:
        return response.json().get("detail", response.text)
    except Exception:
        return response.text


def _prepare_tts_text(raw: str) -> str:
    import re
    normalized = re.sub(r"```[\s\S]*?```", " ", raw)
    normalized = re.sub(r"`[^`]*`", " ", normalized)
    normalized = re.sub(r"[*_#>\-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        raise HTTPException(status_code=422, detail="Kịch bản AI rỗng, không thể tổng hợp âm thanh.")
    if len(normalized) > TTS_SAFE_MAX_CHARS:
        normalized = normalized[:TTS_SAFE_MAX_CHARS]
    return normalized


def _resolve_voice(language: str, requested: Optional[str]) -> str:
    vi_voices = {"vi-VN-Neural2-A", "vi-VN-Neural2-D"}
    en_voices = {"en-US-Neural2-F", "en-US-Neural2-J"}
    if language == "vi":
        return requested if requested in vi_voices else "vi-VN-Neural2-A"
    if language == "en":
        return requested if requested in en_voices else "en-US-Neural2-F"
    return requested or "vi-VN-Neural2-A"
