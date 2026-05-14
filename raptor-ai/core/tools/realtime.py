"""
Real-time data tools for Raptor.
Fetches weather (wttr.in) and news (NYT RSS).
No API key required.
"""
import urllib.request
import xml.etree.ElementTree as ET
import re
import ssl

# macOS often lacks system CA certs for Python — bypass for public read-only APIs
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def get_weather(city: str) -> str:
    """Fetches current weather for a city using wttr.in (no API key needed)."""
    city_clean = city.strip().replace(" ", "+")
    url = f"https://wttr.in/{city_clean}?format=3"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAPTOR-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=5, context=_ssl_ctx) as resp:
            result = resp.read().decode("utf-8").strip()
        if result:
            return result
        return f"Could not get weather for {city}."
    except Exception as e:
        return f"Weather fetch failed: {e}"


def get_news() -> str:
    """Fetches top 5 headlines from NYT RSS feed (free, no API key)."""
    url = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAPTOR-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=5, context=_ssl_ctx) as resp:
            raw = resp.read()

        root = ET.fromstring(raw)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []

        headlines = []
        for i, item in enumerate(items[:5], 1):
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                # Strip any HTML tags just in case
                clean = re.sub(r"<[^>]+>", "", title_el.text).strip()
                headlines.append(f"{i}. {clean}")

        if not headlines:
            return "No headlines retrieved."

        return "Top headlines: " + ". ".join(headlines)
    except Exception as e:
        return f"News fetch failed: {e}"


# ── Live Cricket Scores ──────────────────────────────────────────────────
def get_cricket_scores() -> str:
    """Fetch live cricket scores from ESPN Cricinfo RSS (free, no API key)."""
    url = "https://www.espncricinfo.com/rss/livescores.xml"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAPTOR-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=8, context=_ssl_ctx) as resp:
            raw = resp.read()

        root = ET.fromstring(raw)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []

        scores = []
        for i, item in enumerate(items[:5], 1):
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                clean = re.sub(r"<[^>]+>", "", title_el.text).strip()
                scores.append(f"{i}. {clean}")

        if not scores:
            return "No live cricket matches right now."

        print(f"[REALTIME] Cricket: fetched {len(scores)} live scores.")
        return "Live cricket scores: " + ". ".join(scores)
    except Exception as e:
        print(f"[REALTIME] Cricket fetch error: {e}")
        return f"Cricket scores fetch failed: {e}"


# ── Weather Forecast (multi-day) ─────────────────────────────────────────
def get_weather_forecast(city: str, days: int = 3) -> str:
    """Fetch multi-day weather forecast from wttr.in JSON endpoint (free)."""
    import json

    city_clean = city.strip().replace(" ", "+")
    url = f"https://wttr.in/{city_clean}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAPTOR-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=8, context=_ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Current conditions
        current = data.get("current_condition", [{}])[0]
        temp_c = current.get("temp_C", "?")
        feels_like = current.get("FeelsLikeC", "?")
        desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        humidity = current.get("humidity", "?")
        wind_kmph = current.get("windspeedKmph", "?")

        area = data.get("nearest_area", [{}])[0]
        area_name = area.get("areaName", [{}])[0].get("value", city)

        parts = [
            f"Current in {area_name}: {temp_c}°C, feels like {feels_like}°C. "
            f"{desc}. Humidity {humidity}%, wind {wind_kmph} km/h."
        ]

        # Forecast days
        weather_list = data.get("weather", [])
        for day_data in weather_list[:days]:
            date = day_data.get("date", "")
            max_c = day_data.get("maxtempC", "?")
            min_c = day_data.get("mintempC", "?")
            # Average hourly description
            hourly = day_data.get("hourly", [])
            mid_desc = "Unknown"
            if len(hourly) >= 4:
                mid_desc = hourly[4].get("weatherDesc", [{}])[0].get("value", "Unknown")
            elif hourly:
                mid_desc = hourly[0].get("weatherDesc", [{}])[0].get("value", "Unknown")
            parts.append(f"{date}: {min_c}°C to {max_c}°C, {mid_desc}")

        print(f"[REALTIME] Weather forecast: {area_name}, {len(weather_list)} days.")
        return ". ".join(parts)
    except Exception as e:
        print(f"[REALTIME] Forecast fetch error: {e}")
        return f"Weather forecast fetch failed: {e}"


# ── Live Football Scores ─────────────────────────────────────────────────
def get_football_scores() -> str:
    """Fetch live football/soccer scores from ESPN RSS (free, no API key)."""
    url = "https://www.espn.com/espn/rss/soccer/news"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAPTOR-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=8, context=_ssl_ctx) as resp:
            raw = resp.read()

        root = ET.fromstring(raw)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []

        scores = []
        for i, item in enumerate(items[:5], 1):
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                clean = re.sub(r"<[^>]+>", "", title_el.text).strip()
                scores.append(f"{i}. {clean}")

        if not scores:
            return "No live football updates right now."

        print(f"[REALTIME] Football: fetched {len(scores)} updates.")
        return "Football updates: " + ". ".join(scores)
    except Exception as e:
        print(f"[REALTIME] Football fetch error: {e}")
        return f"Football scores fetch failed: {e}"


# ── Stock / Crypto Price ─────────────────────────────────────────────────
def get_stock_price(symbol: str) -> str:
    """Fetch current stock/crypto price from Yahoo Finance (free, no API key).

    Supports tickers like AAPL, GOOGL, TSLA, BTC-USD, ETH-USD, etc.
    """
    import json

    symbol_clean = symbol.strip().upper().replace(" ", "-")
    # Common aliases
    aliases = {
        "BITCOIN": "BTC-USD", "BTC": "BTC-USD",
        "ETHEREUM": "ETH-USD", "ETH": "ETH-USD",
        "APPLE": "AAPL", "GOOGLE": "GOOGL", "ALPHABET": "GOOGL",
        "AMAZON": "AMZN", "MICROSOFT": "MSFT", "TESLA": "TSLA",
        "META": "META", "FACEBOOK": "META",
        "NVIDIA": "NVDA", "NETFLIX": "NFLX",
        "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "INFOSYS": "INFY.NS",
        "SENSEX": "^BSESN", "NIFTY": "^NSEI", "NIFTY50": "^NSEI",
    }
    ticker = aliases.get(symbol_clean, symbol_clean)

    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?range=1d&interval=1d"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAPTOR-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=8, context=_ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("chartPreviousClose", 0)
        currency = meta.get("currency", "USD")
        name = meta.get("shortName") or meta.get("symbol", ticker)

        change = price - prev_close
        pct = (change / prev_close * 100) if prev_close else 0
        direction = "up" if change >= 0 else "down"
        arrow = "↑" if change >= 0 else "↓"

        result = (
            f"{name}: {price:.2f} {currency}, "
            f"{arrow} {abs(change):.2f} ({abs(pct):.1f}%) {direction} today."
        )
        print(f"[REALTIME] Stock: {ticker} = {price} {currency}")
        return result
    except Exception as e:
        print(f"[REALTIME] Stock fetch error for {ticker}: {e}")
        return f"Could not fetch price for {symbol}. {e}"


# ── Music Playback ───────────────────────────────────────────────────────
def play_music(query: str = "") -> dict:
    import webbrowser
    import urllib.parse
    
    if not query:
        return {
            "status": "ask",
            "message": "What song would you like to hear?"
        }
        
    print(f"[REALTIME] Playing music: {query}")
    query_encoded = urllib.parse.quote_plus(query)
    # Using YouTube for free music search. 
    # Not using 'auto-click first result' directly via python as it requires complex parsing or Selenium.
    # Opening the search page directly is the most reliable fallback-free approach.
    url = f"https://www.youtube.com/results?search_query={query_encoded}"
    
    try:
        webbrowser.open(url)
        return {
            "status": "success",
            "message": f"Playing {query} on YouTube."
        }
    except Exception as exc:
        print(f"[REALTIME] Failed to open YouTube: {exc}")
        return {
            "status": "failed",
            "message": f"Could not play {query}. {exc}"
        }


# ── World Monitor ────────────────────────────────────────────────────────
WORLD_MONITOR_URL = (
    "https://www.worldmonitor.app/"
    "?lat=3.6120&lon=0.0000&zoom=1.00&view=global"
    "&timeRange=7d"
    "&layers=conflicts%2Cbases%2Chotspots%2Cnuclear%2Cirradiators"
    "%2Csanctions%2Cweather%2Ceconomic%2Cwaterways%2Coutages"
    "%2Cmilitary%2Cnatural%2CiranAttacks"
)

_last_world_monitor_open: float = 0.0  # epoch timestamp of last open


def open_world_monitor() -> dict:
    """Open the World Monitor global-situation dashboard.

    Includes 15-second tab-dedup: if the same URL was opened less than
    15 seconds ago the browser open is skipped to prevent duplicate tabs.
    """
    import time
    import webbrowser

    global _last_world_monitor_open

    now = time.time()
    elapsed = now - _last_world_monitor_open

    if elapsed < 15.0:
        print(f"[WORLD_MONITOR] Tab dedup: last opened {elapsed:.1f}s ago — skipping re-open.")
        return {
            "status": "success",
            "message": "World Monitor is already open.",
        }

    print(f"[WORLD_MONITOR] Opening global situation dashboard.")
    try:
        webbrowser.open(WORLD_MONITOR_URL)
        _last_world_monitor_open = time.time()
        return {
            "status": "success",
            "message": "Displaying global situation on World Monitor.",
        }
    except Exception as exc:
        print(f"[WORLD_MONITOR] Failed to open URL: {exc}")
        return {
            "status": "failed",
            "message": f"Could not open World Monitor. {exc}",
        }
