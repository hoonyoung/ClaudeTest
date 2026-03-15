"""News fetching without API key - uses RSS feeds and web scraping."""
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


def _is_korean(text: str) -> bool:
    """Check if text contains Korean characters."""
    korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    return korean_chars > len(text) * 0.1


def _translate_to_korean(text: str) -> str:
    """Translate text to Korean using Google Translate (free, no API key)."""
    if not text or _is_korean(text):
        return text
    try:
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source="auto", target="ko").translate(text)
        return result or text
    except Exception as e:
        logger.debug(f"Translation failed: {e}")
        return text


def get_news_articles(company_name: str, company_symbol: str, market: str) -> dict:
    """Fetch up to 10 news articles without any API key."""
    articles = []

    if market == "KR":
        articles = _get_naver_finance_news(company_symbol)
        if len(articles) < 5:
            extra = _get_google_news_rss(company_name, lang="ko")
            articles += extra
    else:
        articles = _get_google_news_rss(company_name, lang="en")

    articles = articles[:10]

    return {
        "news_items": articles,
        "company_name": company_name,
        "company_symbol": company_symbol,
        "note": "실시간 뉴스 크롤링",
    }


def _get_naver_finance_news(ticker: str) -> list:
    """Fetch news list from Naver Finance for a Korean stock."""
    url = f"https://finance.naver.com/item/news_news.nhn?code={ticker}&page=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(resp.content, "lxml")

        articles = []
        for row in soup.select("table.type5 tr"):
            title_td = row.select_one("td.title")
            date_td = row.select_one("td.date")
            source_td = row.select_one("td.info")
            if not title_td:
                continue
            a_tag = title_td.find("a")
            if not a_tag:
                continue

            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            link = f"https://finance.naver.com{href}" if href.startswith("/") else href
            date = date_td.get_text(strip=True) if date_td else ""
            source = source_td.get_text(strip=True) if source_td else "네이버금융"

            articles.append({
                "title": title,
                "link": link,
                "date": date,
                "source": source,
                "sentiment": "중립",
            })
            if len(articles) >= 10:
                break

        return articles
    except Exception as e:
        logger.warning(f"Naver finance news error: {e}")
        return []


def _get_google_news_rss(query: str, lang: str = "ko") -> list:
    """Fetch news from Google News RSS feed."""
    if lang == "ko":
        params = {"q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
    else:
        params = {"q": query, "hl": "en", "gl": "US", "ceid": "US:en"}

    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(resp.content, "xml")

        articles = []
        for item in soup.select("item"):
            title_tag = item.find("title")
            link_tag = item.find("link")
            pub_tag = item.find("pubDate")
            source_tag = item.find("source")

            if not title_tag:
                continue

            raw_title = title_tag.get_text(strip=True)
            # Google News appends " - Source" at the end
            title = re.sub(r"\s+-\s+[^-]+$", "", raw_title).strip()
            # Translate title to Korean if needed
            title = _translate_to_korean(title)

            link = link_tag.get_text(strip=True) if link_tag else ""
            date = _parse_date(pub_tag.get_text(strip=True) if pub_tag else "")
            source = source_tag.get_text(strip=True) if source_tag else "Google News"

            articles.append({
                "title": title,
                "link": link,
                "date": date,
                "source": source,
                "sentiment": "중립",
            })
            if len(articles) >= 10:
                break

        return articles
    except Exception as e:
        logger.warning(f"Google News RSS error: {e}")
        return []



def _parse_date(raw: str) -> str:
    """Parse RSS pubDate to YYYY-MM-DD format."""
    try:
        dt = datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return raw[:10] if raw else ""
