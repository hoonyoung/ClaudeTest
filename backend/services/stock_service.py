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

        df = None
        try:
            df = krx.get_market_ohlcv_by_date(start_str, end_str, clean_symbol)
        except Exception as krx_err:
            logger.warning(f"pykrx failed for {clean_symbol}, trying yfinance fallback: {krx_err}")

        if df is None or df.empty:
            # Fallback: yfinance with .KS suffix
            try:
                yfdata = get_us_stock_data(f"{clean_symbol}.KS", period)
                if "error" not in yfdata:
                    yfdata["market"] = "KR"
                    yfdata["currency"] = "KRW"
                    return yfdata
            except Exception:
                pass
            return {"error": f"No data found for Korean symbol: {symbol}"}

        try:
            company_name = krx.get_market_ticker_name(clean_symbol)
        except Exception:
            company_name = clean_symbol

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
    name_upper = company_name.upper().strip()
    name_lower = company_name.lower().strip()

    # 1) Well-known Korean companies mapping (network 호출 없이 즉시 해결)
    KOREAN_COMPANIES = {
        "삼성전자": ("005930", "삼성전자"),
        "삼성": ("005930", "삼성전자"),
        "samsung electronics": ("005930", "삼성전자"),
        "sk하이닉스": ("000660", "SK하이닉스"),
        "sk hynix": ("000660", "SK하이닉스"),
        "현대차": ("005380", "현대자동차"),
        "현대자동차": ("005380", "현대자동차"),
        "hyundai": ("005380", "현대자동차"),
        "lg전자": ("066570", "LG전자"),
        "lg electronics": ("066570", "LG전자"),
        "카카오": ("035720", "카카오"),
        "kakao": ("035720", "카카오"),
        "naver": ("035420", "NAVER"),
        "네이버": ("035420", "NAVER"),
        "셀트리온": ("068270", "셀트리온"),
        "celtrion": ("068270", "셀트리온"),
        "삼성바이오로직스": ("207940", "삼성바이오로직스"),
        "포스코": ("005490", "POSCO홀딩스"),
        "posco": ("005490", "POSCO홀딩스"),
        "kb금융": ("105560", "KB금융"),
        "신한지주": ("055550", "신한지주"),
        "하나금융지주": ("086790", "하나금융지주"),
        "lg화학": ("051910", "LG화학"),
        "sk이노베이션": ("096770", "SK이노베이션"),
        "lotte": ("004990", "롯데지주"),
        "롯데": ("004990", "롯데지주"),
        "기아": ("000270", "기아"),
        "기아차": ("000270", "기아"),
        "kia": ("000270", "기아"),
        "두산": ("000150", "두산"),
        "doosan": ("000150", "두산"),
    }

    if name_lower in KOREAN_COMPANIES:
        kr_symbol, kr_name = KOREAN_COMPANIES[name_lower]
        return {
            "symbol": kr_symbol,
            "name": kr_name,
            "market": "KR",
            "found": True,
        }

    # 2) 6자리 숫자 → 한국 주식 종목코드
    if company_name.strip().isdigit() and len(company_name.strip()) == 6:
        try:
            krx_name = krx.get_market_ticker_name(company_name.strip()) or company_name.strip()
        except Exception:
            krx_name = company_name.strip()
        return {
            "symbol": company_name.strip(),
            "name": krx_name,
            "market": "KR",
            "found": True,
        }

    # 3) 미국 티커 직접 조회
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

    # 4) pykrx 전체 검색 (느릴 수 있음)
    kr_symbol = search_korean_ticker_by_name(company_name)
    if kr_symbol:
        try:
            kr_name = krx.get_market_ticker_name(kr_symbol) or company_name
        except Exception:
            kr_name = company_name
        return {
            "symbol": kr_symbol,
            "name": kr_name,
            "market": "KR",
            "found": True,
        }

    return {"symbol": company_name, "name": company_name, "market": "US", "found": False}
