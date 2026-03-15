from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import math
import os
from dotenv import load_dotenv


def _sanitize(obj):
    """Recursively convert non-JSON-serializable objects (DataFrame, numpy types, NaN, etc.)."""
    try:
        import pandas as pd
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        if isinstance(obj, pd.Series):
            return obj.tolist()
    except ImportError:
        pass
    try:
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return None if math.isnan(float(obj)) else float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except ImportError:
        pass
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(i) for i in obj]
    return obj

from services.stock_service import get_stock_data, resolve_company_to_symbol
from services.news_service import get_news_articles
from services.comments_service import get_investor_comments

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Market Analyzer API",
    description="한국/미국 주식 시장 분석 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    company_name: str
    period: Optional[str] = "3mo"


@app.get("/")
async def root():
    return {"message": "Stock Market Analyzer API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/search")
async def search_company(
    q: str = Query(..., description="Company name or stock symbol"),
    period: str = Query("3mo", description="Data period: 1mo, 3mo, 6mo, 1y, 2y"),
):
    """Search for a company and return stock data + news summary."""
    try:
        logger.info(f"Searching for company: {q}")

        # Resolve company name to symbol
        resolution = resolve_company_to_symbol(q)
        symbol = resolution["symbol"]
        company_name = resolution["name"]
        market = resolution["market"]

        logger.info(f"Resolved to: {symbol} ({company_name}) on {market}")

        # Get stock price data
        stock_data = get_stock_data(symbol, period)

        if "error" in stock_data:
            raise HTTPException(
                status_code=404,
                detail=f"주식 데이터를 찾을 수 없습니다: {stock_data['error']}"
            )

        news_data = get_news_articles(
            company_name=stock_data.get("name", company_name),
            company_symbol=symbol,
            market=market,
        )

        return JSONResponse(content=_sanitize({
            "stock": stock_data,
            "news": news_data,
            "query": q,
            "resolved_symbol": symbol,
        }))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing search for '{q}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}")
async def get_stock(
    symbol: str,
    period: str = Query("3mo", description="Data period: 1mo, 3mo, 6mo, 1y, 2y"),
):
    """Get stock price data for a specific symbol."""
    try:
        data = get_stock_data(symbol, period)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return JSONResponse(content=_sanitize(data))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/{symbol}")
async def get_news(
    symbol: str,
    company_name: Optional[str] = Query(None),
    market: str = Query("US"),
):
    """Get AI-summarized news for a specific symbol."""
    try:
        name = company_name or symbol
        data = get_news_articles(
            company_name=name,
            company_symbol=symbol,
            market=market,
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comments/{symbol}")
async def get_comments(
    symbol: str,
    market: str = Query("US"),
    limit: int = Query(100, ge=10, le=100),
):
    """Get investor comments and sentiment for a stock."""
    try:
        data = get_investor_comments(symbol=symbol, market=market, limit=limit)
        return JSONResponse(content=_sanitize(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
