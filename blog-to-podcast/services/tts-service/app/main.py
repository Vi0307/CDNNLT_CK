from fastapi import FastAPI, HTTPException
import webbrowser
import threading
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.config import AUDIO_DIR
from app.schemas import TTSRequest, TTSResponse
from app.service import generate_audio_file

app = FastAPI(
    title="Audio Service (TTS)",
    description="Microservice API để chuyển đổi văn bản (text) sang âm thanh (mp3)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bỏ phần tự động mở trình duyệt vì gây lỗi trong Docker

@app.post("/tts", response_model=TTSResponse)
async def create_tts(request: TTSRequest):
    """
    API chuyển đổi đoạn text thành file âm thanh mp3 (nhận JSON).
    """
    try:
        # Nếu không có text, báo lỗi
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Nội dung văn bản (text) không được để trống")

        # Gọi service để sinh file audio
        filename, _ = await generate_audio_file(text=request.text, language=request.language, voice=request.voice)
        
        return TTSResponse(
            status="success",
            audio_url=f"/download/{filename}",
            message="Tạo file âm thanh thành công"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý TTS: {str(e)}")

from fastapi import Form
from typing import Annotated, Optional

@app.post("/tts/form", response_model=TTSResponse)
async def create_tts_form(
    text: Annotated[str, Form(description="Dán nội dung văn bản vào đây, chấp nhận mọi ký tự lạ")],
    language: Annotated[str, Form()] = "vi",
    voice: Annotated[Optional[str], Form()] = None
):
    """
    API chuyển đổi văn bản thành âm thanh (nhận Form-data). 
    Dùng cái này khi bạn muốn dán cả bài báo dài có dấu ngoặc kép, xuống dòng...
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Nội dung văn bản không được để trống")

        filename, _ = await generate_audio_file(text=text, language=language, voice=voice)
        
        return TTSResponse(
            status="success",
            audio_url=f"/download/{filename}",
            message="Tạo file âm thanh thành công (Form)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý TTS: {str(e)}")

@app.get("/download/{filename}")
async def download_audio(filename: str):
    """
    API dùng để lấy nội dung file mp3 đã được tạo.
    """
    filepath = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(path=filepath, media_type="audio/mpeg", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy file âm thanh này")

@app.get("/")
async def root():
    return {"message": "TTS Service is running"}
