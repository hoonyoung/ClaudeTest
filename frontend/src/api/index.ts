import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export interface PricePoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface StockData {
  symbol: string
  name: string
  market: 'US' | 'KR'
  currency: string
  current_price: number
  change: number
  change_pct: number
  market_cap?: number
  sector?: string
  industry?: string
  description?: string
  prices: PricePoint[]
}

export interface NewsItem {
  title?: string
  link?: string
  date?: string
  source?: string
  sentiment?: '긍정' | '부정' | '중립'
}

export interface NewsData {
  news_items: NewsItem[]
  company_name: string
  company_symbol: string
  note?: string
}

export interface SearchResult {
  stock: StockData
  news: NewsData
  query: string
  resolved_symbol: string
}

export async function searchCompany(query: string, period: string = '3mo'): Promise<SearchResult> {
  const response = await api.get<SearchResult>('/search', {
    params: { q: query, period },
  })
  return response.data
}

export async function getStockData(symbol: string, period: string = '3mo'): Promise<StockData> {
  const response = await api.get<StockData>(`/stock/${symbol}`, {
    params: { period },
  })
  return response.data
}

export interface Comment {
  id: string
  author: string
  content: string
  date: string
  likes: number
  dislikes: number
  views: number
  sentiment: '긍정' | '부정' | '중립'
  source: string
}

export interface SentimentSummary {
  bullish: number
  bearish: number
  neutral: number
  bullish_pct: number
  bearish_pct: number
  neutral_pct: number
  total: number
}

export interface CommentsData {
  comments: Comment[]
  total: number
  sentiment_summary: SentimentSummary
  symbol: string
  market: string
}

export async function getComments(symbol: string, market: string): Promise<CommentsData> {
  const response = await api.get<CommentsData>(`/comments/${symbol}`, {
    params: { market },
  })
  return response.data
}

export interface WeeklyDay {
  date: string
  total: number
  bullish: number
  bearish: number
  neutral: number
  bullish_pct: number
  bearish_pct: number
  neutral_pct: number
  sentiment_score: number
}

export interface WeeklySentimentData {
  symbol: string
  market: string
  days: WeeklyDay[]
  daily_limit: number
}

export async function getWeeklySentiment(
  symbol: string,
  market: string,
  dailyLimit: number = 500,
): Promise<WeeklySentimentData> {
  const response = await api.get<WeeklySentimentData>(`/comments/${symbol}/weekly`, {
    params: { market, daily_limit: dailyLimit },
  })
  return response.data
}
