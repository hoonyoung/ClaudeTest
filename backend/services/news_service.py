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


def get_news_articles(company_name: str, company_symbol: str, market: str) -> dict:
    """Fetch up to 10 news articles without any API key."""
    articles = []

    if market == "KR":
        articles = _get_naver_finance_news(company_symbol)
        if len(articles) < 5:
            articles += _get_google_news_rss(company_name, lang="ko")
    else:
        articles = _get_google_news_rss(company_name, lang="en")

    articles = articles[:10]

    return {
        "summary": _format_summary(articles, company_name),
        "news_items": articles,
        "company_name": company_name,
        "company_symbol": company_symbol,
        "note": "실시간 뉴스 크롤링 (AI 분석 없음)",
    }


def _get_naver_finance_news(ticker: str) -> list:
    """Fetch news list from Naver Finance for a Korean stock."""
    url = f"https://finance.naver.com/item/news_news.nhn?code={ticker}&page=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.encoding = "euc-kr"
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []
        rows = soup.select("table.type5 tr")
        for row in rows:
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

            summary = _fetch_article_summary(link)

            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
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
            # Google News appends " - Source" at the end of title
            title = re.sub(r"\s+-\s+[^-]+$", "", raw_title).strip()
            link = link_tag.get_text(strip=True) if link_tag else ""
            date = _parse_date(pub_tag.get_text(strip=True) if pub_tag else "")
            source = source_tag.get_text(strip=True) if source_tag else "Google News"

            summary = _fetch_article_summary(link) if link else ""

            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
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


def _fetch_article_summary(url: str, max_chars: int = 300) -> str:
    """Fetch article page and extract first 3-4 sentences as summary."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=6, allow_redirects=True)
        # Try euc-kr for Korean news sites, fallback to detected encoding
        if "naver.com" in url or "daum.net" in url:
            resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Try common article body selectors
        body = (
            soup.select_one("article")
            or soup.select_one("#articleBodyContents")   # Naver
            or soup.select_one("#articeBody")            # Naver mobile
            or soup.select_one(".article-body")
            or soup.select_one(".news_end")
            or soup.select_one("#newsct_article")        # Naver news
            or soup.select_one("div[class*='article']")
            or soup.select_one("div[class*='content']")
            or soup.body
        )

        if not body:
            return ""

        text = body.get_text(separator=" ", strip=True)
        # Clean whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Trim to max_chars at sentence boundary
        if len(text) > max_chars:
            cut = text[:max_chars]
            last_period = max(cut.rfind(". "), cut.rfind("다 "), cut.rfind("요 "))
            if last_period > max_chars // 2:
                text = cut[: last_period + 1].strip()
            else:
                text = cut.strip() + "..."

        return text
    except Exception:
        return ""


def _format_summary(articles: list, company_name: str) -> str:
    """Format articles list into a readable markdown summary."""
    if not articles:
        return f"**{company_name}** 관련 최신 뉴스를 가져오지 못했습니다."

    lines = [f"## {company_name} 최신 뉴스\n"]
    for i, a in enumerate(articles, 1):
        title = a.get("title", "")
        summary = a.get("summary", "")
        source = a.get("source", "")
        date = a.get("date", "")
        link = a.get("link", "")

        lines.append(f"**{i}. {title}**")
        if source or date:
            lines.append(f"*{source}{'  ' + date if date else ''}*")
        if summary:
            lines.append(summary)
        if link:
            lines.append(f"[기사 보기]({link})")
        lines.append("")

    return "\n".join(lines)


def _parse_date(raw: str) -> str:
    """Parse RSS pubDate to YYYY-MM-DD format."""
    try:
        dt = datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return raw[:10] if raw else ""
