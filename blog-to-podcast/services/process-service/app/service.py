import logging
import json
import os
import google.generativeai as genai
from app.schemas import ProcessRequest, ProcessResponse
from app.config import settings

logger = logging.getLogger(__name__)

def process_text(request: ProcessRequest) -> ProcessResponse:
    if settings.use_mock:
        return process_text_mock(request)
    return process_text_with_gemini(request)

def process_text_with_gemini(request: ProcessRequest) -> ProcessResponse:
    if not settings.gemini_api_key:
        return process_text_mock(request)

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model_name = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        Bạn là một biên tập viên chuyên nghiệp. Hãy xử lý nội dung bài viết dưới đây (Ngôn ngữ: {request.language}):
        
        NỘI DUNG:
        {request.text}
        
        YÊU CẦU:
        1. Viết bản tóm tắt (summary) ngắn gọn các ý chính.
        2. Viết kịch bản podcast (script) tự nhiên, lôi cuốn theo phong cách dẫn chương trình.
        
        TRẢ VỀ ĐỊNH DẠNG JSON:
        {{
          "summary": "...",
          "script": "..."
        }}
        """
        
        response = model.generate_content(prompt)
        # Loại bỏ các ký tự markdown nếu có
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        return ProcessResponse(
            request_id=request.request_id,
            summary=data.get("summary", ""),
            script=data.get("script", ""),
            status="done",
            language=request.language,
            source="gemini",
        )
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return process_text_mock(request)

def process_text_mock(request: ProcessRequest) -> ProcessResponse:
    return ProcessResponse(
        request_id=request.request_id,
        summary="Đây là tóm tắt giả lập cho mục đích kiểm thử.",
        script="Xin chào, đây là kịch bản podcast giả lập.",
        status="done",
        language=request.language,
        source="mock",
    )
