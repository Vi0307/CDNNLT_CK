import logging
from typing import List
from app.schemas import ArticleItem

logger = logging.getLogger(__name__)

# RSS feeds từ các báo Việt Nam chính thống
RSS_SOURCES = {
    "vnexpress": {
        "name": "VnExpress",
        "feeds": {
            "default":   "https://vnexpress.net/rss/tin-moi-nhat.rss",
            "chính trị": "https://vnexpress.net/rss/thoi-su.rss",
            "thời sự":   "https://vnexpress.net/rss/thoi-su.rss",
            "giáo dục":  "https://vnexpress.net/rss/giao-duc.rss",
            "y tế":      "https://vnexpress.net/rss/suc-khoe.rss",
            "sức khỏe":  "https://vnexpress.net/rss/suc-khoe.rss",
            "công nghệ": "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss",
            "kinh tế":   "https://vnexpress.net/rss/kinh-doanh.rss",
            "thể thao":  "https://vnexpress.net/rss/the-thao.rss",
            "giải trí":  "https://vnexpress.net/rss/giai-tri.rss",
            "pháp luật": "https://vnexpress.net/rss/phap-luat.rss",
            "thế giới":  "https://vnexpress.net/rss/the-gioi.rss",
            "môi trường":"https://vnexpress.net/rss/moi-truong.rss",
        }
    },
    "tuoitre": {
        "name": "Tuổi Trẻ",
        "feeds": {
            "default":   "https://tuoitre.vn/rss/tin-moi-nhat.rss",
            "chính trị": "https://tuoitre.vn/rss/thoi-su.rss",
            "thời sự":   "https://tuoitre.vn/rss/thoi-su.rss",
            "giáo dục":  "https://tuoitre.vn/rss/giao-duc.rss",
            "y tế":      "https://tuoitre.vn/rss/suc-khoe.rss",
            "sức khỏe":  "https://tuoitre.vn/rss/suc-khoe.rss",
            "công nghệ": "https://tuoitre.vn/rss/khoa-hoc.rss",
            "kinh tế":   "https://tuoitre.vn/rss/kinh-doanh.rss",
            "thể thao":  "https://tuoitre.vn/rss/the-thao.rss",
            "giải trí":  "https://tuoitre.vn/rss/giai-tri.rss",
            "thế giới":  "https://tuoitre.vn/rss/the-gioi.rss",
            "pháp luật": "https://tuoitre.vn/rss/phap-luat.rss",
        }
    },
    "thanhnien": {
        "name": "Thanh Niên",
        "feeds": {
            "default":   "https://thanhnien.vn/rss/home.rss",
            "chính trị": "https://thanhnien.vn/rss/thoi-su.rss",
            "thời sự":   "https://thanhnien.vn/rss/thoi-su.rss",
            "giáo dục":  "https://thanhnien.vn/rss/giao-duc.rss",
            "y tế":      "https://thanhnien.vn/rss/suc-khoe.rss",
            "sức khỏe":  "https://thanhnien.vn/rss/suc-khoe.rss",
            "công nghệ": "https://thanhnien.vn/rss/cong-nghe.rss",
            "kinh tế":   "https://thanhnien.vn/rss/kinh-te.rss",
            "thể thao":  "https://thanhnien.vn/rss/the-thao.rss",
            "giải trí":  "https://thanhnien.vn/rss/giai-tri.rss",
            "thế giới":  "https://thanhnien.vn/rss/the-gioi.rss",
            "pháp luật": "https://thanhnien.vn/rss/phap-luat.rss",
        }
    },
    "dantri": {
        "name": "Dân Trí",
        "feeds": {
            "default":   "https://dantri.com.vn/rss/home.rss",
            "chính trị": "https://dantri.com.vn/rss/xa-hoi.rss",
            "thời sự":   "https://dantri.com.vn/rss/xa-hoi.rss",
            "giáo dục":  "https://dantri.com.vn/rss/giao-duc-huong-nghiep.rss",
            "y tế":      "https://dantri.com.vn/rss/suc-khoe.rss",
            "sức khỏe":  "https://dantri.com.vn/rss/suc-khoe.rss",
            "công nghệ": "https://dantri.com.vn/rss/khoa-hoc-cong-nghe.rss",
            "kinh tế":   "https://dantri.com.vn/rss/kinh-doanh.rss",
            "thể thao":  "https://dantri.com.vn/rss/the-thao.rss",
            "giải trí":  "https://dantri.com.vn/rss/giai-tri.rss",
            "thế giới":  "https://dantri.com.vn/rss/the-gioi.rss",
            "pháp luật": "https://dantri.com.vn/rss/phap-luat.rss",
        }
    },
    "zingnews": {
        "name": "Zing News",
        "feeds": {
            "default":   "https://zingnews.vn/tin-tuc-24h.rss",
            "chính trị": "https://zingnews.vn/xa-hoi.rss",
            "thời sự":   "https://zingnews.vn/xa-hoi.rss",
            "công nghệ": "https://zingnews.vn/cong-nghe.rss",
            "kinh tế":   "https://zingnews.vn/kinh-doanh.rss",
            "thể thao":  "https://zingnews.vn/the-thao.rss",
            "giải trí":  "https://zingnews.vn/giai-tri.rss",
            "thế giới":  "https://zingnews.vn/the-gioi.rss",
        }
    },
    "nhandan": {
        "name": "Nhân Dân",
        "feeds": {
            "default":   "https://nhandan.vn/rss/tin-tuc-su-kien.rss",
            "chính trị": "https://nhandan.vn/rss/chinhtri.rss",
            "thời sự":   "https://nhandan.vn/rss/chinhtri.rss",
            "kinh tế":   "https://nhandan.vn/rss/kinhte.rss",
            "thế giới":  "https://nhandan.vn/rss/thegioi.rss",
        }
    },
}

TOPIC_KEYWORDS = {
    "chính trị": ["chính trị", "thời sự", "chính phủ", "quốc hội", "đảng", "bộ trưởng", "thủ tướng"],
    "giáo dục":  ["giáo dục", "học sinh", "sinh viên", "trường", "đại học", "tuyển sinh", "học phí"],
    "y tế":      ["y tế", "sức khỏe", "bệnh viện", "bác sĩ", "dịch bệnh", "vaccine", "thuốc"],
    "công nghệ": ["công nghệ", "ai", "trí tuệ nhân tạo", "phần mềm", "internet", "robot", "chip"],
    "kinh tế":   ["kinh tế", "tài chính", "chứng khoán", "ngân hàng", "doanh nghiệp", "gdp", "lạm phát"],
    "thể thao":  ["thể thao", "bóng đá", "olympic", "vận động viên", "giải đấu", "huy chương"],
    "giải trí":  ["giải trí", "phim", "âm nhạc", "nghệ sĩ", "ca sĩ", "diễn viên", "concert"],
    "thế giới":  ["thế giới", "quốc tế", "nước ngoài", "mỹ", "trung quốc", "nga", "châu âu"],
    "pháp luật": ["pháp luật", "tòa án", "xét xử", "tội phạm", "cảnh sát", "bắt giữ", "điều tra"],
    "môi trường":["môi trường", "biến đổi khí hậu", "ô nhiễm", "rừng", "biển", "năng lượng tái tạo"],
}


def _normalize_topic(topic: str) -> str:
    t = topic.lower().strip()
    for key in TOPIC_KEYWORDS:
        if t == key or any(kw in t for kw in TOPIC_KEYWORDS[key]):
            return key
    return "default"


def search_news(topic: str, limit: int = 5) -> List[ArticleItem]:
    try:
        import feedparser
    except ImportError:
        logger.error("feedparser not installed")
        return []

    normalized = _normalize_topic(topic)
    articles: List[ArticleItem] = []
    seen_urls = set()
    per_source = max(2, limit // len(RSS_SOURCES) + 1)

    for source_key, source_info in RSS_SOURCES.items():
        feeds = source_info["feeds"]
        feed_url = feeds.get(normalized) or feeds["default"]
        source_name = source_info["name"]
        count_from_source = 0

        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue
                title = entry.get("title", "").strip()
                if not title:
                    continue

                pub_date = getattr(entry, "published", "") or getattr(entry, "updated", "")
                summary = ""
                if hasattr(entry, "summary"):
                    from bs4 import BeautifulSoup
                    summary = BeautifulSoup(entry.summary, "html.parser").get_text()[:200]

                seen_urls.add(url)
                articles.append(ArticleItem(
                    title=title, url=url, source=source_name,
                    publish_date=pub_date, summary=summary,
                ))
                count_from_source += 1

                if count_from_source >= per_source or len(articles) >= limit:
                    break

        except Exception as e:
            logger.warning(f"[{source_name}] RSS error: {e}")
            continue

        if len(articles) >= limit:
            break

    # Fallback: tìm theo keyword trong feed default
    if not articles:
        for source_key, source_info in RSS_SOURCES.items():
            feed_url = source_info["feeds"]["default"]
            source_name = source_info["name"]
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:20]:
                    url = entry.get("link", "")
                    title = entry.get("title", "").strip()
                    if not url or not title or url in seen_urls:
                        continue
                    if topic.lower() in title.lower():
                        seen_urls.add(url)
                        articles.append(ArticleItem(
                            title=title, url=url, source=source_name,
                            publish_date=getattr(entry, "published", ""), summary="",
                        ))
                        if len(articles) >= limit:
                            break
            except Exception:
                continue
            if len(articles) >= limit:
                break

    return articles[:limit]

# RSS feeds từ các báo Việt Nam chính thống
RSS_SOURCES = {
    "vnexpress": {
        "name": "VnExpress",
        "feeds": {
            "default":   "https://vnexpress.net/rss/tin-moi-nhat.rss",
            "chính trị": "https://vnexpress.net/rss/thoi-su.rss",
            "thời sự":   "https://vnexpress.net/rss/thoi-su.rss",
            "giáo dục":  "https://vnexpress.net/rss/giao-duc.rss",
            "y tế":      "https://vnexpress.net/rss/suc-khoe.rss",
            "sức khỏe":  "https://vnexpress.net/rss/suc-khoe.rss",
            "công nghệ": "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss",
            "kinh tế":   "https://vnexpress.net/rss/kinh-doanh.rss",
            "thể thao":  "https://vnexpress.net/rss/the-thao.rss",
            "giải trí":  "https://vnexpress.net/rss/giai-tri.rss",
            "pháp luật": "https://vnexpress.net/rss/phap-luat.rss",
            "thế giới":  "https://vnexpress.net/rss/the-gioi.rss",
            "môi trường":"https://vnexpress.net/rss/moi-truong.rss",
        }
    },
    "tuoitre": {
        "name": "Tuổi Trẻ",
        "feeds": {
            "default":   "https://tuoitre.vn/rss/tin-moi-nhat.rss",
            "chính trị": "https://tuoitre.vn/rss/thoi-su.rss",
            "thời sự":   "https://tuoitre.vn/rss/thoi-su.rss",
            "giáo dục":  "https://tuoitre.vn/rss/giao-duc.rss",
            "y tế":      "https://tuoitre.vn/rss/suc-khoe.rss",
            "sức khỏe":  "https://tuoitre.vn/rss/suc-khoe.rss",
            "công nghệ": "https://tuoitre.vn/rss/khoa-hoc.rss",
            "kinh tế":   "https://tuoitre.vn/rss/kinh-doanh.rss",
            "thể thao":  "https://tuoitre.vn/rss/the-thao.rss",
            "giải trí":  "https://tuoitre.vn/rss/giai-tri.rss",
            "thế giới":  "https://tuoitre.vn/rss/the-gioi.rss",
            "pháp luật": "https://tuoitre.vn/rss/phap-luat.rss",
        }
    },
    "thanhnien": {
        "name": "Thanh Niên",
        "feeds": {
            "default":   "https://thanhnien.vn/rss/home.rss",
            "chính trị": "https://thanhnien.vn/rss/thoi-su.rss",
            "thời sự":   "https://thanhnien.vn/rss/thoi-su.rss",
            "giáo dục":  "https://thanhnien.vn/rss/giao-duc.rss",
            "y tế":      "https://thanhnien.vn/rss/suc-khoe.rss",
            "sức khỏe":  "https://thanhnien.vn/rss/suc-khoe.rss",
            "công nghệ": "https://thanhnien.vn/rss/cong-nghe.rss",
            "kinh tế":   "https://thanhnien.vn/rss/kinh-te.rss",
            "thể thao":  "https://thanhnien.vn/rss/the-thao.rss",
            "giải trí":  "https://thanhnien.vn/rss/giai-tri.rss",
            "thế giới":  "https://thanhnien.vn/rss/the-gioi.rss",
            "pháp luật": "https://thanhnien.vn/rss/phap-luat.rss",
        }
    },
    "dantri": {
        "name": "Dân Trí",
        "feeds": {
            "default":   "https://dantri.com.vn/rss/home.rss",
            "chính trị": "https://dantri.com.vn/rss/xa-hoi.rss",
            "thời sự":   "https://dantri.com.vn/rss/xa-hoi.rss",
            "giáo dục":  "https://dantri.com.vn/rss/giao-duc-huong-nghiep.rss",
            "y tế":      "https://dantri.com.vn/rss/suc-khoe.rss",
            "sức khỏe":  "https://dantri.com.vn/rss/suc-khoe.rss",
            "công nghệ": "https://dantri.com.vn/rss/khoa-hoc-cong-nghe.rss",
            "kinh tế":   "https://dantri.com.vn/rss/kinh-doanh.rss",
            "thể thao":  "https://dantri.com.vn/rss/the-thao.rss",
            "giải trí":  "https://dantri.com.vn/rss/giai-tri.rss",
            "thế giới":  "https://dantri.com.vn/rss/the-gioi.rss",
            "pháp luật": "https://dantri.com.vn/rss/phap-luat.rss",
        }
    },
    "zingnews": {
        "name": "Zing News",
        "feeds": {
            "default":   "https://zingnews.vn/tin-tuc-24h.rss",
            "chính trị": "https://zingnews.vn/xa-hoi.rss",
            "thời sự":   "https://zingnews.vn/xa-hoi.rss",
            "công nghệ": "https://zingnews.vn/cong-nghe.rss",
            "kinh tế":   "https://zingnews.vn/kinh-doanh.rss",
            "thể thao":  "https://zingnews.vn/the-thao.rss",
            "giải trí":  "https://zingnews.vn/giai-tri.rss",
            "thế giới":  "https://zingnews.vn/the-gioi.rss",
        }
    },
    "nhandan": {
        "name": "Nhân Dân",
        "feeds": {
            "default":   "https://nhandan.vn/rss/tin-tuc-su-kien.rss",
            "chính trị": "https://nhandan.vn/rss/chinhtri.rss",
            "thời sự":   "https://nhandan.vn/rss/chinhtri.rss",
            "kinh tế":   "https://nhandan.vn/rss/kinhte.rss",
            "thế giới":  "https://nhandan.vn/rss/thegioi.rss",
        }
    },
}

TOPIC_KEYWORDS = {
    "chính trị": ["chính trị", "thời sự", "chính phủ", "quốc hội", "đảng", "bộ trưởng", "thủ tướng"],
    "giáo dục":  ["giáo dục", "học sinh", "sinh viên", "trường", "đại học", "tuyển sinh", "học phí"],
    "y tế":      ["y tế", "sức khỏe", "bệnh viện", "bác sĩ", "dịch bệnh", "vaccine", "thuốc"],
    "công nghệ": ["công nghệ", "ai", "trí tuệ nhân tạo", "phần mềm", "internet", "robot", "chip"],
    "kinh tế":   ["kinh tế", "tài chính", "chứng khoán", "ngân hàng", "doanh nghiệp", "gdp", "lạm phát"],
    "thể thao":  ["thể thao", "bóng đá", "olympic", "vận động viên", "giải đấu", "huy chương"],
    "giải trí":  ["giải trí", "phim", "âm nhạc", "nghệ sĩ", "ca sĩ", "diễn viên", "concert"],
    "thế giới":  ["thế giới", "quốc tế", "nước ngoài", "mỹ", "trung quốc", "nga", "châu âu"],
    "pháp luật": ["pháp luật", "tòa án", "xét xử", "tội phạm", "cảnh sát", "bắt giữ", "điều tra"],
    "môi trường":["môi trường", "biến đổi khí hậu", "ô nhiễm", "rừng", "biển", "năng lượng tái tạo"],
}


def _normalize_topic(topic: str) -> str:
    t = topic.lower().strip()
    for key in TOPIC_KEYWORDS:
        if t == key or any(kw in t for kw in TOPIC_KEYWORDS[key]):
            return key
    return "default"


def search_news(topic: str, limit: int = 5) -> List[ArticleItem]:
    try:
        import feedparser
    except ImportError:
        logger.error("feedparser not installed")
        return []

    normalized = _normalize_topic(topic)
    articles: List[ArticleItem] = []
    seen_urls = set()
    per_source = max(2, limit // len(RSS_SOURCES) + 1)

    for source_key, source_info in RSS_SOURCES.items():
        feeds = source_info["feeds"]
        feed_url = feeds.get(normalized) or feeds["default"]
        source_name = source_info["name"]
        count_from_source = 0

        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue
                title = entry.get("title", "").strip()
                if not title:
                    continue

                pub_date = getattr(entry, "published", "") or getattr(entry, "updated", "")
                summary = ""
                if hasattr(entry, "summary"):
                    from bs4 import BeautifulSoup
                    summary = BeautifulSoup(entry.summary, "html.parser").get_text()[:200]

                seen_urls.add(url)
                articles.append(ArticleItem(
                    title=title, url=url, source=source_name,
                    publish_date=pub_date, summary=summary,
                ))
                count_from_source += 1

                if count_from_source >= per_source or len(articles) >= limit:
                    break

        except Exception as e:
            logger.warning(f"[{source_name}] RSS error: {e}")
            continue

        if len(articles) >= limit:
            break

    # Fallback: tìm theo keyword trong feed default
    if not articles:
        for source_key, source_info in RSS_SOURCES.items():
            feed_url = source_info["feeds"]["default"]
            source_name = source_info["name"]
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:20]:
                    url = entry.get("link", "")
                    title = entry.get("title", "").strip()
                    if not url or not title or url in seen_urls:
                        continue
                    if topic.lower() in title.lower():
                        seen_urls.add(url)
                        articles.append(ArticleItem(
                            title=title, url=url, source=source_name,
                            publish_date=getattr(entry, "published", ""), summary="",
                        ))
                        if len(articles) >= limit:
                            break
            except Exception:
                continue
            if len(articles) >= limit:
                break

    return articles[:limit]
