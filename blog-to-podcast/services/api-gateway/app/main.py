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
LIBRARY_SERVICE_URL = os.getenv("LIBRARY_SERVICE_URL", "http://library-service:8005")
NEWS_SERVICE_URL    = os.getenv("NEWS_SERVICE_URL",    "http://news-service:8006")

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
    title: str = ""
    summary: str
    original_script: str = ""
    script: str = ""
    source: str


class LibraryPodcast(BaseModel):
    id: int
    title: str
    original_url: str
    audio_url: str
    summary: Optional[str] = None
    created_at: str


class LibraryPodcastCreate(BaseModel):
    title: str
    original_url: str
    audio_url: str
    summary: Optional[str] = None


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
            "library": LIBRARY_SERVICE_URL,
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
        article_title = crawl_data.get("title", "")
        if not raw_text or len(raw_text.strip()) < 50:
            raise HTTPException(status_code=422, detail="Không thể trích xuất nội dung từ URL này. Hãy thử URL bài báo cụ thể hơn.")

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
        original_script = process_data.get("original_script", "")
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
            title=article_title,
            summary=summary,
            original_script=original_script,
            script=script,
            source=source,
        )


# ---------- Explain Term ----------

class ExplainRequest(BaseModel):
    word: str
    context: str
    language: str = "vi"


@app.post("/explain")
async def explain_term(request: ExplainRequest):
    """Giải thích thuật ngữ hoặc cụm từ dựa trên ngữ cảnh bài viết."""
    prompt = f"""Nhiệm vụ:
Giải thích thuật ngữ hoặc cụm từ dựa trên nội dung bài viết.
BẮT BUỘC:
- Chỉ trả về JSON hợp lệ
- Không text ngoài JSON
FORMAT:
{{"type": "common" | "term","original": "từ gốc","meaning": "giải thích theo ngữ cảnh","example": "ví dụ"}}
QUY TẮC:
- Nếu là từ thông thường: dịch nghĩa ngắn gọn
- Nếu là thuật ngữ: giải thích dễ hiểu, liên quan tới nội dung bài
- Ví dụ phải gần với nội dung bài viết
INPUT:
WORD: {request.word}
CONTEXT: {request.context[:3000]}"""

    timeout = httpx.Timeout(60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            res = await client.post(
                f"{PROCESS_SERVICE_URL.replace(':8002', ':8004').replace('process-service', 'ai-service')}/generate",
                json={"prompt": prompt, "system_instruction": "Chỉ trả về JSON hợp lệ, không markdown, không giải thích thêm.", "provider": "claude"},
            )
            res.raise_for_status()
            content = res.json().get("content", "")
            # Parse JSON từ response
            import json, re as _re
            try:
                data = json.loads(content)
            except Exception:
                m = _re.search(r'\{[\s\S]*\}', content)
                if not m:
                    raise HTTPException(status_code=502, detail="Không parse được JSON từ AI")
                data = json.loads(m.group())
            return data
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không kết nối được AI service: {e}")




# ---------- Chat Q&A ----------

class ChatRequest(BaseModel):
    question: str
    context: str
    language: str = "vi"


@app.post("/chat")
async def chat_qa(request: ChatRequest):
    """Trả lời câu hỏi dựa trên nội dung bài viết."""
    prompt = f"""Bạn là AI trả lời câu hỏi dựa trên nội dung bài viết.
Nhiệm vụ:
- Nhận câu hỏi từ người dùng
- Đọc nội dung bài viết (context)
- Trả lời chính xác dựa trên nội dung
- Trích dẫn đoạn liên quan từ bài
BẮT BUỘC:
- Chỉ trả về JSON hợp lệ
- Không thêm text ngoài JSON
- Không tự bịa thông tin ngoài context
FORMAT:
{{"answer": "câu trả lời","source": "đoạn trích","confidence": "high | medium | low"}}
QUY TẮC:
1. TRẢ LỜI: Ngắn gọn, dễ hiểu, dựa hoàn toàn vào context, không suy đoán ngoài bài
2. SOURCE: Trích nguyên văn 1–2 câu từ context liên quan nhất, không chỉnh sửa
3. CONFIDENCE: high → thông tin rõ ràng | medium → suy luận nhẹ | low → không chắc
4. Nếu không tìm thấy: {{"answer": "Không tìm thấy thông tin trong bài viết","source": "","confidence": "low"}}
5. Trả lời bằng tiếng Việt
INPUT:
QUESTION: {request.question}
CONTEXT:
{request.context[:4000]}"""

    timeout = httpx.Timeout(60.0, connect=10.0)
    ai_url = PROCESS_SERVICE_URL.replace(":8002", ":8004").replace("process-service", "ai-service")
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            res = await client.post(
                f"{ai_url}/generate",
                json={"prompt": prompt, "system_instruction": "Chỉ trả về JSON hợp lệ, không markdown, không giải thích thêm.", "provider": "claude"},
            )
            res.raise_for_status()
            content = res.json().get("content", "")
            import json as _json, re as _re
            try:
                data = _json.loads(content)
            except Exception:
                m = _re.search(r'\{[\s\S]*\}', content)
                if not m:
                    raise HTTPException(status_code=502, detail="Không parse được JSON từ AI")
                data = _json.loads(m.group())
            return data
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không kết nối được AI service: {e}")


# ---------- News Search (proxy to news-service) ----------

class NewsSearchRequest(BaseModel):
    topic: str
    limit: int = 5


@app.post("/news/search")
async def news_search(request: NewsSearchRequest):
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            res = await client.post(f"{NEWS_SERVICE_URL}/news/search", json=request.dict())
            res.raise_for_status()
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không kết nối được news-service: {e}")


# ---------- Generate News Podcast ----------

class NewsPodcastRequest(BaseModel):
    topic: str
    language: str = "vi"
    voice: Optional[str] = None
    max_articles: int = 5


class NewsPodcastResponse(BaseModel):
    status: str
    topic: str
    title: str
    summary: str
    script: str
    script_vi: str = ""
    audio_url: str
    articles: list
    source: str


@app.post("/generate-news-podcast", response_model=NewsPodcastResponse)
async def generate_news_podcast(request: NewsPodcastRequest):
    """
    Full pipeline: Chủ đề → Tìm bài báo → Crawl → AI tổng hợp → TTS → Audio
    """
    timeout = httpx.Timeout(180.0, connect=10.0)
    ai_url = PROCESS_SERVICE_URL.replace(":8002", ":8004").replace("process-service", "ai-service")

    async with httpx.AsyncClient(timeout=timeout) as client:

        # ── STEP 1: Tìm bài báo theo chủ đề ──────────────────────────
        logger.info(f"[NEWS] Searching topic: {request.topic}")
        try:
            news_res = await client.post(
                f"{NEWS_SERVICE_URL}/news/search",
                json={"topic": request.topic, "limit": request.max_articles},
            )
            news_res.raise_for_status()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"[News] Không kết nối được news-service: {e}")

        news_data = news_res.json()
        articles_meta = news_data.get("data", [])
        if not articles_meta:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy bài báo nào về chủ đề '{request.topic}'")

        logger.info(f"[NEWS] Found {len(articles_meta)} articles")

        # ── STEP 2: Crawl nội dung từng bài ──────────────────────────
        crawled_articles = []
        for article in articles_meta:
            try:
                crawl_res = await client.post(
                    f"{CONTENT_SERVICE_URL}/crawl",
                    json={"url": article["url"]},
                )
                if crawl_res.status_code == 200:
                    crawl_data = crawl_res.json()
                    text = crawl_data.get("text", "").strip()
                    if text and len(text) > 100:
                        crawled_articles.append({
                            "title": crawl_data.get("title") or article["title"],
                            "content": text[:3000],
                            "source": article.get("source", ""),
                            "url": article["url"],
                        })
            except Exception as e:
                logger.warning(f"[CRAWL] Skip {article['url']}: {e}")
                continue

        if not crawled_articles:
            raise HTTPException(status_code=422, detail="Không crawl được nội dung bài báo nào")

        logger.info(f"[CRAWL] Crawled {len(crawled_articles)} articles")

        # ── STEP 3: AI tổng hợp nhiều bài ────────────────────────────
        articles_text = "\n\n---\n\n".join(
            f"BÀI {i+1}: {a['title']} (Nguồn: {a['source']})\n{a['content']}"
            for i, a in enumerate(crawled_articles)
        )

        lang_name = {"vi": "tiếng Việt", "en": "tiếng Anh", "fr": "tiếng Pháp", "ja": "tiếng Nhật"}.get(request.language, "tiếng Việt")
        need_translation = request.language != "vi"

        if need_translation:
            prompt = f"""Bạn là AI chuyên tổng hợp tin tức và tạo podcast.
Nhiệm vụ:
- Đọc {len(crawled_articles)} bài báo về chủ đề "{request.topic}"
- Tóm tắt các ý chính, không lặp ý
- Tạo 2 phiên bản script podcast:
  1. script_vi: script bằng tiếng Việt tự nhiên
  2. script: script dịch sang {lang_name}, tự nhiên như người bản ngữ

Yêu cầu script:
- Có lời mở đầu chào người nghe
- Trình bày các tin tức chính theo thứ tự quan trọng
- Văn phong thân thiện, dễ hiểu
- Có kết luận ngắn gọn
- Khoảng 3-5 phút đọc

Chỉ trả về JSON hợp lệ:
{{"title": "tiêu đề ngắn gọn bằng {lang_name}", "summary": "tóm tắt 3-5 câu bằng tiếng Việt", "script_vi": "script tiếng Việt đầy đủ", "script": "script bằng {lang_name} đầy đủ"}}

CÁC BÀI BÁO:
{articles_text[:12000]}"""
        else:
            prompt = f"""Bạn là AI chuyên tổng hợp tin tức và tạo podcast.
Nhiệm vụ:
- Đọc {len(crawled_articles)} bài báo về chủ đề "{request.topic}"
- Tóm tắt các ý chính, không lặp ý
- Tạo script podcast tự nhiên, dễ nghe, khoảng 3-5 phút đọc

Yêu cầu script:
- Có lời mở đầu chào người nghe
- Trình bày các tin tức chính theo thứ tự quan trọng
- Văn phong thân thiện, dễ hiểu
- Có kết luận ngắn gọn

Chỉ trả về JSON hợp lệ:
{{"title": "tiêu đề podcast ngắn gọn", "summary": "tóm tắt 3-5 câu", "script": "toàn bộ script podcast"}}

CÁC BÀI BÁO:
{articles_text[:12000]}"""

        try:
            ai_res = await client.post(
                f"{ai_url}/generate",
                json={
                    "prompt": prompt,
                    "system_instruction": "Chỉ trả về JSON hợp lệ, không markdown, không giải thích thêm.",
                    "provider": "claude",
                },
            )
            ai_res.raise_for_status()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"[AI] Không kết nối được ai-service: {e}")

        import json as _json, re as _re
        ai_content = ai_res.json().get("content", "")
        try:
            ai_data = _json.loads(ai_content)
        except Exception:
            m = _re.search(r'\{[\s\S]*\}', ai_content)
            if not m:
                raise HTTPException(status_code=502, detail="AI không trả về JSON hợp lệ")
            ai_data = _json.loads(m.group())

        title    = ai_data.get("title", f"Podcast: {request.topic}")
        summary  = ai_data.get("summary", "")
        script   = ai_data.get("script", "")
        script_vi = ai_data.get("script_vi", script)  # fallback về script nếu không có bản VI riêng

        if not script:
            raise HTTPException(status_code=422, detail="AI không tạo được script")

        logger.info(f"[AI] Generated script ({len(script)} chars)")

        # ── STEP 4: TTS ───────────────────────────────────────────────
        voice = _resolve_voice(request.language, request.voice)
        tts_text = _prepare_tts_text(script)

        try:
            tts_res = await client.post(
                f"{TTS_SERVICE_URL}/tts",
                json={"text": tts_text, "language": request.language, "voice": voice},
            )
            tts_res.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"[TTS] {_extract_detail(e.response)}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"[TTS] Không kết nối được tts-service: {e}")

        audio_url = tts_res.json().get("audio_url", "")
        if not audio_url:
            raise HTTPException(status_code=502, detail="TTS không trả về audio_url")

        logger.info(f"[TTS] Audio: {audio_url}")

        return NewsPodcastResponse(
            status="success",
            topic=request.topic,
            title=title,
            summary=summary,
            script=script,
            script_vi=script_vi,
            audio_url=audio_url,
            articles=[{"title": a["title"], "url": a["url"], "source": a["source"]} for a in crawled_articles],
            source="claude",
        )


@app.get("/download/{filename}")
async def proxy_download(filename: str):
    """Proxy file audio từ tts-service về browser."""
    from fastapi.responses import Response

    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            upstream = await client.get(f"{TTS_SERVICE_URL}/download/{filename}")
            upstream.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="File không tồn tại.")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không lấy được file audio: {e}")

    return Response(
        content=upstream.content,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(upstream.content)),
            "Accept-Ranges": "bytes"
        },
    )


# ---------- Library Proxy ----------

@app.get("/library", response_model=list[LibraryPodcast])
async def get_library():
    """Lấy danh sách podcast đã lưu."""
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{LIBRARY_SERVICE_URL}/podcasts")
            res.raise_for_status()
            return res.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi Library Service: {e}")


@app.post("/library", response_model=LibraryPodcast)
async def save_to_library(podcast: LibraryPodcastCreate):
    """Lưu podcast vào thư viện."""
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{LIBRARY_SERVICE_URL}/podcasts",
                json=podcast.dict()
            )
            res.raise_for_status()
            return res.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi Library Service: {e}")


@app.delete("/library/{podcast_id}")
async def delete_from_library(podcast_id: int):
    """Xóa podcast khỏi thư viện."""
    async with httpx.AsyncClient() as client:
        try:
            res = await client.delete(f"{LIBRARY_SERVICE_URL}/podcasts/{podcast_id}")
            res.raise_for_status()
            return res.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi Library Service: {e}")


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
    fr_voices = {"fr-FR-Neural2-A", "fr-FR-Neural2-B"}
    ja_voices = {"ja-JP-Neural2-A", "ja-JP-Neural2-B"}
    
    if language == "vi":
        return requested if requested in vi_voices else "vi-VN-Neural2-A"
    if language == "en":
        return requested if requested in en_voices else "en-US-Neural2-F"
    if language == "fr":
        return requested if requested in fr_voices else "fr-FR-Neural2-A"
    if language == "ja":
        return requested if requested in ja_voices else "ja-JP-Neural2-A"
        
    return requested or "vi-VN-Neural2-A"
