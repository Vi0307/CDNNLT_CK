"""
Module lấy dữ liệu real-time: giá vàng, tỷ giá, giá xăng, thời tiết.
"""
import logging
import os
import requests
from bs4 import BeautifulSoup
from typing import Optional

logger = logging.getLogger(__name__)

WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
TIMEOUT = 8


# ── Giá vàng SJC ─────────────────────────────────────────────────────────────

def get_gold_price() -> dict:
    """Lấy giá vàng từ Ngọc Thịnh Jewelry, fallback sang SJC."""

    # ── Nguồn 1: Ngọc Thịnh Jewelry (ngocthinh-jewelry.vn) ────────────────
    try:
        res = requests.get(
            "https://ngocthinh-jewelry.vn/pages/bang-gia-vang",
            timeout=TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "vi-VN,vi;q=0.9",
            },
        )
        res.raise_for_status()
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        container = soup.find(class_="flexbanggiavang")
        if container:
            content = container.find(class_="contenttogoldflex") or container
            rows = []
            # Mỗi row con trực tiếp chứa 3 div: .headerindex1, .headerindex2, .headerindex3
            for row_div in content.find_all("div", recursive=False):
                name_el = row_div.find(class_="headerindex1")
                buy_el  = row_div.find(class_="headerindex2")
                sell_el = row_div.find(class_="headerindex3")
                if name_el and buy_el and sell_el:
                    name = name_el.get_text(strip=True)
                    buy  = buy_el.get_text(strip=True)
                    sell = sell_el.get_text(strip=True)
                    # Bỏ qua hàng tiêu đề
                    if name and name != "Loại vàng" and any(c.isdigit() for c in buy):
                        rows.append({"name": name, "buy": buy, "sell": sell})
            if rows:
                return {"type": "gold", "data": rows[:8], "source": "Ngọc Thịnh Jewelry (ngocthinh-jewelry.vn)"}
    except Exception as e:
        logger.warning(f"[GOLD] Ngoc Thinh error: {e}")

    try:
        res = requests.get(
            "https://sjc.com.vn/xml/tygia.xml",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        res.raise_for_status()
        soup = BeautifulSoup(res.content, "xml")
        rows = []
        for item in soup.find_all("item"):
            name = item.find("name")
            buy  = item.find("muavao") or item.find("buy")
            sell = item.find("bandra") or item.find("sell")
            if name and buy and sell:
                rows.append({
                    "name": name.get_text(strip=True),
                    "buy":  buy.get_text(strip=True),
                    "sell": sell.get_text(strip=True),
                })
        if rows:
            return {"type": "gold", "data": rows[:6], "source": "SJC (sjc.com.vn)"}
    except Exception as e:
        logger.warning(f"[GOLD] SJC XML error: {e}")

    # ── Nguồn 2: SJC trang chủ scrape ─────────────────────────────────────
    try:
        res = requests.get(
            "https://sjc.com.vn/",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        rows = []
        for table in soup.find_all("table"):
            for tr in table.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if len(tds) >= 3:
                    name = tds[0].get_text(strip=True)
                    buy  = tds[1].get_text(strip=True)
                    sell = tds[2].get_text(strip=True)
                    if name and any(c.isdigit() for c in buy):
                        rows.append({"name": name, "buy": buy, "sell": sell})
        if rows:
            return {"type": "gold", "data": rows[:6], "source": "SJC (sjc.com.vn)"}
    except Exception as e:
        logger.warning(f"[GOLD] SJC homepage error: {e}")

    # ── Nguồn 3: metals.live + quy đổi đúng ──────────────────────────────
    try:
        er_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=TIMEOUT)
        er_res.raise_for_status()
        usd_vnd = er_res.json().get("rates", {}).get("VND", 25450)

        gold_res = requests.get(
            "https://api.metals.live/v1/spot/gold",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        gold_res.raise_for_status()
        xau_usd = gold_res.json()[0].get("gold", 0) if gold_res.json() else 0
        if not xau_usd:
            raise ValueError("No gold price")

        # Công thức đúng: 1 oz = 31.1035g, 1 lượng = 37.5g, 1 chỉ = 3.75g
        price_luong = round(xau_usd / 31.1035 * 37.5 * usd_vnd / 1_000_000) * 1_000_000
        price_chi   = round(price_luong / 10 / 100_000) * 100_000  # 1 lượng = 10 chỉ

        note = f"(Giá quốc tế: ${xau_usd:,.0f}/oz | Tỷ giá: {usd_vnd:,.0f} VND/USD)"
        rows = [
            {"name": "Vàng quốc tế 1 lượng (quy đổi)", "buy": f"{price_luong:,.0f}", "sell": f"{int(price_luong*1.005):,.0f}"},
            {"name": "Vàng quốc tế 1 chỉ (quy đổi)",   "buy": f"{price_chi:,.0f}",   "sell": f"{int(price_chi*1.005):,.0f}"},
        ]
        return {"type": "gold", "data": rows, "source": f"Metals.live + ExchangeRate-API {note}"}
    except Exception as e:
        logger.warning(f"[GOLD] metals.live error: {e}")

    return {"type": "gold", "data": [], "source": "N/A", "error": "Không lấy được giá vàng"}



# ── Tỷ giá Vietcombank ────────────────────────────────────────────────────────

def get_exchange_rate() -> dict:
    """Lấy tỷ giá từ Vietcombank JSON API."""
    try:
        res = requests.get(
            "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        currencies = ["USD", "EUR", "JPY", "CNY", "GBP", "AUD", "SGD"]
        rows = []
        for exrate in soup.find_all("exrate"):
            code = exrate.get("currencycode", "")
            if code.upper() in currencies:
                rows.append({
                    "currency": code.upper(),
                    "name":     exrate.get("currencyname", "").strip(),
                    "buy":      exrate.get("buy", "").strip(),
                    "transfer": exrate.get("transfer", "").strip(),
                    "sell":     exrate.get("sell", "").strip(),
                })
        if not rows:
            raise ValueError("No exchange rate data")
        return {"type": "exchange_rate", "data": rows, "source": "Vietcombank"}
    except Exception as e:
        logger.warning(f"[EXCHANGE] Vietcombank error: {e}")

    # Fallback: ExchangeRate-API (miễn phí, không cần key)
    try:
        res = requests.get(
            "https://open.er-api.com/v6/latest/USD",
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        d = res.json()
        rates = d.get("rates", {})
        vnd = rates.get("VND", 0)
        rows = []
        for code in ["EUR", "JPY", "CNY", "GBP", "AUD", "SGD"]:
            if code in rates and vnd:
                rate_vnd = round(vnd / rates[code])
                rows.append({"currency": code, "name": code, "buy": str(rate_vnd), "transfer": str(rate_vnd), "sell": str(rate_vnd)})
        rows.insert(0, {"currency": "USD", "name": "Đô la Mỹ", "buy": str(int(vnd * 0.998)), "transfer": str(int(vnd)), "sell": str(int(vnd * 1.002))})
        return {"type": "exchange_rate", "data": rows, "source": "ExchangeRate-API"}
    except Exception as e:
        logger.warning(f"[EXCHANGE] Fallback error: {e}")
        return {"type": "exchange_rate", "data": [], "source": "Vietcombank", "error": str(e)}


# ── Giá xăng dầu Petrolimex ──────────────────────────────────────────────────

def get_fuel_price() -> dict:
    """Lấy giá xăng dầu từ webgia.com (Petrolimex), fallback sang petrolimex.com.vn."""

    # ── Nguồn 1: webgia.com (HTML tĩnh, dễ scrape) ────────────────────────
    try:
        res = requests.get(
            "https://webgia.com/gia-xang-dau/petrolimex/",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        res.raise_for_status()
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        rows = []
        # Bảng giá có class "table table-radius table-hover"
        table = soup.find("table", class_="table-radius")
        if table:
            for tr in table.find("tbody").find_all("tr"):
                cells = tr.find_all(["th", "td"])
                if len(cells) >= 3:
                    name   = cells[0].get_text(strip=True)
                    vung1  = cells[1].get_text(strip=True)
                    vung2  = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    if name and any(c.isdigit() for c in vung1):
                        price_str = f"{vung1} đ/lít (Vùng 1)"
                        if vung2 and vung2 != vung1:
                            price_str += f" | {vung2} đ/lít (Vùng 2)"
                        rows.append({"name": name, "price": price_str})
        if rows:
            return {"type": "fuel", "data": rows[:8], "source": "Petrolimex (webgia.com)"}
    except Exception as e:
        logger.warning(f"[FUEL] webgia.com error: {e}")

    # ── Nguồn 2: petrolimex.com.vn (fallback) ────────────────────────────
    try:
        res = requests.get(
            "https://www.petrolimex.com.vn/nd/gia-ban-le-xang-dau.html",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        rows = []
        for table in soup.find_all("table"):
            for tr in table.find_all("tr")[1:10]:
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    name  = tds[0].get_text(strip=True)
                    price = tds[-1].get_text(strip=True)
                    if any(kw in name.lower() for kw in ["xăng", "dầu", "e5", "ron", "diesel"]):
                        if any(c.isdigit() for c in price):
                            rows.append({"name": name, "price": price})
        if rows:
            return {"type": "fuel", "data": rows[:8], "source": "Petrolimex"}
        raise ValueError("No fuel price found")
    except Exception as e:
        logger.warning(f"[FUEL] Petrolimex error: {e}")
        return {
            "type": "fuel",
            "data": [{"name": "Lưu ý", "price": "Không lấy được giá xăng real-time. Kiểm tra tại petrolimex.com.vn"}],
            "source": "Petrolimex",
            "error": str(e)
        }



# ── Lịch thi đấu bóng đá ──────────────────────────────────────────────────

def get_football_schedule(query: str = "") -> dict:
    """Lấy lịch thi đấu bóng đá hôm nay từ bongda.com.vn."""
    try:
        import datetime
        today_obj = datetime.date.today()
        today = today_obj.strftime("%d-%m-%Y")
        today_api = today_obj.strftime("%Y-%m-%d")

        res = requests.get(
            "https://bongda.com.vn/lich-thi-dau",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        res.raise_for_status()
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        matches = []
        q_lower = query.lower()

        # Bản đồ giải đấu → từ khóa nhập của người dùng
        LEAGUE_FILTER = {
            "world cup":        ["world cup", "fifa world", "w/c"],
            "ngoại hạng anh":   ["ngoại hạng", "premier league", "epl"],
            "champions league": ["champions", "c1", "ucl"],
            "v-league":         ["v-league", "v league", "việt nam"],
            "laliga":           ["laliga", "la liga", "tây ban nha"],
            "serie a":          ["serie a", "ý", "italy"],
            "bundesliga":       ["bundesliga", "đức"],
            "ligue 1":          ["ligue 1", "ligue1", "pháp"],
        }
        target_league = None
        for league_name, kws in LEAGUE_FILTER.items():
            if any(kw in q_lower for kw in kws):
                target_league = league_name
                break

        # Nếu người dùng hỏi World Cup 2026, trả về lịch tĩnh vì hiện chưa đá
        if target_league == "world cup":
            wc_matches = [
                {"league": "World Cup 2026", "time": "11/06/2026", "home": "Mexico", "away": "Chưa xác định", "score": "Khai mạc"},
                {"league": "World Cup 2026", "time": "12/06/2026", "home": "Canada", "away": "Chưa xác định", "score": "Vòng bảng"},
                {"league": "World Cup 2026", "time": "12/06/2026", "home": "Mỹ", "away": "Chưa xác định", "score": "Vòng bảng"}
            ]
            return {"type": "football", "data": wc_matches, "source": "Lịch chuẩn FIFA 2026", "date": "Sắp diễn ra"}

        url = f"https://bongda.com.vn/api/fixtures/get-by-date?date={today_api}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "vi-VN,vi;q=0.9",
        }
        res = requests.get(url, headers=headers, timeout=TIMEOUT)
        res.raise_for_status()

        data_json = res.json()
        html_content = data_json.get("html", "")
        if not html_content:
            raise ValueError("No HTML content in JSON API response")

        soup = BeautifulSoup(html_content, "html.parser")

        for match_el in soup.find_all("li", class_="match-detail"):
            league_el = match_el.find(class_="league")
            current_league = league_el.get_text(strip=True) if league_el else "Giải đấu khác"

            # Lọc giải đấu
            if target_league and target_league.lower() not in current_league.lower():
                continue

            time_el = match_el.find(class_="match-time") or match_el.find(class_="datetime")
            home_el = match_el.find(class_="home-team")
            away_el = match_el.find(class_="away-team")
            status  = match_el.find(class_="status")

            time_txt = time_el.get_text(strip=True).replace("\n", " ").strip() if time_el else ""
            home_txt = home_el.get_text(strip=True) if home_el else ""
            away_txt = away_el.get_text(strip=True) if away_el else ""
            score_txt = status.get_text(strip=True).replace("\n", " ").strip() if status else "vs"

            if home_txt and away_txt:
                matches.append({
                    "league": current_league,
                    "time":   time_txt,
                    "home":   home_txt,
                    "away":   away_txt,
                    "score":  score_txt,
                })
            
            if len(matches) >= 15:
                break

        if not matches:
            if target_league:
                # Trả về data giả định để AI đọc thành một câu thân thiện
                return {
                    "type": "football",
                    "data": [{
                        "league": target_league,
                        "time": "Hôm nay",
                        "home": "Không có",
                        "away": "trận nào",
                        "score": "-"
                    }],
                    "source": "Bongda.com.vn API",
                    "date": today
                }
            else:
                raise ValueError("Không tìm thấy trận đấu nào hôm nay")

        return {"type": "football", "data": matches, "source": "Bongda.com.vn", "date": today}
    except Exception as e:
        logger.warning(f"[FOOTBALL] bongda.com.vn error: {e}")
        return {"type": "football", "data": [], "source": "bongda.com.vn", "error": str(e)}


# ── Thời tiết OpenWeatherMap ──────────────────────────────────────────────────

def get_weather(city: str = "Ho Chi Minh City") -> dict:
    """Lấy thời tiết từ OpenWeatherMap. Cần OPENWEATHER_API_KEY."""
    if not WEATHER_API_KEY:
        return {
            "type": "weather",
            "data": [],
            "source": "OpenWeatherMap",
            "error": "Chưa cấu hình OPENWEATHER_API_KEY"
        }
    try:
        res = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q":     city,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang":  "vi",
            },
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        d = res.json()
        data = {
            "city":        d.get("name", city),
            "temp":        d["main"]["temp"],
            "feels_like":  d["main"]["feels_like"],
            "humidity":    d["main"]["humidity"],
            "description": d["weather"][0]["description"] if d.get("weather") else "",
            "wind_speed":  d["wind"]["speed"],
        }
        return {"type": "weather", "data": [data], "source": "OpenWeatherMap"}
    except Exception as e:
        logger.warning(f"[WEATHER] Error: {e}")
        return {"type": "weather", "data": [], "source": "OpenWeatherMap", "error": str(e)}


# ── Dispatcher ────────────────────────────────────────────────────────────────

REALTIME_KEYWORDS = {
    "gold":          ["giá vàng", "vàng sjc", "vàng 9999", "vàng miếng", "gia vang"],
    "exchange_rate": ["tỷ giá", "giá usd", "đô la", "ngoại tệ", "ty gia", "usd vnd", "eur vnd"],
    "fuel":          ["giá xăng", "giá dầu", "xăng dầu", "petrolimex", "gia xang"],
    "weather":       ["thời tiết", "nhiệt độ", "dự báo thời tiết", "thoi tiet", "mưa nắng"],
    "football":      [
        "bóng đá", "lịch thi đấu", "lich thi dau", "world cup", "ngoại hạng",
        "champions league", "v-league", "bong da", "kết quả bóng đá", "tỷ số",
        "laliga", "serie a", "bundesliga", "ligue 1", "c1 châu âu",
    ],
}


def detect_realtime_type(query: str) -> Optional[str]:
    """Phát hiện query có phải real-time data không. Trả về type hoặc None."""
    q = query.lower()
    for rtype, keywords in REALTIME_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return rtype
    return None


def fetch_realtime(rtype: str, query: str = "") -> dict:
    """Gọi đúng hàm theo type."""
    if rtype == "gold":
        return get_gold_price()
    if rtype == "exchange_rate":
        return get_exchange_rate()
    if rtype == "fuel":
        return get_fuel_price()
    if rtype == "football":
        return get_football_schedule(query)
    if rtype == "weather":
        # Trích tên thành phố từ query nếu có
        city = "Ho Chi Minh City"
        for c in ["hà nội", "hanoi", "ha noi"]:
            if c in query.lower():
                city = "Hanoi"
                break
        for c in ["đà nẵng", "da nang"]:
            if c in query.lower():
                city = "Da Nang"
                break
        return get_weather(city)
    return {"type": rtype, "data": [], "error": "Unknown type"}


def format_realtime_text(result: dict) -> str:
    """Chuyển dữ liệu real-time thành text để AI tổng hợp."""
    rtype = result.get("type", "")
    data  = result.get("data", [])
    source = result.get("source", "")

    if result.get("error") and not data:
        return f"Không lấy được dữ liệu từ {source}: {result['error']}"

    if rtype == "gold":
        lines = [f"GIÁ VÀNG (nguồn: {source}):"]
        for row in data:
            lines.append(f"- {row['name']}: Mua vào {row['buy']} | Bán ra {row['sell']} VNĐ")
        return "\n".join(lines)

    if rtype == "exchange_rate":
        lines = [f"TỶ GIÁ NGOẠI TỆ (nguồn: {source}):"]
        for row in data:
            lines.append(f"- {row['currency']} ({row['name']}): Mua {row['buy']} | Bán {row['sell']} VNĐ")
        return "\n".join(lines)

    if rtype == "fuel":
        lines = [f"GIÁ XĂNG DẦU (nguồn: {source}):"]
        for row in data:
            lines.append(f"- {row['name']}: {row['price']}")
        return "\n".join(lines)

    if rtype == "weather":
        lines = [f"THỜI TIẾT (nguồn: {source}):"]
        for row in data:
            lines.append(
                f"- {row['city']}: {row['temp']}°C, cảm giác {row['feels_like']}°C, "
                f"{row['description']}, độ ẩm {row['humidity']}%, gió {row['wind_speed']} m/s"
            )
        return "\n".join(lines)

    if rtype == "football":
        date_str = result.get("date", "hôm nay")
        lines = [f"LỊCH / KẾT QUẢ BÓNG ĐÁ {date_str} (nguồn: {source}):"]
        current_league = ""
        for m in data:
            if m.get("league") and m["league"] != current_league:
                current_league = m["league"]
                lines.append(f"\n[{current_league}]")
            score = m.get("score", "vs")
            lines.append(f"- {m.get('time', '')} | {m['home']} {score} {m['away']}")
        return "\n".join(lines)

    return str(data)
