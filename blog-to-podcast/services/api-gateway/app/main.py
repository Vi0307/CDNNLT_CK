from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="API Gateway", description="Cổng giao tiếp duy nhất cho Blog2Cast")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://content-service:8001")
PROCESS_SERVICE_URL = os.getenv("PROCESS_SERVICE_URL", "http://process-service:8002")
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://tts-service:8003")

class GenerateRequest(BaseModel):
    url: str
    language: str = "vi"
    voice: str = "vi-VN-HoaiMyNeural"

class GenerateResponse(BaseModel):
    status: str
    audio_url: str
    summary: str

@app.post("/api/generate-podcast", response_model=GenerateResponse)
async def generate_podcast(request: GenerateRequest):
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Bước 1: Gọi Content Service
        try:
            content_res = await client.post(f"{CONTENT_SERVICE_URL}/crawl", json={"url": request.url})
            content_res.raise_for_status()
            content_data = content_res.json()
            article_text = content_data.get("text")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi cào dữ liệu bài báo: {str(e)}")

        if not article_text:
            raise HTTPException(status_code=400, detail="Không tìm thấy nội dung bài báo")

        # Bước 2: Gọi Process Service
        try:
            process_res = await client.post(f"{PROCESS_SERVICE_URL}/process", json={"text": article_text, "language": request.language})
            process_res.raise_for_status()
            process_data = process_res.json()
            script_text = process_data.get("script")
            summary_text = process_data.get("summary")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi AI xử lý nội dung: {str(e)}")

        if not script_text:
            raise HTTPException(status_code=500, detail="AI không trả về kịch bản")

        # Bước 3: Gọi TTS Service
        try:
            tts_res = await client.post(f"{TTS_SERVICE_URL}/tts", json={"text": script_text, "language": request.language, "voice": request.voice})
            tts_res.raise_for_status()
            tts_data = tts_res.json()
            audio_url = tts_data.get("audio_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi tạo Audio (TTS): {str(e)}")

        if not audio_url:
            raise HTTPException(status_code=500, detail="TTS service không trả về URL audio")

        return GenerateResponse(
            status="success",
            audio_url=f"/api/download/{audio_url.split('/')[-1]}",
            summary=summary_text
        )

from fastapi.responses import StreamingResponse

@app.get("/api/download/{filename}")
async def download_audio(filename: str):
    # Stream file từ tts-service
    url = f"{TTS_SERVICE_URL}/download/{filename}"
    client = httpx.AsyncClient()
    try:
        # Gửi request GET tới TTS service với stream=True
        req = client.build_request("GET", url)
        r = await client.send(req, stream=True)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="File không tồn tại trên TTS service")
            
        async def stream_generator():
            async for chunk in r.aiter_bytes():
                yield chunk
            await client.aclose()
            
        return StreamingResponse(
            stream_generator(), 
            media_type=r.headers.get("content-type", "audio/mpeg"),
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        await client.aclose()
        raise HTTPException(status_code=500, detail=f"Lỗi khi tải file: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "API Gateway is running"}