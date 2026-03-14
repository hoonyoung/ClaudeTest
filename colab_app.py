"""
주식 시장 분석기 - Gradio 버전 (Google Colab / 로컬 실행용)

실행 방법:
  pip install gradio yfinance pykrx anthropic matplotlib mplfinance
  python colab_app.py
  또는 Google Colab에서 셀별로 실행
"""

import os
import io
import base64
import warnings
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# 주가 데이터 수집
# ─────────────────────────────────────────

def get_us_stock(symbol: str, period: str):
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)
    if hist.empty:
        return None, None
    info = ticker.info
    return hist, info


def get_kr_stock(symbol: str, period: str):
    from pykrx import stock as krx

    end_date = datetime.today()
    days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    days = days_map.get(period, 90)
    start_date = end_date - timedelta(days=days)

    clean = symbol.replace(".KS", "").replace(".KQ", "")
    df = krx.get_market_ohlcv_by_date(
        start_date.strftime("%Y%m%d"),
        end_date.strftime("%Y%m%d"),
        clean,
    )
    name = krx.get_market_ticker_name(clean)
    return df, name


KOREAN_TICKER_MAP = {
    "삼성전자": "005930", "삼성": "005930",
    "samsung": "005930", "samsung electronics": "005930",
    "sk하이닉스": "000660", "sk hynix": "000660",
    "현대차": "005380", "현대자동차": "005380", "hyundai": "005380",
    "기아": "000270", "기아차": "000270", "kia": "000270",
    "lg전자": "066570", "lg electronics": "066570",
    "카카오": "035720", "kakao": "035720",
    "네이버": "035420", "naver": "035420",
    "셀트리온": "068270",
    "삼성바이오로직스": "207940",
    "포스코": "005490", "posco": "005490",
    "kb금융": "105560",
    "신한지주": "055550",
    "하나금융지주": "086790",
    "lg화학": "051910",
    "sk이노베이션": "096770",
    "롯데": "004990", "lotte": "004990",
    "두산": "000150", "doosan": "000150",
}


def resolve_symbol(query: str):
    """입력된 회사명 / 종목코드를 통일된 형태로 변환"""
    q = query.strip()

    # 6자리 숫자 → 한국 주식
    if q.isdigit() and len(q) == 6:
        try:
            from pykrx import stock as krx
            name = krx.get_market_ticker_name(q)
            return q, name or q, "KR"
        except Exception:
            return q, q, "KR"

    # .KS / .KQ 접미사
    if q.upper().endswith((".KS", ".KQ")):
        clean = q.upper().replace(".KS", "").replace(".KQ", "")
        try:
            from pykrx import stock as krx
            name = krx.get_market_ticker_name(clean)
            return clean, name or clean, "KR"
        except Exception:
            return clean, clean, "KR"

    # 한국어 회사명 매핑
    if q.lower() in KOREAN_TICKER_MAP:
        ticker = KOREAN_TICKER_MAP[q.lower()]
        try:
            from pykrx import stock as krx
            name = krx.get_market_ticker_name(ticker)
            return ticker, name or q, "KR"
        except Exception:
            return ticker, q, "KR"

    # pykrx 전체 검색
    try:
        from pykrx import stock as krx
        today = datetime.today().strftime("%Y%m%d")
        for market in ("KOSPI", "KOSDAQ"):
            for t in krx.get_market_ticker_list(today, market=market):
                nm = krx.get_market_ticker_name(t)
                if q.lower() in nm.lower() or nm.lower() in q.lower():
                    return t, nm, "KR"
    except Exception:
        pass

    # 미국 주식 (yfinance)
    try:
        import yfinance as yf
        t = yf.Ticker(q.upper())
        info = t.info
        if info and info.get("longName"):
            return q.upper(), info["longName"], "US"
    except Exception:
        pass

    return q.upper(), q, "US"


# ─────────────────────────────────────────
# 차트 생성 (matplotlib)
# ─────────────────────────────────────────

def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def make_chart(symbol: str, company_name: str, market: str, period: str):
    """주가 차트 + 거래량 차트를 생성하여 base64 PNG 반환"""
    BG = "#0f172a"
    FG = "#e2e8f0"
    GRID = "#1e293b"
    UP_C = "#22c55e"
    DOWN_C = "#ef4444"
    VOL_C = "#3b82f680"
    MA20_C = "#f59e0b"
    MA60_C = "#a78bfa"

    try:
        if market == "KR":
            df, _ = get_kr_stock(symbol, period)
            if df is None or df.empty:
                return None, "데이터 없음"
            dates = df.index
            opens = df["시가"].values.astype(float)
            highs = df["고가"].values.astype(float)
            lows = df["저가"].values.astype(float)
            closes = df["종가"].values.astype(float)
            volumes = df["거래량"].values.astype(float)
            currency = "₩"
        else:
            hist, info = get_us_stock(symbol, period)
            if hist is None or hist.empty:
                return None, "데이터 없음"
            dates = hist.index
            opens = hist["Open"].values.astype(float)
            highs = hist["High"].values.astype(float)
            lows = hist["Low"].values.astype(float)
            closes = hist["Close"].values.astype(float)
            volumes = hist["Volume"].values.astype(float)
            currency = "$"

        # 이동평균
        def ma(arr, n):
            result = np.full_like(arr, np.nan)
            for i in range(n - 1, len(arr)):
                result[i] = arr[i - n + 1 : i + 1].mean()
            return result

        ma20 = ma(closes, 20)
        ma60 = ma(closes, min(60, len(closes)))

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(12, 7), gridspec_kw={"height_ratios": [3, 1]},
            facecolor=BG,
        )
        fig.subplots_adjust(hspace=0.08)

        for ax in (ax1, ax2):
            ax.set_facecolor(BG)
            ax.tick_params(colors=FG, labelsize=8)
            ax.spines[:].set_color(GRID)
            ax.grid(axis="y", color=GRID, linewidth=0.5, linestyle="--")
            ax.yaxis.set_tick_params(color=GRID)

        # ── 캔들스틱 ──────────────────────────────
        width = 0.6
        x = np.arange(len(dates))
        colors = np.where(closes >= opens, UP_C, DOWN_C)

        ax1.bar(x, np.abs(closes - opens), bottom=np.minimum(opens, closes),
                width=width, color=colors, alpha=0.9)
        ax1.vlines(x, lows, highs, color=colors, linewidth=0.8)

        # 이동평균선
        valid20 = ~np.isnan(ma20)
        valid60 = ~np.isnan(ma60)
        if valid20.sum() > 1:
            ax1.plot(x[valid20], ma20[valid20], color=MA20_C, linewidth=1.2,
                     label="MA20", zorder=3)
        if valid60.sum() > 1:
            ax1.plot(x[valid60], ma60[valid60], color=MA60_C, linewidth=1.2,
                     label="MA60", zorder=3)

        # 최신 가격 표시
        last_price = closes[-1]
        change = closes[-1] - closes[-2] if len(closes) > 1 else 0
        change_pct = change / closes[-2] * 100 if len(closes) > 1 and closes[-2] != 0 else 0
        sign = "+" if change >= 0 else ""
        price_color = UP_C if change >= 0 else DOWN_C

        if currency == "₩":
            price_str = f"{currency}{last_price:,.0f}"
            change_str = f"{sign}{change:,.0f} ({sign}{change_pct:.2f}%)"
        else:
            price_str = f"{currency}{last_price:.2f}"
            change_str = f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)"

        ax1.set_title(
            f"{company_name}  ({symbol})   {price_str}  {change_str}",
            color=FG, fontsize=12, fontweight="bold", pad=10,
        )
        ax1.title.set_color(price_color if change != 0 else FG)

        # Y축 포맷
        if currency == "₩":
            ax1.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda v, _: f"₩{v/1000:.0f}K" if v >= 1000 else f"₩{v:.0f}")
            )
        else:
            ax1.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda v, _: f"${v:.0f}")
            )

        leg = ax1.legend(loc="upper left", facecolor=GRID, edgecolor=GRID,
                         labelcolor=FG, fontsize=8)

        # ── 거래량 ──────────────────────────────
        ax2.bar(x, volumes, color=VOL_C, width=width)
        ax2.set_ylabel("거래량", color=FG, fontsize=8)
        ax2.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"{v/1_000_000:.1f}M" if v >= 1_000_000 else f"{v/1_000:.0f}K")
        )

        # X축 날짜 레이블
        step = max(1, len(dates) // 8)
        tick_idx = list(range(0, len(dates), step))
        if tick_idx[-1] != len(dates) - 1:
            tick_idx.append(len(dates) - 1)
        tick_labels = [str(dates[i])[:10] for i in tick_idx]

        for ax in (ax1, ax2):
            ax.set_xticks(tick_idx)
        ax1.set_xticklabels([""] * len(tick_idx))
        ax2.set_xticklabels(tick_labels, rotation=30, ha="right", fontsize=7)

        b64 = _fig_to_base64(fig)
        return f"data:image/png;base64,{b64}", None

    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────
# Claude AI 뉴스 분석
# ─────────────────────────────────────────

def analyze_news(company_name: str, symbol: str, market: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "⚠️ ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.\n`os.environ['ANTHROPIC_API_KEY'] = 'sk-...'` 로 설정해주세요."

    import anthropic as ant

    client = ant.Anthropic(api_key=api_key)
    market_label = "한국" if market == "KR" else "미국"

    prompt = f"""{market_label} 주식 '{company_name}' ({symbol})의 최신 뉴스와 주가 동향을 분석해주세요.

아래 항목을 포함해주세요:
1. **최신 주요 뉴스** (최근 1~2주, 3~5개 항목)
   - 각 뉴스: 제목, 핵심 내용 2~3문장, 주가 영향 (긍정🟢/부정🔴/중립⚪)
2. **실적 및 사업 현황** (최근 분기 실적, 주요 사업 변화)
3. **시장 전망** (애널리스트 목표가, 업계 동향)
4. **리스크 요인** (주의해야 할 부정적 요소)

답변은 한국어로, 마크다운 형식으로 작성해주세요."""

    try:
        # 웹 검색 도구 사용 시도
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=3000,
            thinking={"type": "adaptive"},
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            response = stream.get_final_message()
        source_note = "🔍 *실시간 웹 검색 기반 분석*"
    except Exception:
        # 웹 검색 불가 시 지식 기반 분석
        try:
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                response = stream.get_final_message()
            source_note = "📚 *학습 데이터 기반 분석 (실시간 검색 불가)*"
        except Exception as e:
            return f"❌ Claude API 오류: {e}"

    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text

    return f"{source_note}\n\n---\n\n{text}"


# ─────────────────────────────────────────
# Gradio UI
# ─────────────────────────────────────────

def run_analysis(query: str, period: str, api_key_input: str):
    """메인 분석 함수 - Gradio에서 호출"""
    if not query.strip():
        return (
            None,
            "⚠️ 회사명 또는 종목코드를 입력해주세요.",
            "### 검색 결과가 여기에 표시됩니다",
        )

    # API 키 설정
    if api_key_input.strip():
        os.environ["ANTHROPIC_API_KEY"] = api_key_input.strip()

    period_map = {
        "1개월": "1mo", "3개월": "3mo", "6개월": "6mo", "1년": "1y", "2년": "2y",
    }
    period_code = period_map.get(period, "3mo")

    # 1. 종목 해석
    status_msg = f"🔍 '{query}' 검색 중..."
    symbol, company_name, market = resolve_symbol(query)
    status_msg = f"✅ {company_name} ({symbol}) [{market}] 데이터 로딩..."

    # 2. 차트 생성
    chart_img, chart_err = make_chart(symbol, company_name, market, period_code)
    if chart_err:
        status_msg = f"⚠️ 차트 오류: {chart_err}"

    # 3. 뉴스 분석
    news_text = analyze_news(company_name, symbol, market)

    stock_info = f"### {company_name} ({symbol})  [{market} 시장]\n기간: {period}"

    return chart_img, stock_info, news_text


def create_app():
    import gradio as gr

    PERIOD_CHOICES = ["1개월", "3개월", "6개월", "1년", "2년"]
    QUICK_PICKS = [
        "삼성전자", "SK하이닉스", "네이버", "카카오", "현대차",
        "AAPL", "NVDA", "MSFT", "TSLA", "GOOGL",
    ]

    with gr.Blocks(
        title="주식 시장 분석기",
        theme=gr.themes.Base(
            primary_hue="blue",
            neutral_hue="slate",
        ),
        css="""
        .container { max-width: 1100px; margin: 0 auto; }
        .quick-btn { margin: 2px !important; }
        """,
    ) as demo:
        gr.Markdown(
            """
# 📈 주식 시장 분석기
**한국 · 미국 주식 뉴스 AI 분석 & 주가 차트**
- 🇰🇷 한국어 회사명(삼성전자, 카카오) 또는 종목코드(005930) 지원
- 🇺🇸 미국 티커(AAPL, NVDA) 또는 회사명(Apple) 지원
- 🤖 Claude AI가 최신 뉴스를 검색하고 한국어로 요약
"""
        )

        with gr.Row():
            with gr.Column(scale=3):
                query_input = gr.Textbox(
                    label="🔍 회사명 또는 종목코드",
                    placeholder="예: 삼성전자, AAPL, 005930, NVDA",
                    lines=1,
                )
            with gr.Column(scale=1):
                period_input = gr.Dropdown(
                    label="📅 기간",
                    choices=PERIOD_CHOICES,
                    value="3개월",
                )

        # API 키 입력 (Colab에서 환경 변수 미설정 시 사용)
        api_key_input = gr.Textbox(
            label="🔑 Anthropic API Key (선택 - 환경변수 미설정 시 입력)",
            placeholder="sk-ant-... (ANTHROPIC_API_KEY 환경변수가 있으면 비워두세요)",
            type="password",
            lines=1,
        )

        # 빠른 선택 버튼
        gr.Markdown("**빠른 선택:**")
        with gr.Row(elem_classes="quick-btn"):
            btns = []
            for pick in QUICK_PICKS:
                btn = gr.Button(pick, size="sm", variant="secondary")
                btns.append((btn, pick))

        search_btn = gr.Button("🚀 분석 시작", variant="primary", size="lg")

        # 출력 영역
        stock_info_md = gr.Markdown("### 검색 결과가 여기에 표시됩니다")
        chart_output = gr.Image(label="📊 주가 차트", type="filepath")
        news_output = gr.Markdown(label="📰 AI 뉴스 분석")

        # 이벤트 핸들러
        def on_search(q, period, api_key):
            img_b64, info, news = run_analysis(q, period, api_key)
            if img_b64:
                # base64를 임시 파일로 저장
                import tempfile, base64 as b64mod
                header, data = img_b64.split(",", 1)
                img_data = b64mod.b64decode(data)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    f.write(img_data)
                    return f.name, info, news
            return None, info, news

        search_btn.click(
            fn=on_search,
            inputs=[query_input, period_input, api_key_input],
            outputs=[chart_output, stock_info_md, news_output],
        )
        query_input.submit(
            fn=on_search,
            inputs=[query_input, period_input, api_key_input],
            outputs=[chart_output, stock_info_md, news_output],
        )

        # 빠른 선택 버튼 클릭 이벤트
        for btn, pick in btns:
            btn.click(
                fn=lambda q=pick, p=None, k=None: on_search(q, "3개월", ""),
                inputs=[],
                outputs=[chart_output, stock_info_md, news_output],
            )

    return demo


if __name__ == "__main__":
    app = create_app()
    app.launch(
        share=True,       # Colab용 공개 링크 생성
        server_port=7860,
        show_error=True,
    )
