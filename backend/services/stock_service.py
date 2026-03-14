import yfinance as yf
import pandas as pd
from pykrx import stock as krx
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

KOREAN_MARKET_SUFFIXES = [".KS", ".KQ"]

def search_ticker_by_name(company_name: str) -> Optional[str]:
    """Search for a US stock ticker by company name using yfinance."""
    try:
        ticker = yf.Ticker(company_name)
        info = ticker.info
        if info and info.get("symbol"):
            return info["symbol"]
    except Exception:
        pass

    # Try direct lookup
    try:
        ticker = yf.Ticker(company_name.upper())
        info = ticker.info
        if info and info.get("longName"):
            return company_name.upper()
    except Exception:
        pass

    return None


def search_korean_ticker_by_name(company_name: str) -> Optional[str]:
    """Search for a Korean stock ticker by company name."""
    try:
        today = datetime.today().strftime("%Y%m%d")
        tickers = krx.get_market_ticker_list(today, market="ALL")
        for ticker in tickers:
            name = krx.get_market_ticker_name(ticker)
            if company_name.lower() in name.lower() or name.lower() in company_name.lower():
                return ticker
    except Exception as e:
        logger.error(f"Korean ticker search error: {e}")
    return None


def get_stock_data(symbol: str, period: str = "3mo") -> dict:
    """Fetch stock data for a given symbol."""
    # Detect if Korean stock
    is_korean = symbol.endswith(".KS") or symbol.endswith(".KQ") or (
        symbol.isdigit() and len(symbol) == 6
    )

    if is_korean:
        return get_korean_stock_data(symbol, period)
    else:
        return get_us_stock_data(symbol, period)


def get_us_stock_data(symbol: str, period: str = "3mo") -> dict:
    """Fetch US stock data using yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        info = ticker.info

        if hist.empty:
            return {"error": f"No data found for symbol: {symbol}"}

        prices = []
        for date, row in hist.iterrows():
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        current_price = prices[-1]["close"] if prices else 0
        prev_price = prices[-2]["close"] if len(prices) > 1 else current_price
        change = round(current_price - prev_price, 2)
        change_pct = round((change / prev_price) * 100, 2) if prev_price else 0

        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "market": "US",
            "currency": info.get("currency", "USD"),
            "current_price": current_price,
            "change": change,
            "change_pct": change_pct,
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "description": info.get("longBusinessSummary", ""),
            "prices": prices,
        }
    except Exception as e:
        logger.error(f"US stock data error for {symbol}: {e}")
        return {"error": str(e)}


def get_korean_stock_data(symbol: str, period: str = "3mo") -> dict:
    """Fetch Korean stock data using pykrx."""
    try:
        end_date = datetime.today()
        period_map = {
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
        }
        days = period_map.get(period, 90)
        start_date = end_date - timedelta(days=days)

        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        # Remove exchange suffix for pykrx
        clean_symbol = symbol.replace(".KS", "").replace(".KQ", "")

        df = krx.get_market_ohlcv_by_date(start_str, end_str, clean_symbol)

        if df is None or df.empty:
            return {"error": f"No data found for Korean symbol: {symbol}"}

        company_name = krx.get_market_ticker_name(clean_symbol)

        prices = []
        for date, row in df.iterrows():
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": int(row["시가"]),
                "high": int(row["고가"]),
                "low": int(row["저가"]),
                "close": int(row["종가"]),
                "volume": int(row["거래량"]),
            })

        current_price = prices[-1]["close"] if prices else 0
        prev_price = prices[-2]["close"] if len(prices) > 1 else current_price
        change = current_price - prev_price
        change_pct = round((change / prev_price) * 100, 2) if prev_price else 0

        return {
            "symbol": clean_symbol,
            "name": company_name,
            "market": "KR",
            "currency": "KRW",
            "current_price": current_price,
            "change": change,
            "change_pct": change_pct,
            "prices": prices,
        }
    except Exception as e:
        logger.error(f"Korean stock data error for {symbol}: {e}")
        return {"error": str(e)}


def resolve_company_to_symbol(company_name: str) -> dict:
    """Try to resolve a company name to a stock symbol."""
    # Check if it's already a known ticker format
    name_upper = company_name.upper().strip()

    # Try as US ticker directly
    try:
        ticker = yf.Ticker(name_upper)
        info = ticker.info
        if info and info.get("longName"):
            return {
                "symbol": name_upper,
                "name": info["longName"],
                "market": "US",
                "found": True,
            }
    except Exception:
        pass

    # Try Korean market (6-digit number)
    if company_name.strip().isdigit() and len(company_name.strip()) == 6:
        krx_name = krx.get_market_ticker_name(company_name.strip())
        if krx_name:
            return {
                "symbol": company_name.strip(),
                "name": krx_name,
                "market": "KR",
                "found": True,
            }

    # Search Korean market by name
    kr_symbol = search_korean_ticker_by_name(company_name)
    if kr_symbol:
        kr_name = krx.get_market_ticker_name(kr_symbol)
        return {
            "symbol": kr_symbol,
            "name": kr_name,
            "market": "KR",
            "found": True,
        }

    # Well-known Korean companies mapping
    KOREAN_COMPANIES = {
        "삼성전자": "005930",
        "삼성": "005930",
        "samsung electronics": "005930",
        "sk하이닉스": "000660",
        "sk hynix": "000660",
        "현대차": "005380",
        "현대자동차": "005380",
        "hyundai": "005380",
        "lg전자": "066570",
        "lg electronics": "066570",
        "카카오": "035720",
        "kakao": "035720",
        "naver": "035420",
        "네이버": "035420",
        "셀트리온": "068270",
        "celtrion": "068270",
        "삼성바이오로직스": "207940",
        "포스코": "005490",
        "posco": "005490",
        "kb금융": "105560",
        "신한지주": "055550",
        "하나금융지주": "086790",
        "lg화학": "051910",
        "sk이노베이션": "096770",
        "lotte": "004990",
        "롯데": "004990",
        "기아": "000270",
        "기아차": "000270",
        "kia": "000270",
        "두산": "000150",
        "doosan": "000150",
    }

    name_lower = company_name.lower().strip()
    if name_lower in KOREAN_COMPANIES:
        kr_symbol = KOREAN_COMPANIES[name_lower]
        kr_name = krx.get_market_ticker_name(kr_symbol)
        return {
            "symbol": kr_symbol,
            "name": kr_name or company_name,
            "market": "KR",
            "found": True,
        }

    return {"symbol": company_name, "name": company_name, "market": "US", "found": False}
