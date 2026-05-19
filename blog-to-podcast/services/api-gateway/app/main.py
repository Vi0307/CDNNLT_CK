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
    raw_text: str = ""


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
            "news":    NEWS_SERVICE_URL,
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
        # Retry TTS tối đa 3 lần
        tts_last_error = None
        for tts_attempt in range(3):
            try:
                tts_res = await client.post(
                    f"{TTS_SERVICE_URL}/tts",
                    json={"text": tts_text, "language": request.language, "voice": voice},
                )
                if tts_res.status_code == 200:
                    break
                tts_last_error = _extract_detail(tts_res)
                logger.warning(f"[TTS] Attempt {tts_attempt+1} failed {tts_res.status_code}, retrying...")
                import asyncio; await asyncio.sleep(2)
            except httpx.RequestError as e:
                tts_last_error = str(e)
                import asyncio; await asyncio.sleep(2)
        else:
            raise HTTPException(status_code=502, detail=f"[TTS] Thất bại sau 3 lần thử: {tts_last_error}")
        tts_res.raise_for_status()

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
            raw_text=raw_text,
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
            content_c = _re.sub(r'^```(?:json)?\s*', '', content.strip())
            content_c = _re.sub(r'\s*```$', '', content_c.strip())
            try:
                data = json.loads(content_c)
            except Exception:
                m = _re.search(r'\{[\s\S]*\}', content_c)
                if not m:
                    raise HTTPException(status_code=502, detail="Không parse được JSON từ AI")
                data = json.loads(m.group())
            return data
        except Exception as e:
            logger.warning(f"[EXPLAIN] AI service failed, usando fallback: {e}")
            return {
                "type": "common",
                "original": request.word,
                "meaning": ("Hệ thống AI đang tạm thời gián đoạn "
                            "nên không thể giải nghĩa cụm từ này lúc này. Vui lòng thử lại sau."),
                "example": ""
            }


# ---------- Chat Q&A ----------

class ChatRequest(BaseModel):
    question: str
    context: str
    language: str = "vi"


@app.post("/chat")
async def chat_qa(request: ChatRequest):
    """Trả lời câu hỏi dựa trên nội dung bài viết, có fallback kiến thức AI."""
    import json as _json, re as _re

    GOOGLE_SEARCH_KEY = os.getenv("GOOGLE_SEARCH_KEY", "")
    GOOGLE_SEARCH_CX  = os.getenv("GOOGLE_SEARCH_CX", "")

    # ── TẦNG 2 (tùy chọn): Google Search nếu có API key ──────────────
    web_section = ""
    if GOOGLE_SEARCH_KEY and GOOGLE_SEARCH_CX:
        try:
            search_timeout = httpx.Timeout(8.0, connect=4.0)
            async with httpx.AsyncClient(timeout=search_timeout) as search_client:
                search_res = await search_client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": GOOGLE_SEARCH_KEY,
                        "cx":  GOOGLE_SEARCH_CX,
                        "q":   request.question,
                        "num": 3,
                        "lr":  "lang_vi",
                    },
                )
                if search_res.status_code == 200:
                    items = search_res.json().get("items", [])
                    snippets = [
                        f"- {item.get('title','')}: {item.get('snippet','')}"
                        for item in items if item.get("snippet")
                    ]
                    if snippets:
                        web_section = (
                            "\n\nWEB SEARCH RESULTS (thông tin bổ sung từ web):\n"
                            + "\n".join(snippets)
                            + "\nƯu tiên dùng CONTEXT bài viết. Dùng web results để bổ sung khi context thiếu."
                        )
        except Exception as e:
            logger.warning(f"[CHAT] Google Search failed (ignored): {e}")

    # ── TẦNG 1: Prompt chính ─────────────────────────────────────────
    prompt = f"""Bạn là AI trợ lý phân tích bài báo.

CONTEXT (nội dung bài viết):
{request.context}

QUESTION: {request.question}
{web_section}

Hướng dẫn trả lời:
- Nếu câu hỏi có thể trả lời từ context → trả lời chi tiết, trích dẫn phần liên quan.
- Nếu context KHÔNG có đủ thông tin → ĐỪNG bịa. Thay vào đó:
  1. Trả lời phần nào có trong context (nếu có liên quan một phần).
  2. Nói rõ: "Bài viết không đề cập chi tiết về [X]. Dưới đây là thông tin chung tôi biết về chủ đề này:"
  3. Dùng kiến thức của bạn để bổ sung thông tin liên quan.
- Luôn trả lời bằng tiếng Việt, rõ ràng và hữu ích.
- Cuối câu trả lời thêm 1 dòng: NGUỒN: [Từ bài viết] hoặc [Từ bài viết + kiến thức AI] hoặc [Kiến thức AI]

Chỉ trả về JSON hợp lệ:
{{"answer": "câu trả lời đầy đủ (bao gồm dòng NGUỒN ở cuối)", "source": "đoạn trích nguyên văn từ context nếu có, để trống nếu không có", "confidence": "high | medium | low"}}

Quy tắc confidence:
- high → thông tin rõ ràng trong bài viết
- medium → kết hợp bài viết + kiến thức AI / web
- low → chủ yếu từ kiến thức AI, bài không đề cập"""

    timeout = httpx.Timeout(60.0, connect=10.0)
    ai_url = PROCESS_SERVICE_URL.replace(":8002", ":8004").replace("process-service", "ai-service")
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            res = await client.post(
                f"{ai_url}/generate",
                json={
                    "prompt": prompt,
                    "system_instruction": "Chỉ trả về JSON hợp lệ, không markdown, không giải thích thêm.",
                    "provider": "claude",
                },
            )
            res.raise_for_status()
            content = res.json().get("content", "")
            content_c = _re.sub(r'^```(?:json)?\s*', '', content.strip())
            content_c = _re.sub(r'\s*```$', '', content_c.strip())
            try:
                data = _json.loads(content_c)
            except Exception:
                m = _re.search(r'\{[\s\S]*\}', content_c)
                if not m:
                    raise HTTPException(status_code=502, detail="Không parse được JSON từ AI")
                data = _json.loads(m.group())
            return data
        except Exception as e:
            logger.warning(f"[CHAT] AI service failed, usando fallback: {e}")
            return {
                "answer": ("Xin lỗi, hiện tại dịch vụ AI đang bị gián đoạn hoặc quá tải. "
                           "Vui lòng thử lại sau nhé."),
                "source": "",
                "confidence": "low"
            }


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



# ---------- Realtime Podcast ----------

class RealtimePodcastRequest(BaseModel):
    query: str
    rtype: str
    language: str = "vi"
    voice: Optional[str] = None


@app.post("/realtime-podcast")
async def realtime_podcast(request: RealtimePodcastRequest):
    """Pipeline real-time: Lấy dữ liệu thực → AI script → TTS → Audio"""
    timeout = httpx.Timeout(60.0, connect=10.0)
    ai_url  = PROCESS_SERVICE_URL.replace(":8002", ":8004").replace("process-service", "ai-service")
    import json as _json, re as _re

    async with httpx.AsyncClient(timeout=timeout) as client:
        # STEP 1: Lấy dữ liệu real-time
        try:
            rt_res = await client.post(
                f"{NEWS_SERVICE_URL}/realtime",
                json={"query": request.query, "rtype": request.rtype},
            )
            rt_res.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"[Realtime] {e}")

        rt_data = rt_res.json()
        rt_text = rt_data.get("text", "")
        source  = rt_data.get("source", "")
        if not rt_text:
            raise HTTPException(status_code=422, detail=f"Dữ liệu trống từ {source}")

        # STEP 2: AI tổng hợp script
        type_labels = {"gold":"giá vàng","exchange_rate":"tỷ giá ngoại tệ","fuel":"giá xăng dầu","weather":"thời tiết"}
        label = type_labels.get(request.rtype, request.rtype)
        prompt = f"""Bạn là MC podcast chuyên đọc bản tin tài chính và thời tiết.
Dữ liệu thực tế vừa lấy về:
{rt_text}

Tạo script podcast ngắn gọn (1-2 phút) về {label}.
Yêu cầu: mở đầu chào người nghe, đọc số liệu rõ ràng, thêm nhận xét ngắn, kết thúc tự nhiên.
Chỉ trả về JSON: {{"title": "tiêu đề ngắn", "script": "toàn bộ script"}}"""

        try:
            ai_res = await client.post(
                f"{ai_url}/generate",
                json={"prompt": prompt, "system_instruction": "Chỉ trả về JSON hợp lệ.", "provider": "claude"},
            )
            ai_res.raise_for_status()
            content = ai_res.json().get("content", "")
            content_c = _re.sub(r'^```(?:json)?\s*', '', content.strip())
            content_c = _re.sub(r'\s*```$', '', content_c.strip())
            try:
                ai_data = _json.loads(content_c)
            except Exception:
                m = _re.search(r'\{[\s\S]*\}', content_c)
                ai_data = _json.loads(m.group()) if m else {"title": label, "script": content_c}
        except Exception as e:
            logger.warning(f"[AI] Realtime fallback triggered due to error: {e}")
            ai_data = {
                "title": f"Bản tin {label} (Dữ liệu thô)",
                "script": f"Chào bạn, đây là bản tin nhanh về {label}. Hiện tại hệ thống tổng hợp AI đang bị gián đoạn, nền tảng sẽ tự động đọc thẳng dữ liệu thô. Chúc quý vị một ngày tốt lành nhé. Chi tiết như sau:\n\n{rt_text}"
            }

        title  = ai_data.get("title", f"Bản tin {label}")
        script = ai_data.get("script", "")
        if not script:
            raise HTTPException(status_code=422, detail="AI không tạo được script")

        # STEP 3: TTS
        voice    = _resolve_voice(request.language, request.voice)
        tts_text = _prepare_tts_text(script)
        try:
            tts_res = await client.post(
                f"{TTS_SERVICE_URL}/tts",
                json={"text": tts_text, "language": request.language, "voice": voice},
            )
            tts_res.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"[TTS] {e}")

        audio_url = tts_res.json().get("audio_url", "")
        if not audio_url:
            raise HTTPException(status_code=502, detail="TTS không trả về audio_url")

        return {
            "status": "success", "rtype": request.rtype,
            "title": title, "script": script,
            "raw_data": rt_text, "audio_url": audio_url, "source": source,
        }


# ---------- Parse News Query ----------

class ParseQueryRequest(BaseModel):
    query: str


@app.post("/parse-news-query")
async def parse_news_query(request: ParseQueryRequest):
    """Phân tích ý định tìm kiếm tin tức từ câu nhập tự do."""
    import json as _json, re as _re

    prompt = f"""# Vai trò
Bạn là một trình phân tích ý định tìm kiếm tin tức.
Người dùng nhập một câu hoặc từ khoá bất kỳ bằng tiếng Việt.
Nhiệm vụ của bạn là trích xuất thông tin tìm kiếm có cấu trúc.

# Quy tắc bắt buộc
1. Chỉ trả về JSON, không thêm bất kỳ văn bản nào khác.
2. Không bịa ra thông tin nếu không có trong input.
3. search_keywords phải là mảng tối đa 3 phần tử, ngắn gọn.
4. category chỉ được chọn trong danh sách cho phép.
5. time_range mặc định là "24h" nếu không có chỉ định thời gian.

# Danh sách category cho phép
chinh-tri | giao-duc | cong-nghe | y-te | kinh-te |
the-thao | giai-tri | the-gioi | phap-luat | moi-truong |
bat-dong-san | tai-chinh | xa-hoi | khoa-hoc | other

# Output schema
{{"search_keywords": ["keyword1", "keyword2"], "category": "kinh-te", "time_range": "24h", "language": "vi", "is_valid_news_topic": true, "rejection_reason": null}}

# Giá trị time_range hợp lệ
"1h" | "6h" | "24h" | "3d" | "7d" | "30d"

# Khi nào đặt is_valid_news_topic = false
- Input không liên quan đến tin tức (ví dụ: "xin chào", "1+1=?")
- Input là câu hỏi cá nhân ("tôi bị đau bụng phải làm gì")
- Input là yêu cầu hành động ("viết code cho tôi")
Khi false, điền rejection_reason bằng tiếng Việt để hiển thị cho user.

INPUT: {request.query}"""

    ai_url = PROCESS_SERVICE_URL.replace(":8002", ":8004").replace("process-service", "ai-service")
    timeout = httpx.Timeout(20.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            res = await client.post(
                f"{ai_url}/generate",
                json={"prompt": prompt, "system_instruction": "Chỉ trả về JSON hợp lệ.", "provider": "claude"},
            )
            res.raise_for_status()
            content = res.json().get("content", "")
            content_c = _re.sub(r'^```(?:json)?\s*', '', content.strip())
            content_c = _re.sub(r'\s*```$', '', content_c.strip())
            try:
                data = _json.loads(content_c)
            except Exception:
                m = _re.search(r'\{[\s\S]*?\}', content_c)
                data = _json.loads(m.group()) if m else {
                    "search_keywords": [request.query],
                    "category": "other",
                    "time_range": "24h",
                    "language": "vi",
                    "is_valid_news_topic": True,
                    "rejection_reason": None
                }
            return data
        except Exception as e:
            logger.warning(f"[PARSE] AI unavailable, using fallback: {e}")
            # Fallback nếu AI không khả dụng
            return {
                "search_keywords": [request.query],
                "category": "other",
                "time_range": "24h",
                "language": "vi",
                "is_valid_news_topic": True,
                "rejection_reason": None
            }


# ---------- Generate News Podcast ----------

class NewsPodcastRequest(BaseModel):
    topic: str
    keywords: Optional[list] = None   # từ parse-news-query
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
                json={"topic": request.topic, "limit": request.max_articles, "keywords": request.keywords or []},
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
- Đọc {len(crawled_articles)} bài báo dưới đây
- CHỈ tổng hợp các thông tin liên quan đến chủ đề: "{request.topic}"{f' với từ khóa: {", ".join(request.keywords)}' if request.keywords else ''}
- Bỏ qua hoàn toàn các bài/đoạn không liên quan đến chủ đề trên
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
- Đọc {len(crawled_articles)} bài báo dưới đây
- CHỈ tổng hợp các thông tin liên quan đến chủ đề: "{request.topic}"{f' với từ khóa: {", ".join(request.keywords)}' if request.keywords else ''}
- Bỏ qua hoàn toàn các bài/đoạn không liên quan đến chủ đề trên
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
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"[AI] Sự cố kết nối hoặc AI service lỗi: {e}")

        import json as _json, re as _re
        ai_raw = ai_res.json()
        ai_content = ai_raw.get("content", "")
        logger.info(f"[AI] Full response keys: {list(ai_raw.keys())}, content length={len(ai_content)}, preview={ai_content[:300]}")
        # Bỏ markdown code block nếu có (```json ... ```)
        ai_content_clean = _re.sub(r'^```(?:json)?\s*', '', ai_content.strip())
        ai_content_clean = _re.sub(r'\s*```$', '', ai_content_clean.strip())
        try:
            ai_data = _json.loads(ai_content_clean)
        except Exception:
            m = _re.search(r'\{[\s\S]*\}', ai_content_clean)
            if not m:
                logger.error(f"[AI] Cannot parse JSON. Full content: {ai_content[:500]}")
                # Check for refusal/safety block
                refusal_keywords = [
                    "can't discuss", "cannot discuss", "can't help", "cannot help", "sorry, i",
                    "từ chối", "không thể hỗ trợ", "không thể thảo luận", "an toàn", "nhạy cảm",
                    "I'm Claude", "I am Claude", "Hi there!"
                ]
                if any(kw.lower() in ai_content.lower() for kw in refusal_keywords):
                    raise HTTPException(
                        status_code=502,
                        detail=f"AI từ chối xử lý nội dung nhạy cảm hoặc phản hồi không phù hợp: \"{ai_content[:100]}...\""
                    )
                raise HTTPException(status_code=502, detail="AI không trả về JSON hợp lệ")
            ai_data = _json.loads(m.group())

        title    = ai_data.get("title", f"Podcast: {request.topic}")
        summary  = ai_data.get("summary", "")
        script   = ai_data.get("script", "")
        script_vi = ai_data.get("script_vi", script)

        if not script:
            logger.error(f"[AI] No script in response. Keys: {list(ai_data.keys())}")
            raise HTTPException(status_code=422, detail="AI không tạo được script")

        logger.info(f"[AI] Generated script ({len(script)} chars), calling TTS...")

        # ── STEP 4: TTS ───────────────────────────────────────────────
        voice = _resolve_voice(request.language, request.voice)
        tts_text = _prepare_tts_text(script)

        # Retry TTS tối đa 3 lần (edge-tts không ổn định)
        tts_last_error = None
        for tts_attempt in range(3):
            try:
                tts_res = await client.post(
                    f"{TTS_SERVICE_URL}/tts",
                    json={"text": tts_text, "language": request.language, "voice": voice},
                )
                if tts_res.status_code == 200:
                    break
                tts_last_error = _extract_detail(tts_res)
                logger.warning(f"[TTS] Attempt {tts_attempt+1} failed with {tts_res.status_code}, retrying...")
                import asyncio; await asyncio.sleep(2)
            except httpx.RequestError as e:
                tts_last_error = str(e)
                logger.warning(f"[TTS] Attempt {tts_attempt+1} request error: {e}, retrying...")
                import asyncio; await asyncio.sleep(2)
        else:
            raise HTTPException(status_code=502, detail=f"[TTS] Thất bại sau 3 lần thử: {tts_last_error}")

        tts_res.raise_for_status()

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
    normalized = re.sub(r"<[^>]*>", " ", normalized)
    normalized = re.sub(r"[*_#>\-&+%$@?!|{}[\]]", " ", normalized)
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
