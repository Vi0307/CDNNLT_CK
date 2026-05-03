import requests
from bs4 import BeautifulSoup
import random
from app.config import settings
from app.schemas import CrawlResponse

_MOCK_ARTICLES = [
    {"title": "Mẫu bài viết về Microservices", "text": "Nội dung giả lập về kiến trúc microservices..."},
    {"title": "Mẫu bài viết về AI", "text": "Nội dung giả lập về trí tuệ nhân tạo..."}
]

def crawl_url(url: str) -> CrawlResponse:
    if settings.use_mock:
        article = random.choice(_MOCK_ARTICLES)
        return CrawlResponse(url=url, title=article["title"], text=article["text"], word_count=len(article["text"].split()), is_mock=True)

    try:
        # Sử dụng headers để giả lập trình duyệt, tránh bị chặn
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.encoding = 'utf-8' # Đảm bảo đọc đúng tiếng Việt
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Loại bỏ triệt để các thành phần rác
        tags_to_remove = [
            'script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 
            'noscript', 'form', 'button', '.ads', '.sidebar', '.menu', '.related'
        ]
        for tag in tags_to_remove:
            for element in soup.select(tag) if tag.startswith('.') else soup.find_all(tag):
                element.decompose()
            
        # 2. Lấy tiêu đề bài báo
        title = ""
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
        elif soup.title:
            title = soup.title.string.strip()
            
        # 3. Chiến lược tìm nội dung chính (ưu tiên các vùng chứa văn bản lớn)
        # Thử tìm trong các thẻ article hoặc các div có class liên quan đến content
        main_content = (
            soup.find('article') or 
            soup.find('main') or 
            soup.find('div', class_=lambda x: x and any(c in x.lower() for c in ['article', 'content', 'post-body', 'entry-content']))
        )
        
        if not main_content:
            main_content = soup.body if soup.body else soup
            
        # 4. Trích xuất văn bản từ các thẻ p, h2, h3
        paragraphs = main_content.find_all(['p', 'h2', 'h3'])
        
        # Lọc và làm sạch văn bản
        content_parts = []
        for p in paragraphs:
            txt = p.get_text().strip()
            # Chỉ lấy các đoạn văn có độ dài hợp lý (tránh lấy các câu cụt, link lẻ)
            if len(txt) > 50:
                content_parts.append(txt)
                
        final_text = "\n\n".join(content_parts)
        
        if not final_text:
            # Fallback nếu chiến lược trên thất bại: lấy tất cả các thẻ p có text
            final_text = "\n\n".join([p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 30])

        return CrawlResponse(
            url=url,
            title=title or "Không tìm thấy tiêu đề",
            text=final_text,
            word_count=len(final_text.split()),
            is_mock=False
        )
    except Exception as e:
        # Khi có lỗi thật, trả về thông báo lỗi chi tiết thay vì Mock nếu bạn muốn debug
        return CrawlResponse(
            url=url,
            title="Lỗi xử lý URL",
            text=f"Không thể bóc tách nội dung từ URL này. Chi tiết lỗi: {str(e)}",
            word_count=0,
            is_mock=False
        )
    except Exception as e:
        return CrawlResponse(url=url, title="Lỗi Crawl", text=f"Lỗi: {str(e)}", word_count=0, is_mock=False)
