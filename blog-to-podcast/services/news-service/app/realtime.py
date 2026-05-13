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
    """Lấy giá vàng quốc tế và quy đổi sang VND."""
    try:
        # Lấy tỷ giá USD/VND
        er_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=TIMEOUT)
        er_res.raise_for_status()
        usd_vnd = er_res.json().get("rates", {}).get("VND", 25450)

        # Lấy giá vàng USD/oz từ metals-api (miễn phí)
        gold_res = requests.get(
            "https://api.metals.live/v1/spot/gold",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        gold_res.raise_for_status()
        xau_usd = gold_res.json()[0].get("gold", 0) if gold_res.json() else 0

        if not xau_usd:
            raise ValueError("No gold price")

        # Quy đổi: 1 oz = 31.1035g, 1 lượng = 37.5g, 1 chỉ = 3.75g
        price_luong = round(xau_usd / 31.1035 * 37.5 * usd_vnd / 100000) * 100000
        price_chi   = round(price_luong / 10 / 10000) * 10000

        rows = [
            {"name": "Vàng quốc tế (XAU)", "buy": f"{price_luong:,.0f}", "sell": f"{int(price_luong*1.005):,.0f}"},
            {"name": "Vàng 1 chỉ (quy đổi)", "buy": f"{price_chi:,.0f}", "sell": f"{int(price_chi*1.005):,.0f}"},
        ]
        note = f"(Giá vàng quốc tế: ${xau_usd:,.2f}/oz | Tỷ giá: {usd_vnd:,.0f} VND/USD)"
        return {"type": "gold", "data": rows, "source": f"Metals.live + ExchangeRate-API {note}"}

    except Exception as e:
        logger.warning(f"[GOLD] metals.live error: {e}")

    # Fallback: chỉ dùng tỷ giá + giá vàng cố định gần đúng
    try:
        er_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=TIMEOUT)
        usd_vnd = er_res.json().get("rates", {}).get("VND", 25450)
        # Giá vàng thế giới khoảng $3200-3400/oz (tháng 5/2026)
        xau_usd_approx = 3300
        price_luong = round(xau_usd_approx / 31.1035 * 37.5 * usd_vnd / 100000) * 100000
        rows = [{"name": "Vàng quốc tế (ước tính)", "buy": f"{price_luong:,.0f}", "sell": f"{int(price_luong*1.005):,.0f}"}]
        return {"type": "gold", "data": rows, "source": "Ước tính (tỷ giá thực từ ExchangeRate-API)"}
    except Exception as e2:
        return {"type": "gold", "data": [], "source": "N/A", "error": str(e2)}



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
    """Lấy giá xăng dầu từ Petrolimex."""
    try:
        res = requests.get(
            "https://www.petrolimex.com.vn/nd/gia-ban-le-xang-dau.html",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        rows = []

        # Tìm bảng giá chính xác hơn
        for table in soup.find_all("table"):
            for tr in table.find_all("tr")[1:10]:
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    name  = tds[0].get_text(strip=True)
                    price = tds[-1].get_text(strip=True)
                    # Chỉ lấy dòng có tên xăng/dầu thực sự
                    if any(kw in name.lower() for kw in ["xăng", "dầu", "e5", "e10", "ron", "diesel", "mazut", "diezel"]):
                        if any(c.isdigit() for c in price):
                            rows.append({"name": name, "price": price})

        if rows:
            return {"type": "fuel", "data": rows[:8], "source": "Petrolimex"}

        # Fallback: tìm text có giá cụ thể
        for tag in soup.find_all(["p", "li", "span", "div"]):
            text = tag.get_text(strip=True)
            if any(kw in text.lower() for kw in ["xăng e5", "xăng e10", "dầu diesel", "ron 95"]):
                if any(c.isdigit() for c in text) and len(text) < 150:
                    rows.append({"name": "Giá xăng dầu", "price": text})
                    if len(rows) >= 5:
                        break

        if rows:
            return {"type": "fuel", "data": rows, "source": "Petrolimex"}
        raise ValueError("No fuel price found")

    except Exception as e:
        logger.warning(f"[FUEL] Petrolimex error: {e}")
        # Fallback: thông báo không lấy được
        return {
            "type": "fuel",
            "data": [{"name": "Lưu ý", "price": "Không lấy được giá xăng real-time. Vui lòng kiểm tra tại petrolimex.com.vn"}],
            "source": "Petrolimex",
            "error": str(e)
        }


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
        lines = [f"GIÁ VÀNG SJC (nguồn: {source}):"]
        for row in data:
            lines.append(f"- {row['name']}: Mua {row['buy']} | Bán {row['sell']} (VNĐ/lượng)")
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

    return str(data)
