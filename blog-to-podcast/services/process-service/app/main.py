import logging
import os
from typing import Annotated, Optional, Union

import google.generativeai as genai
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import setup_logging
from app.schemas import ProcessRequest, ProcessResponse

setup_logging()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
USE_MOCK = os.getenv("USE_MOCK", "false").strip().lower() == "true"

# gemini-1.5-flash thường 404 trên AI Studio (model đổi đời). Mặc định dùng Flash mới;
# có thể ghi đè: GEMINI_MODEL=gemini-2.0-flash
GEMINI_MODEL = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()


def _should_use_mock() -> bool:
    return USE_MOCK or not GEMINI_API_KEY


def call_gemini(prompt: str) -> str:
    """Gọi Gemini API, trả về nội dung text thuần."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    try:
        text = (response.text or "").strip()
    except Exception as e:
        raise RuntimeError(f"Không đọc được phản hồi từ Gemini: {e}") from e
    if not text:
        raise RuntimeError("Gemini trả về nội dung rỗng")
    return text


def _mock_response(request: ProcessRequest) -> ProcessResponse:
    logger.info("Running in MOCK mode")
    return ProcessResponse(
        request_id=request.request_id,
        summary="Đây là tóm tắt giả lập cho mục đích kiểm thử.",
        script="Xin chào, đây là kịch bản podcast giả lập.",
        status="done",
        language=request.language,
        source="mock",
    )


def _generate_summary(request: ProcessRequest) -> str:
    prompt = f"""Bạn là biên tập viên. Dựa trên văn bản blog dưới đây, hãy viết bản tóm tắt bằng tiếng Việt gồm 5 đến 7 câu, súc tích, giữ đúng các ý chính. Chỉ trả về phần tóm tắt, không thêm tiêu đề hay giải thích.

VĂN BẢN:
{request.text}
"""
    return call_gemini(prompt)


def _generate_script(request: ProcessRequest, summary: str) -> str:
    prompt = f"""Bạn là người dẫn podcast. Hãy viết lại bản tóm tắt sau thành một đoạn kịch bản đọc thuật tiếng Việt, giọng tự nhiên và thân thiện.
Độ dài khoảng 150–250 chữ (ký tự), có lời mở đầu chào người nghe và lời kết gọn gàng. Chỉ trả về nội dung kịch bản, không ghi chú thêm.

TÓM TẮT:
{summary}
"""
    return call_gemini(prompt)


def _process_with_gemini(request: ProcessRequest) -> ProcessResponse:
    summary = _generate_summary(request)
    script = _generate_script(request, summary)
    return ProcessResponse(
        request_id=request.request_id,
        summary=summary,
        script=script,
        status="done",
        language=request.language,
        source="gemini",
    )


# --- Khởi tạo ứng dụng FastAPI ---
app = FastAPI(
    title="Process Service",
    description="Microservice xử lý văn bản Blog thành nội dung Podcast",
    version="1.0.0",
)

# --- CORS Middleware (cho phép mọi origin) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoint: GET /health ---
@app.get("/health", tags=["Health"])
def health_check():
    """Kiểm tra trạng thái hoạt động và cấu hình mock / Gemini (không lộ API key)."""
    use_mock = _should_use_mock()
    env_raw = os.getenv("USE_MOCK")
    hint = "Ổn."
    if use_mock and bool(GEMINI_API_KEY):
        hint = "Đã có GEMINI_API_KEY nhưng USE_MOCK đang bật (env hiện tại: xem use_mock_env). Đặt USE_MOCK=false trong .env rồi docker compose up -d lại."
    elif use_mock and not GEMINI_API_KEY:
        hint = "Thiếu GEMINI_API_KEY hoặc USE_MOCK=true — đang chạy mock."
    return {
        "status": "ok",
        "service": "process-service",
        "mock_mode": use_mock,
        "use_mock_env": env_raw if env_raw is not None else "(unset — compose dùng mặc định)",
        "gemini_model": GEMINI_MODEL,
        "gemini_key_configured": bool(GEMINI_API_KEY),
        "hint": hint,
    }


def _handle_process(request: ProcessRequest) -> Union[ProcessResponse, JSONResponse]:
    if _should_use_mock():
        return _mock_response(request)
    try:
        return _process_with_gemini(request)
    except Exception as e:
        logger.error(
            f"[request_id={request.request_id}] Gemini lỗi: {e}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"error": "AI call failed", "detail": str(e)},
        )


# --- Endpoint: POST /process ---
@app.post("/process", response_model=ProcessResponse, tags=["Process"])
def process_text(request: ProcessRequest):
    """
    Nhận JSON. Chuỗi `text` phải escape dấu `"` và xuống dòng (`\\n`); nếu bài báo dài/khó escape, dùng **POST /process/form**.
    """
    return _handle_process(request)


@app.post("/process/form", response_model=ProcessResponse, tags=["Process"])
def process_text_form(
    text: Annotated[str, Form(description="Dán toàn bộ nội dung bài báo, không cần escape JSON")],
    language: Annotated[str, Form()] = "vi",
    request_id: Annotated[Optional[str], Form()] = None,
):
    """Giống POST /process nhưng gửi form (multipart). Swagger có ô text lớn, tránh lỗi JSON khi dán báo."""
    request = ProcessRequest(text=text, language=language, request_id=request_id)
    return _handle_process(request)
