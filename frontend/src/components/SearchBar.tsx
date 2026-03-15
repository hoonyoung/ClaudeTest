import { useState, useRef, FormEvent } from 'react'
import { Search, TrendingUp } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string, period: string) => void
  isLoading: boolean
}

const SUGGESTIONS = [
  { label: '삼성전자', desc: '한국 반도체/전자' },
  { label: '네이버', desc: '한국 인터넷' },
  { label: '카카오', desc: '한국 IT' },
  { label: 'Apple', desc: '미국 기술주 (AAPL)' },
  { label: 'TSMC', desc: '대만 반도체 (TSM)' },
  { label: 'NVDA', desc: '엔비디아' },
  { label: 'MSFT', desc: '마이크로소프트' },
]

const PERIODS = [
  { value: '1mo', label: '1개월' },
  { value: '3mo', label: '3개월' },
  { value: '6mo', label: '6개월' },
  { value: '1y', label: '1년' },
  { value: '2y', label: '2년' },
]

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [period, setPeriod] = useState('3mo')
  const isComposingRef = useRef(false)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (isComposingRef.current) return
    if (query.trim()) {
      onSearch(query.trim(), period)
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-5 h-5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onCompositionStart={() => { isComposingRef.current = true }}
            onCompositionEnd={(e) => {
              isComposingRef.current = false
              setQuery((e.target as HTMLInputElement).value)
            }}
            placeholder="회사명 또는 종목코드 입력 (예: 삼성전자, AAPL, 005930)"
            className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            disabled={isLoading}
          />
        </div>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="px-3 py-3 bg-gray-800 border border-gray-700 rounded-xl text-gray-300 focus:outline-none focus:border-blue-500 cursor-pointer"
          disabled={isLoading}
        >
          {PERIODS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Search className="w-5 h-5" />
          )}
          검색
        </button>
      </form>

      {/* Quick suggestions */}
      <div className="mt-3 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.label}
            onClick={() => {
              setQuery(s.label)
              onSearch(s.label, period)
            }}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800/60 hover:bg-gray-700 border border-gray-700/50 rounded-lg text-sm text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-50"
          >
            <TrendingUp className="w-3.5 h-3.5 text-blue-400" />
            <span>{s.label}</span>
            <span className="text-gray-600 text-xs">{s.desc}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
