import logging
import json
import requests
from app.schemas import ProcessRequest, ProcessResponse
from app.config import settings

logger = logging.getLogger(__name__)

def process_text(request: ProcessRequest) -> ProcessResponse:
    if settings.use_mock:
        return process_text_mock(request)
    return process_text_with_ai_service(request)

def process_text_with_ai_service(request: ProcessRequest) -> ProcessResponse:
    try:
        system_instruction = f"Bạn là một biên tập viên chuyên nghiệp. Ngôn ngữ: {request.language}. Trả về định dạng JSON với các field: summary (tóm tắt ý chính), script (kịch bản podcast)."
        
        prompt = f"""
        HÃY XỬ LÝ NỘI DUNG SAU:
        {request.text}
        
        YÊU CẦU:
        1. Summary ngắn gọn.
        2. Kịch bản podcast lôi cuốn.
        
        LƯU Ý: Chỉ trả về JSON, không kèm giải thích.
        """
        
        logger.info(f"Sending request to AI Service at {settings.ai_service_url}")
        response = requests.post(
            f"{settings.ai_service_url}/generate",
            json={
                "prompt": prompt,
                "system_instruction": system_instruction
            },
            timeout=120
        )
        response.raise_for_status()
        ai_data = response.json()
        content = ai_data.get("content", "")
        
        # Parse content as JSON - more robustly
        try:
            # Find the first { and the last }
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                data = json.loads(json_str)
            else:
                raise ValueError("Could not find JSON block in AI response")
        except Exception as parse_err:
            logger.error(f"JSON Parse Error: {parse_err}. Content was: {content}")
            raise parse_err
        
        return ProcessResponse(
            request_id=request.request_id,
            summary=data.get("summary", ""),
            script=data.get("script", ""),
            status="done",
            language=request.language,
            source=ai_data.get("provider", "claude"),
        )
    except Exception as e:
        logger.error(f"AI Service Call Error: {e}")
        return process_text_mock(request)

def process_text_mock(request: ProcessRequest) -> ProcessResponse:
    return ProcessResponse(
        request_id=request.request_id,
        summary="[MOCK] Đây là tóm tắt giả lập cho mục đích kiểm thử.",
        script="[MOCK] Xin chào, đây là kịch bản podcast giả lập.",
        status="done",
        language=request.language,
        source="mock",
    )
