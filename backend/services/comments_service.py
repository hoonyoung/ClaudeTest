"""Investor comments fetching without API key."""
import requests
from bs4 import BeautifulSoup
import logging
import re
import urllib.parse
from datetime import datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}

KR_BULLISH = {"매수", "상승", "급등", "올라", "호재", "기대", "추천", "좋아", "긍정", "상향", "목표", "돌파", "강세", "매집", "저점"}
KR_BEARISH = {"매도", "하락", "급락", "내려", "악재", "우려", "손절", "떨어", "부정", "하향", "위험", "폭락", "공매도", "고점", "버블"}
EN_BULLISH = {"buy", "bull", "long", "moon", "gain", "profit", "up", "bullish", "calls", "squeeze", "rocket", "hold", "hodl"}
EN_BEARISH = {"sell", "bear", "short", "crash", "dump", "loss", "down", "bearish", "puts", "drop", "tank", "collapse"}


def get_investor_comments(symbol: str, market: str, limit: int = 100) -> dict:
    """Fetch investor comments/discussions for a stock."""
    comments = []

    if market == "KR":
        comments = _get_naver_board_comments(symbol, limit)
    else:
        comments = _get_stocktwits_comments(symbol, limit)
        if len(comments) < limit // 2:
            reddit_comments = _get_reddit_comments(symbol, limit - len(comments))
            comments += reddit_comments

    comments = comments[:limit]
    sentiment_summary = _summarize_sentiment(comments)

    return {
        "comments": comments,
        "total": len(comments),
        "sentiment_summary": sentiment_summary,
        "symbol": symbol,
        "market": market,
    }


def _get_naver_board_comments(ticker: str, limit: int = 100) -> list:
    """Scrape Naver Finance stock discussion board."""
    comments = []
    page = 1
    while len(comments) < limit:
        url = f"https://finance.naver.com/item/board.nhn?code={ticker}&page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            resp.encoding = "euc-kr"
            soup = BeautifulSoup(resp.text, "lxml")

            rows = soup.select("table.type2 tr")
            found_in_page = 0
            for row in rows:
                title_td = row.select_one("td.title")
                date_td = row.select_one("td.date")
                author_td = row.select_one("td.writer")
                view_td = row.select_one("td.num")

                if not title_td:
                    continue
                a_tag = title_td.find("a")
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                if not title:
                    continue

                date = date_td.get_text(strip=True) if date_td else ""
                author = author_td.get_text(strip=True) if author_td else "익명"
                views = view_td.get_text(strip=True) if view_td else "0"

                # Extract agree/disagree from the row
                nums = row.select("td.num")
                agree = nums[1].get_text(strip=True) if len(nums) > 1 else "0"
                disagree = nums[2].get_text(strip=True) if len(nums) > 2 else "0"

                sentiment = _detect_sentiment_kr(title)

                comments.append({
                    "id": f"naver_{ticker}_{page}_{found_in_page}",
                    "author": author,
                    "content": title,
                    "date": date,
                    "likes": _safe_int(agree),
                    "dislikes": _safe_int(disagree),
                    "views": _safe_int(views),
                    "sentiment": sentiment,
                    "source": "네이버 종목토론실",
                })
                found_in_page += 1

            if found_in_page == 0:
                break  # No more pages
            page += 1
            if page > 5:
                break  # Max 5 pages

        except Exception as e:
            logger.warning(f"Naver board scrape error page {page}: {e}")
            break

    return comments


def _get_stocktwits_comments(symbol: str, limit: int = 100) -> list:
    """Fetch messages from StockTwits (no API key required)."""
    comments = []
    max_id = None

    while len(comments) < limit:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        params = {"limit": 30}
        if max_id:
            params["max"] = max_id

        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=8)
            if resp.status_code != 200:
                logger.warning(f"StockTwits returned {resp.status_code}")
                break
            data = resp.json()
            messages = data.get("messages", [])
            if not messages:
                break

            for msg in messages:
                body = msg.get("body", "").strip()
                if not body:
                    continue
                created = msg.get("created_at", "")[:10]
                username = msg.get("user", {}).get("username", "unknown")
                # StockTwits provides sentiment in entities
                raw_sentiment = (
                    msg.get("entities", {})
                    .get("sentiment", {})
                    or {}
                ).get("basic", "")
                if raw_sentiment == "Bullish":
                    sentiment = "긍정"
                elif raw_sentiment == "Bearish":
                    sentiment = "부정"
                else:
                    sentiment = _detect_sentiment_en(body)

                likes = msg.get("likes", {}).get("total", 0) if isinstance(msg.get("likes"), dict) else 0

                comments.append({
                    "id": str(msg.get("id", "")),
                    "author": username,
                    "content": body,
                    "date": created,
                    "likes": likes,
                    "dislikes": 0,
                    "views": 0,
                    "sentiment": sentiment,
                    "source": "StockTwits",
                })

            max_id = messages[-1].get("id")
            if len(messages) < 30:
                break  # Last page

        except Exception as e:
            logger.warning(f"StockTwits error: {e}")
            break

    return comments


def _get_reddit_comments(symbol: str, limit: int = 50) -> list:
    """Fetch posts from Reddit r/stocks and r/wallstreetbets."""
    comments = []
    subreddits = ["stocks", "wallstreetbets", "investing"]

    for sub in subreddits:
        if len(comments) >= limit:
            break
        url = f"https://www.reddit.com/r/{sub}/search.json"
        params = {"q": symbol, "sort": "new", "limit": 25, "type": "link", "t": "month"}
        reddit_headers = {**HEADERS, "User-Agent": "StockAnalyzer/1.0 (educational project)"}
        try:
            resp = requests.get(url, headers=reddit_headers, params=params, timeout=8)
            if resp.status_code != 200:
                continue
            data = resp.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                d = post.get("data", {})
                title = d.get("title", "").strip()
                body = d.get("selftext", "").strip()
                content = title + (f"\n{body[:200]}" if body and body != "[removed]" else "")
                if not content.strip():
                    continue

                created = datetime.utcfromtimestamp(d.get("created_utc", 0)).strftime("%Y-%m-%d")
                author = d.get("author", "unknown")
                score = d.get("score", 0)
                sentiment = _detect_sentiment_en(content)

                comments.append({
                    "id": d.get("id", ""),
                    "author": f"u/{author}",
                    "content": title,
                    "date": created,
                    "likes": score,
                    "dislikes": 0,
                    "views": d.get("num_comments", 0),
                    "sentiment": sentiment,
                    "source": f"Reddit r/{sub}",
                })

        except Exception as e:
            logger.warning(f"Reddit r/{sub} error: {e}")

    return comments


def _detect_sentiment_kr(text: str) -> str:
    words = set(re.findall(r"\w+", text.lower()))
    bull_score = len(words & KR_BULLISH)
    bear_score = len(words & KR_BEARISH)
    if bull_score > bear_score:
        return "긍정"
    elif bear_score > bull_score:
        return "부정"
    return "중립"


def _detect_sentiment_en(text: str) -> str:
    words = set(re.findall(r"\w+", text.lower()))
    bull_score = len(words & EN_BULLISH)
    bear_score = len(words & EN_BEARISH)
    if bull_score > bear_score:
        return "긍정"
    elif bear_score > bull_score:
        return "부정"
    return "중립"


def _summarize_sentiment(comments: list) -> dict:
    counts = {"긍정": 0, "부정": 0, "중립": 0}
    for c in comments:
        s = c.get("sentiment", "중립")
        counts[s] = counts.get(s, 0) + 1
    total = len(comments) or 1
    return {
        "bullish": counts["긍정"],
        "bearish": counts["부정"],
        "neutral": counts["중립"],
        "bullish_pct": round(counts["긍정"] / total * 100),
        "bearish_pct": round(counts["부정"] / total * 100),
        "neutral_pct": round(counts["중립"] / total * 100),
        "total": len(comments),
    }


def _safe_int(value: str) -> int:
    try:
        return int(re.sub(r"[^\d]", "", str(value)) or 0)
    except Exception:
        return 0
