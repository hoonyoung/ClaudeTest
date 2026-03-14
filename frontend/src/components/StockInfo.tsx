import { TrendingUp, TrendingDown, Building2, Globe } from 'lucide-react'
import { StockData } from '../api'

interface StockInfoProps {
  data: StockData
}

function formatPrice(price: number, currency: string): string {
  if (currency === 'KRW') {
    return new Intl.NumberFormat('ko-KR').format(price) + '원'
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(price)
}

function formatMarketCap(cap: number, currency: string): string {
  if (currency === 'KRW') {
    const trillion = cap / 1_000_000_000_000
    return `${trillion.toFixed(1)}조원`
  }
  const billion = cap / 1_000_000_000
  if (billion >= 1000) {
    return `$${(billion / 1000).toFixed(1)}T`
  }
  return `$${billion.toFixed(1)}B`
}

export default function StockInfo({ data }: StockInfoProps) {
  const isPositive = data.change >= 0

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-2xl font-bold text-white">{data.name}</h2>
            <span className="px-2 py-0.5 bg-gray-800 text-gray-400 text-sm rounded border border-gray-700">
              {data.symbol}
            </span>
            <span className={`px-2 py-0.5 text-xs rounded border font-medium ${
              data.market === 'KR'
                ? 'bg-blue-900/40 text-blue-400 border-blue-800'
                : 'bg-purple-900/40 text-purple-400 border-purple-800'
            }`}>
              {data.market === 'KR' ? '🇰🇷 한국' : '🇺🇸 미국'}
            </span>
          </div>
          {data.sector && (
            <p className="text-sm text-gray-500 flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5" />
              {data.sector} · {data.industry}
            </p>
          )}
        </div>
        <Globe className="w-5 h-5 text-gray-600" />
      </div>

      <div className="flex items-end gap-4 mb-5">
        <span className="text-4xl font-bold text-white">
          {formatPrice(data.current_price, data.currency)}
        </span>
        <div className={`flex items-center gap-1 text-lg font-semibold pb-1 ${
          isPositive ? 'text-green-400' : 'text-red-400'
        }`}>
          {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
          <span>{isPositive ? '+' : ''}{formatPrice(data.change, data.currency)}</span>
          <span>({isPositive ? '+' : ''}{data.change_pct}%)</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {data.market_cap && (
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">시가총액</p>
            <p className="text-sm font-semibold text-gray-200">
              {formatMarketCap(data.market_cap, data.currency)}
            </p>
          </div>
        )}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">통화</p>
          <p className="text-sm font-semibold text-gray-200">{data.currency}</p>
        </div>
      </div>

      {data.description && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <p className="text-sm text-gray-400 leading-relaxed line-clamp-3">
            {data.description}
          </p>
        </div>
      )}
    </div>
  )
}
