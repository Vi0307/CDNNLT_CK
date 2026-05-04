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
    if not settings.gemini_api_key:
        logger.error("GEMINI_API_KEY is not set.")
        return process_text_mock(request)

    try:
        system_instruction = f"Bạn là một biên tập viên chuyên nghiệp. Ngôn ngữ: {request.language}. Trả về định dạng JSON BẮT BUỘC có 2 trường: 'summary' (kiểu string) và 'script' (kiểu string chứa toàn bộ kịch bản, KHÔNG ĐƯỢC LÀ ARRAY HAY OBJECT)."
        
        prompt = f"""
        HÃY XỬ LÝ NỘI DUNG SAU:
        {request.text[:15000]}
        
        YÊU CẦU:
        1. 'summary': Tóm tắt ngắn gọn.
        2. 'script': Kịch bản podcast lôi cuốn (viết thành 1 chuỗi string duy nhất).
        
        LƯU Ý: Chỉ trả về JSON, không kèm giải thích.
        """
        
        logger.info(f"Sending request to Gemini API ({settings.gemini_model})")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": system_instruction + "\n\n" + prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
            }
        }

        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        gemini_data = response.json()
        
        content = gemini_data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
        
        # Parse content as JSON
        try:
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
        
        script_val = data.get("script", "")
        if not isinstance(script_val, str):
            if isinstance(script_val, list):
                script_val = "\n".join([x.get("content", str(x)) if isinstance(x, dict) else str(x) for x in script_val])
            else:
                script_val = str(script_val)
                
        summary_val = data.get("summary", "")
        if not isinstance(summary_val, str):
            summary_val = str(summary_val)
        
        return ProcessResponse(
            request_id=request.request_id,
            summary=summary_val,
            script=script_val,
            status="done",
            language=request.language,
            source="gemini",
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
