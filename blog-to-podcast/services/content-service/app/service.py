import json
import random
import re
import ssl
from typing import Optional, Tuple

import requests
import trafilatura
import urllib3
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

from app.config import settings
from app.schemas import CrawlResponse


class _LegacySSLAdapter(HTTPAdapter):
    """Adapter cho phép kết nối tới các site dùng SSL legacy renegotiation."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def _get(url: str) -> requests.Response:
    """Gửi GET request, tự fallback sang legacy SSL nếu cần."""
    session = requests.Session()
    try:
        resp = session.get(url, timeout=20, headers=_HEADERS, allow_redirects=True)
        resp.raise_for_status()
        return resp
    except Exception as e:
        if "SSL" in str(e) or "ssl" in str(e).lower():
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            session2 = requests.Session()
            session2.mount("https://", _LegacySSLAdapter())
            resp2 = session2.get(url, timeout=20, headers=_HEADERS, allow_redirects=True, verify=False)
            resp2.raise_for_status()
            return resp2
        raise

_MOCK_ARTICLES = [
    {"title": "Mẫu bài viết về Microservices", "text": "Nội dung giả lập về kiến trúc microservices..."},
    {"title": "Mẫu bài viết về AI", "text": "Nội dung giả lập về trí tuệ nhân tạo..."},
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}


def _walk_json_ld(obj) -> Tuple[str, str]:
    """Lấy headline + articleBody / description từ cây JSON-LD."""
    title, body = "", ""
    if isinstance(obj, dict):
        types = obj.get("@type")
        type_list = types if isinstance(types, list) else ([types] if types else [])
        type_names = {str(t).lower() for t in type_list if t}
        interesting = bool(
            type_names & {"newsarticle", "article", "webpage", "blogposting", "reportagearticle"}
        ) or ("articleBody" in obj or "headline" in obj)
        if interesting:
            t = obj.get("headline") or obj.get("name") or ""
            b = obj.get("articleBody") or obj.get("description") or ""
            if isinstance(t, str) and len(t) > len(title):
                title = t.strip()
            if isinstance(b, str) and len(b) > len(body):
                body = b.strip()
        for v in obj.values():
            st, sb = _walk_json_ld(v)
            if len(st) > len(title):
                title = st
            if len(sb) > len(body):
                body = sb
    elif isinstance(obj, list):
        for item in obj:
            st, sb = _walk_json_ld(item)
            if len(st) > len(title):
                title = st
            if len(sb) > len(body):
                body = sb
    return title, body


def _extract_json_ld(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    best_title, best_body = "", ""
    for script in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        t, b = _walk_json_ld(data)
        if len(t) > len(best_title):
            best_title = t
        if len(b) > len(best_body):
            best_body = b
    return best_title, best_body


def _meta_og(soup: BeautifulSoup) -> Tuple[str, str]:
    def get_meta(*, prop: Optional[str] = None, name: Optional[str] = None) -> str:
        tag = None
        if prop:
            tag = soup.find("meta", property=prop)
        if not tag and name:
            tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
        return ""

    return (
        get_meta(prop="og:title") or get_meta(name="twitter:title"),
        get_meta(prop="og:description")
        or get_meta(name="description")
        or get_meta(name="twitter:description"),
    )


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _legacy_paragraphs(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    tags_to_remove = [
        "script", "style", "nav", "footer", "header", "aside", "iframe",
        "noscript", "form", "button",
    ]
    for tag in tags_to_remove:
        for element in soup.find_all(tag):
            element.decompose()
    for sel in [".ads", ".sidebar", ".menu", ".related", ".box-category", ".list-news"]:
        for element in soup.select(sel):
            element.decompose()

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = _clean_text(h1.get_text())
    elif soup.title and soup.title.string:
        title = _clean_text(soup.title.string)

    def _div_content_class(cls) -> bool:
        if not cls:
            return False
        parts = cls if isinstance(cls, list) else [cls]
        s = " ".join(str(p).lower() for p in parts)
        return any(k in s for k in ["article", "content", "post-body", "entry-content"])

    main_content = soup.find("article") or soup.find("main") or soup.find("div", class_=_div_content_class)
    if not main_content:
        main_content = soup.body if soup.body else soup

    parts = []
    for tag in main_content.find_all(["p", "h2", "h3"]):
        txt = _clean_text(tag.get_text(" "))
        if len(txt) > 25:
            parts.append(txt)
    text = "\n\n".join(parts)
    if not text:
        text = "\n\n".join(
            _clean_text(p.get_text(" ")) for p in soup.find_all("p") if len(_clean_text(p.get_text(" "))) > 15
        )
    return title, text


def _extract_vnexpress(html: str, soup: BeautifulSoup) -> Tuple[str, str]:
    """Bóc tách riêng VnExpress để tránh lấy nhầm bài liên quan trong HTML."""
    title_tag = soup.select_one("h1.title-detail") or soup.select_one("h1")
    title = _clean_text(title_tag.get_text(" ")) if title_tag else ""

    description_tag = soup.select_one("p.description")
    parts = []
    if description_tag:
        description = _clean_text(description_tag.get_text(" "))
        if len(description) > 25:
            parts.append(description)

    article = soup.select_one("article.fck_detail") or soup.select_one("article")
    if article:
        for unwanted in article.select(
            ".Normal[style*='display:none'], .box_embed_video_parent, .box_quangcao, "
            ".related_news, .list-news, .box-category, table.tplCaption"
        ):
            unwanted.decompose()
        for paragraph in article.select("p.Normal, p"):
            text = _clean_text(paragraph.get_text(" "))
            if len(text) > 25 and text not in parts:
                parts.append(text)

    return title, "\n\n".join(parts)


def _pick_best_body(url: str, html: str, soup: BeautifulSoup) -> str:
    """Ưu tiên extractor theo domain, rồi JSON-LD/legacy, cuối cùng mới trafilatura."""
    if "vnexpress.net" in url.lower():
        _, vnexpress_body = _extract_vnexpress(html, soup)
        if vnexpress_body and len(vnexpress_body.strip()) >= 80:
            return vnexpress_body.strip()

    _, body_ld = _extract_json_ld(html)
    if body_ld and len(body_ld.strip()) >= 80:
        return body_ld.strip()

    _, legacy_text = _legacy_paragraphs(html)
    if legacy_text and len(legacy_text.strip()) >= 80:
        return legacy_text.strip()

    try:
        traf = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
    except Exception:
        traf = None
    if traf and len(traf.strip()) >= 80:
        return traf.strip()

    _, og_desc = _meta_og(soup)
    if og_desc and len(og_desc.strip()) >= 30:
        return og_desc.strip()

    if body_ld:
        return body_ld.strip()
    if legacy_text:
        return legacy_text.strip()
    return traf.strip() if traf else ""


def _pick_title(url: str, html: str, soup: BeautifulSoup, body_fallback: str) -> str:
    if "vnexpress.net" in url.lower():
        vnexpress_title, _ = _extract_vnexpress(html, soup)
        if vnexpress_title and len(vnexpress_title) > 2:
            return vnexpress_title[:500]

    title_ld, _ = _extract_json_ld(html)
    og_title, _ = _meta_og(soup)
    h1 = soup.find("h1")
    h1t = _clean_text(h1.get_text(" ")) if h1 else ""

    for cand in (h1t, title_ld, og_title):
        if cand and len(cand) > 2 and cand.lower() not in ("msn", "home", "news"):
            return cand[:500]
    if soup.title and soup.title.string:
        t = _clean_text(soup.title.string)
        if t and t.lower() not in ("msn",):
            return t[:500]
    first_line = body_fallback.split("\n", 1)[0].strip() if body_fallback else ""
    return (first_line[:200] or "Không tìm thấy tiêu đề")


def crawl_url(url: str) -> CrawlResponse:
    if settings.use_mock:
        article = random.choice(_MOCK_ARTICLES)
        return CrawlResponse(
            url=url,
            title=article["title"],
            text=article["text"],
            word_count=len(article["text"].split()),
            is_mock=True,
        )

    try:
        response = _get(url)
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        text = _pick_best_body(url, html, soup)
        title = _pick_title(url, html, soup, text)

        cleaned_text = text.strip() if text else ""
        if len(cleaned_text) < 250:
            # Check for paywall indicators
            paywall_keywords = [
                "đăng ký thành viên vip", "thành viên vip", "tài khoản vip",
                "quét zalo qrcode", "quét zalo qr", "thanh toán bằng",
                "đọc tiếp vui lòng", "nội dung dành cho", "đăng nhập để đọc",
                "chỉ dành cho thành viên", "vip member", "gói thuê bao", "báo vip"
            ]
            soup_text_lower = soup.get_text().lower()
            is_paywall = any(kw in soup_text_lower for kw in paywall_keywords)
            
            if is_paywall:
                raise ValueError("Đây là bài viết thu phí (VIP) hoặc yêu cầu đăng nhập để đọc tiếp. Vui lòng sử dụng URL bài viết công khai và đầy đủ.")
            else:
                raise ValueError("Nội dung trích xuất quá ngắn (dưới 250 ký tự). Hãy thử một URL bài báo khác đầy đủ và công khai hơn.")

        return CrawlResponse(
            url=url,
            title=title or "Không tìm thấy tiêu đề",
            text=cleaned_text,
            word_count=len(cleaned_text.split()),
            is_mock=False,
        )
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail=f"Không thể bóc tách nội dung từ URL này. Chi tiết lỗi: {str(e)}"
        )
