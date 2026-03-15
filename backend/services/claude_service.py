import anthropic
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


def search_and_summarize_news(company_name: str, company_symbol: str, market: str) -> dict:
    """Use Claude with web search to find and summarize latest news about a company."""
    client = get_client()

    market_label = "한국" if market == "KR" else "미국"
    lang_instruction = (
        "답변은 한국어로 작성해주세요." if market == "KR" else
        "Please write the response in Korean for Korean users."
    )

    prompt = f"""
{market_label} 주식 시장의 '{company_name}' (종목코드: {company_symbol}) 회사에 대한 최신 뉴스와 정보를 검색해주세요.

다음 내용을 포함하여 분석해주세요:
1. **최신 뉴스 요약** (최근 1-2주 이내 주요 뉴스 3-5개)
2. **주가 관련 이슈** (실적 발표, 주요 사업 변화 등)
3. **시장 전망** (애널리스트 의견, 업계 동향)
4. **리스크 요인** (주의해야 할 부정적 요인들)

{lang_instruction}

각 뉴스 항목은 다음 형식으로 작성해주세요:
- 제목
- 핵심 내용 (2-3문장)
- 주가에 미치는 영향 (긍정/부정/중립)
"""

    try:
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=[
                {
                    "type": "web_search_20260209",
                    "name": "web_search",
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            response = stream.get_final_message()

        # Extract text content
        content_text = ""
        for block in response.content:
            if block.type == "text":
                content_text += block.text

        # Parse news items from the response
        news_items = parse_news_items(content_text)

        return {
            "summary": content_text,
            "news_items": news_items,
            "company_name": company_name,
            "company_symbol": company_symbol,
        }

    except (anthropic.BadRequestError, anthropic.APIStatusError) as e:
        logger.warning(f"Web search not available, falling back to knowledge: {e}")
        return get_news_from_knowledge(client, company_name, company_symbol, market)
    except Exception as e:
        logger.error(f"Claude API error: {e}", exc_info=True)
        return {
            "summary": f"{company_name}에 대한 뉴스를 가져오는 중 오류가 발생했습니다: {str(e)}",
            "news_items": [],
            "company_name": company_name,
            "company_symbol": company_symbol,
        }


def get_news_from_knowledge(
    client: anthropic.Anthropic,
    company_name: str,
    company_symbol: str,
    market: str,
) -> dict:
    """Fallback: use Claude's knowledge base to provide company analysis."""
    market_label = "한국" if market == "KR" else "미국"

    prompt = f"""
{market_label} 주식 시장의 '{company_name}' (종목코드: {company_symbol}) 회사에 대해 알고 있는 최신 정보를 바탕으로 분석해주세요.

다음 내용을 포함하여 분석해주세요:
1. **회사 개요** (주요 사업, 시장 지위)
2. **최근 동향** (알려진 주요 이슈 및 사업 현황)
3. **경쟁 환경** (주요 경쟁사, 업계 동향)
4. **투자 고려사항** (강점, 리스크 요인)

답변은 한국어로 작성해주세요.
참고: 실시간 뉴스 검색이 불가하여 학습 데이터 기반 분석입니다.
"""

    try:
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            response = stream.get_final_message()

        content_text = ""
        for block in response.content:
            if block.type == "text":
                content_text += block.text

        return {
            "summary": content_text,
            "news_items": [],
            "company_name": company_name,
            "company_symbol": company_symbol,
            "note": "실시간 검색 불가 - 학습 데이터 기반 분석",
        }
    except Exception as e:
        logger.error(f"get_news_from_knowledge error: {e}", exc_info=True)
        return {
            "summary": f"{company_name} 분석 중 오류가 발생했습니다: {str(e)}",
            "news_items": [],
            "company_name": company_name,
            "company_symbol": company_symbol,
        }


def parse_news_items(text: str) -> list:
    """Parse structured news items from Claude's response."""
    lines = text.split("\n")
    items = []
    current_item = {}

    for line in lines:
        line = line.strip()
        if not line:
            if current_item:
                items.append(current_item)
                current_item = {}
            continue

        if line.startswith("**") and line.endswith("**"):
            if current_item:
                items.append(current_item)
            current_item = {"title": line.strip("*").strip(), "content": "", "sentiment": "중립"}
        elif current_item and line.startswith("-"):
            content = line[1:].strip()
            if "긍정" in content:
                current_item["sentiment"] = "긍정"
            elif "부정" in content:
                current_item["sentiment"] = "부정"
            else:
                current_item["content"] += content + " "

    if current_item:
        items.append(current_item)

    # Return at most 5 items with content
    return [item for item in items if item.get("title") or item.get("content")][:5]
