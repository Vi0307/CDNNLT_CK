import logging
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, model_validator

# --- Cấu hình logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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


# --- Schema định nghĩa Input / Output ---
SUPPORTED_LANGUAGES = {"vi", "en"}


class ProcessRequest(BaseModel):
    text: str
    request_id: Optional[str] = None
    language: str = "vi"

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        """Bắt buộc 'text' không được rỗng."""
        if not v or not v.strip():
            raise ValueError("text field is required")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Nếu language không hợp lệ → mặc định về 'vi'."""
        return v if v in SUPPORTED_LANGUAGES else "vi"

    @model_validator(mode="after")
    def auto_generate_request_id(self) -> "ProcessRequest":
        """Tự sinh UUID nếu request_id không được cung cấp."""
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
        return self


class ProcessResponse(BaseModel):
    request_id: str
    summary: str
    script: str
    status: str
    language: str


# --- Endpoint: GET /health ---
@app.get("/health", tags=["Health"])
def health_check():
    """Kiểm tra trạng thái hoạt động của service."""
    return {"status": "ok", "service": "process-service"}


# --- Endpoint: POST /process ---
@app.post("/process", response_model=ProcessResponse, tags=["Process"])
def process_text(request: ProcessRequest):
    """
    Nhận văn bản Blog và trả về tóm tắt + kịch bản Podcast.
    (Hiện tại dùng MOCK DATA — không gọi AI API thật)
    """
    # Log thông tin request nhận được
    logger.info(
        f"[request_id={request.request_id}] Nhận request — độ dài text: {len(request.text)} ký tự"
    )

    try:
        # --- MOCK LOGIC ---
        # Lấy 50 ký tự đầu của text (xử lý an toàn nếu text ngắn hơn 50 ký tự)
        preview = request.text[:50].strip()

        summary = f"Đây là tóm tắt mẫu cho bài viết: {preview}"
        script = (
            f"Xin chào các bạn, hôm nay chúng ta cùng tìm hiểu về chủ đề sau đây. "
            f"{summary}"
        )

        logger.info(f"[request_id={request.request_id}] Xử lý hoàn tất — status: done")

        return ProcessResponse(
            request_id=request.request_id,
            summary=summary,
            script=script,
            status="done",
            language=request.language,
        )

    except Exception as e:
        logger.error(f"[request_id={request.request_id}] Lỗi xử lý: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal error", "detail": str(e)},
        )
