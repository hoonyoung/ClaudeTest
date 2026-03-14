from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import os
from dotenv import load_dotenv

from services.stock_service import get_stock_data, resolve_company_to_symbol
from services.claude_service import search_and_summarize_news

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

        # Get news and AI summary (run concurrently would be ideal, but keeping it simple)
        news_data = search_and_summarize_news(
            company_name=stock_data.get("name", company_name),
            company_symbol=symbol,
            market=market,
        )

        return JSONResponse(content={
            "stock": stock_data,
            "news": news_data,
            "query": q,
            "resolved_symbol": symbol,
        })

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
        return data
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
        data = search_and_summarize_news(
            company_name=name,
            company_symbol=symbol,
            market=market,
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
