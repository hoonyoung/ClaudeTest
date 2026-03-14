# 주식 시장 분석기 (Stock Market Analyzer)

한국 및 미국 주식 시장의 기업 정보를 검색하여 **최신 뉴스 AI 요약**과 **주가 차트**를 제공하는 웹 애플리케이션입니다.

## 주요 기능

- 🔍 **기업 검색**: 한국어 회사명, 영어 회사명, 또는 종목코드로 검색
- 📈 **주가 차트**: 라인 차트 / OHLC 차트, 1개월~2년 기간 선택
- 📰 **AI 뉴스 분석**: Claude AI가 최신 뉴스를 검색하고 한국어로 요약
- 🇰🇷 **한국 주식**: KOSPI/KOSDAQ 전체 종목 지원 (pykrx)
- 🇺🇸 **미국 주식**: NYSE/NASDAQ 전체 종목 지원 (yfinance)

## 기술 스택

### 백엔드
- **FastAPI** - Python 웹 프레임워크
- **yfinance** - 미국 주식 데이터
- **pykrx** - 한국 주식 데이터 (한국거래소 API)
- **Anthropic Claude API** - AI 뉴스 검색 및 요약 (claude-opus-4-6)

### 프론트엔드
- **React + TypeScript** - UI 프레임워크
- **Vite** - 빌드 도구
- **Recharts** - 주가 차트
- **Tailwind CSS** - 스타일링

## 설치 및 실행

### 사전 요구사항
- Python 3.10+
- Node.js 18+
- Anthropic API 키

### 백엔드 설정

```bash
cd backend

# 가상환경 생성 (선택)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력

# 서버 실행
python main.py
# 또는
uvicorn main:app --reload --port 8000
```

### 프론트엔드 설정

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 접속
- 프론트엔드: http://localhost:5173
- API 문서: http://localhost:8000/docs

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/search?q={회사명}&period={기간}` | 회사 검색 (주가+뉴스) |
| GET | `/api/stock/{symbol}?period={기간}` | 주가 데이터만 조회 |
| GET | `/api/news/{symbol}?company_name={이름}&market={KR\|US}` | 뉴스만 조회 |

## 검색 예시

- **한국 주식**: `삼성전자`, `삼성`, `네이버`, `카카오`, `현대차`, `SK하이닉스`
- **미국 주식**: `AAPL`, `Apple`, `NVDA`, `MSFT`, `TSLA`, `GOOGL`
- **종목코드**: `005930` (삼성전자), `000660` (SK하이닉스)

## 환경 변수

| 변수명 | 설명 |
|--------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 키 (필수) |

## 주의사항

- 투자 정보 제공 목적이 아닙니다. 참고 자료로만 활용하세요.
- Claude AI 뉴스 분석은 실시간 웹 검색을 사용하며, 검색 불가 시 학습 데이터 기반으로 분석합니다.
- 한국 주식 데이터는 한국거래소(KRX) 공개 데이터를 사용합니다.
