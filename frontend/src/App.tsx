import { useState, useCallback } from 'react'
import { BarChart3, AlertCircle, Loader2 } from 'lucide-react'
import SearchBar from './components/SearchBar'
import StockInfo from './components/StockInfo'
import StockChart from './components/StockChart'
import NewsSection from './components/NewsSection'
import CommentsSection from './components/CommentsSection'
import { searchCompany, getStockData, getComments, SearchResult, CommentsData } from './api'

export default function App() {
  const [result, setResult] = useState<SearchResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isUpdatingChart, setIsUpdatingChart] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPeriod, setCurrentPeriod] = useState('3mo')
  const [comments, setComments] = useState<CommentsData | null>(null)
  const [isLoadingComments, setIsLoadingComments] = useState(false)

  const handleSearch = useCallback(async (query: string, period: string) => {
    setIsLoading(true)
    setError(null)
    setCurrentPeriod(period)
    setComments(null)

    try {
      const data = await searchCompany(query, period)
      setResult(data)

      // 댓글은 별도로 비동기 로드
      setIsLoadingComments(true)
      getComments(data.resolved_symbol, data.stock.market)
        .then(setComments)
        .catch(() => setComments(null))
        .finally(() => setIsLoadingComments(false))
    } catch (err) {
      const message = err instanceof Error ? err.message : '검색 중 오류가 발생했습니다'
      if (message.includes('404')) {
        setError(`"${query}"에 해당하는 주식 정보를 찾을 수 없습니다. 정확한 종목명 또는 종목코드를 입력해주세요.`)
      } else {
        setError(message)
      }
      setResult(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handlePeriodChange = useCallback(async (period: string) => {
    if (!result) return
    setIsUpdatingChart(true)
    setCurrentPeriod(period)

    try {
      const stockData = await getStockData(result.resolved_symbol, period)
      setResult((prev) => prev ? { ...prev, stock: stockData } : null)
    } catch (err) {
      console.error('Failed to update chart period:', err)
    } finally {
      setIsUpdatingChart(false)
    }
  }, [result])

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-xl">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">주식 시장 분석기</h1>
            <p className="text-xs text-gray-500">한국 · 미국 주식 뉴스 분석 & 주가 차트</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Search */}
        <div className="mb-10">
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-blue-900 border-t-blue-500 rounded-full animate-spin" />
              <BarChart3 className="w-6 h-6 text-blue-400 absolute inset-0 m-auto" />
            </div>
            <p className="text-gray-400 text-sm">주식 데이터와 AI 뉴스 분석을 가져오는 중...</p>
            <p className="text-gray-600 text-xs">30-60초 소요될 수 있습니다</p>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="max-w-2xl mx-auto">
            <div className="flex gap-3 p-4 bg-red-900/20 border border-red-800/50 rounded-xl text-red-300">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-400" />
              <div>
                <p className="font-medium text-red-300">검색 오류</p>
                <p className="text-sm text-red-400/80 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && !isLoading && (
          <div className="space-y-6">
            {/* Stock info */}
            <StockInfo data={result.stock} />

            {/* Chart */}
            <div className="relative">
              {isUpdatingChart && (
                <div className="absolute inset-0 bg-gray-950/70 rounded-xl flex items-center justify-center z-10">
                  <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                </div>
              )}
              <StockChart
                data={result.stock}
                onPeriodChange={handlePeriodChange}
                currentPeriod={currentPeriod}
              />
            </div>

            {/* News */}
            <NewsSection data={result.news} />

            {/* Comments */}
            <CommentsSection data={comments} isLoading={isLoadingComments} />
          </div>
        )}

        {/* Empty state */}
        {!result && !isLoading && !error && (
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <div className="p-5 bg-gray-800/50 rounded-2xl border border-gray-700/50">
              <BarChart3 className="w-12 h-12 text-gray-600 mx-auto" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-400 mb-2">
                주식 정보를 검색해보세요
              </h2>
              <p className="text-sm text-gray-600 max-w-md">
                한국(삼성전자, 네이버, 카카오 등) 또는 미국(AAPL, MSFT, NVDA 등) 주식의
                최신 뉴스와 주가 차트를 AI로 분석해드립니다.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 mt-2 text-sm text-left max-w-sm">
              <div className="p-3 bg-gray-800/40 rounded-lg border border-gray-700/40">
                <p className="text-blue-400 font-medium mb-1">🇰🇷 한국 주식</p>
                <p className="text-gray-500 text-xs">삼성전자, 현대차, SK하이닉스, 카카오, 네이버 등</p>
              </div>
              <div className="p-3 bg-gray-800/40 rounded-lg border border-gray-700/40">
                <p className="text-purple-400 font-medium mb-1">🇺🇸 미국 주식</p>
                <p className="text-gray-500 text-xs">AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA 등</p>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-gray-800 mt-20 py-6 text-center text-xs text-gray-600">
        <p>주식 시장 분석기 · AI 뉴스 분석은 Claude AI 제공 · 투자 조언이 아닙니다</p>
      </footer>
    </div>
  )
}
