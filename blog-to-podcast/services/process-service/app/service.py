import json
import logging
from typing import Any

import requests
from fastapi import HTTPException

from app.config import settings
from app.schemas import ProcessRequest, ProcessResponse

logger = logging.getLogger(__name__)


def process_text(request: ProcessRequest) -> ProcessResponse:
    if settings.use_mock:
        return process_text_mock(request)
    return process_text_with_ai_service(request)


def process_text_with_ai_service(request: ProcessRequest) -> ProcessResponse:
    try:
        system_instruction = (
            f"Bạn là một biên tập viên podcast chuyên nghiệp. Ngôn ngữ gốc có thể là bất kỳ ngôn ngữ nào. "
            f"Ngôn ngữ đầu ra (chuyển đổi) là: {request.language}. "
            "Chỉ trả về JSON hợp lệ, không markdown, không giải thích thêm. "
            "JSON bắt buộc có đúng 3 trường: "
            "'original_script' là kịch bản podcast bằng ngôn ngữ gốc của bài viết (phải khớp từng câu chữ với script), "
            "'summary' là chuỗi tóm tắt bằng ngôn ngữ đầu ra, "
            "và 'script' là chuỗi kịch bản podcast hoàn chỉnh bằng ngôn ngữ đầu ra."
        )

        prompt = f"""
HÃY XỬ LÝ NỘI DUNG BÀI VIẾT SAU:
{request.text[:15000]}

YÊU CẦU QUAN TRỌNG:
1. script: Viết lại thành kịch bản podcast lôi cuốn, tự nhiên bằng ngôn ngữ đầu ra, phù hợp để đọc thành audio.
2. original_script: Nếu ngôn ngữ gốc của bài viết khác với ngôn ngữ đầu ra, hãy dịch kịch bản podcast ('script') trở lại ngôn ngữ gốc. Nếu giống nhau, hãy sao chép y nguyên 'script'.
3. summary: Tóm tắt nội dung chính bằng ngôn ngữ đầu ra.
4. BẮT BUỘC trả về ĐÚNG VÀ CHỈ 1 OBJECT JSON HỢP LỆ. KHÔNG thêm bất kỳ giải thích, markdown (```), hay văn bản nào khác ngoài JSON.
5. Hãy chắc chắn escape (thoát) đúng các ký tự đặc biệt (như ngoặc kép, dấu xuống dòng) bên trong chuỗi JSON.
6. Cấu trúc JSON chuẩn xác: {{"original_script":"...", "summary":"...","script":"..."}}
""".strip()

        logger.info("Sending request to AI Service (Claude)")
        response = requests.post(
            f"{settings.ai_service_url}/generate",
            json={
                "prompt": prompt,
                "system_instruction": system_instruction,
                "provider": "claude",
            },
            timeout=settings.ai_timeout,
        )
        response.raise_for_status()
        ai_data = response.json()
        content = ai_data.get("content", "")
        data = _parse_ai_json(content)

        script_val = _stringify_ai_field(data.get("script", ""))
        summary_val = _stringify_ai_field(data.get("summary", ""))
        original_script_val = _stringify_ai_field(data.get("original_script", ""))

        if not script_val.strip():
            raise ValueError("Claude response did not contain a usable script")

        return ProcessResponse(
            request_id=request.request_id,
            summary=summary_val,
            original_script=original_script_val,
            script=script_val,
            status="done",
            language=request.language,
            source="claude",
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"AI Service request failed: {e}")
        raise HTTPException(status_code=502, detail=f"Claude AI service request failed: {e}")
    except Exception as e:
        logger.error(f"Claude processing failed: {e}")
        raise HTTPException(status_code=502, detail=f"Claude processing failed: {e}")


def _parse_ai_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError as e2:
                logger.error(f"Failed to parse inner JSON: {e2}. Snippet: {content[start:start+200]}")
                raise ValueError(f"JSON parsing error: {e2}")
        
        logger.error(f"Failed to parse JSON: {e}. Snippet: {content[:200]}")
        raise ValueError("Could not find valid JSON object in Claude response")


def _stringify_ai_field(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(
            item.get("content", str(item)) if isinstance(item, dict) else str(item)
            for item in value
        ).strip()
    if value is None:
        return ""
    return str(value).strip()


def process_text_mock(request: ProcessRequest) -> ProcessResponse:
    return ProcessResponse(
        request_id=request.request_id,
        summary="[MOCK] Đây là tóm tắt giả lập cho mục đích kiểm thử.",
        original_script="[MOCK] Hello, this is a mock podcast script for testing.",
        script="[MOCK] Xin chào, đây là kịch bản podcast giả lập cho mục đích kiểm thử.",
        status="done",
        language=request.language,
        source="mock",
    )
