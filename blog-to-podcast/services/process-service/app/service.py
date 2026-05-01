import logging
from app.schemas import ProcessRequest, ProcessResponse

logger = logging.getLogger(__name__)

def process_text_mock(request: ProcessRequest) -> ProcessResponse:
    """
    (Hiện tại dùng MOCK DATA — không gọi AI API thật)
    """
    logger.info(
        f"[request_id={request.request_id}] Nhận request — độ dài text: {len(request.text)} ký tự"
    )
    
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
