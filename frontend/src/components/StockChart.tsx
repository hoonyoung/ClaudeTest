import { useState, useMemo } from 'react'
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts'
import { PricePoint, StockData } from '../api'

interface StockChartProps {
  data: StockData
  onPeriodChange: (period: string) => void
  currentPeriod: string
}

const PERIODS = [
  { value: '1mo', label: '1M' },
  { value: '3mo', label: '3M' },
  { value: '6mo', label: '6M' },
  { value: '1y', label: '1Y' },
  { value: '2y', label: '2Y' },
]

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ value: number; name: string; color: string }>
  label?: string
  currency: string
}

function CustomTooltip({ active, payload, label, currency }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null

  const formatValue = (val: number) => {
    if (currency === 'KRW') {
      return new Intl.NumberFormat('ko-KR').format(val) + '원'
    }
    return '$' + val.toFixed(2)
  }

  const formatVolume = (val: number) => {
    if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + 'M'
    if (val >= 1_000) return (val / 1_000).toFixed(1) + 'K'
    return val.toString()
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm shadow-xl">
      <p className="text-gray-400 mb-2 font-medium">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex justify-between gap-4">
          <span className="text-gray-400">{p.name}</span>
          <span className="font-medium" style={{ color: p.color }}>
            {p.name === '거래량' ? formatVolume(p.value) : formatValue(p.value)}
          </span>
        </div>
      ))}
    </div>
  )
}

function formatXAxis(dateStr: string, period: string): string {
  const date = new Date(dateStr)
  if (period === '1mo') {
    return `${date.getMonth() + 1}/${date.getDate()}`
  }
  if (period === '3mo' || period === '6mo') {
    return `${date.getMonth() + 1}/${date.getDate()}`
  }
  return `${date.getFullYear()}.${date.getMonth() + 1}`
}

function formatYAxis(value: number, currency: string): string {
  if (currency === 'KRW') {
    if (value >= 1_000_000) return (value / 1_000_000).toFixed(0) + 'M'
    if (value >= 1_000) return (value / 1_000).toFixed(0) + 'K'
    return value.toString()
  }
  if (value >= 1000) return '$' + (value / 1000).toFixed(1) + 'K'
  return '$' + value.toFixed(0)
}

export default function StockChart({ data, onPeriodChange, currentPeriod }: StockChartProps) {
  const [chartType, setChartType] = useState<'line' | 'candle'>('line')

  const chartData = useMemo(() => {
    return data.prices.map((p: PricePoint) => ({
      ...p,
      label: formatXAxis(p.date, currentPeriod),
    }))
  }, [data.prices, currentPeriod])

  const isPositive = data.change >= 0
  const lineColor = isPositive ? '#22c55e' : '#ef4444'

  const minPrice = Math.min(...data.prices.map((p) => p.low))
  const maxPrice = Math.max(...data.prices.map((p) => p.high))
  const pricePadding = (maxPrice - minPrice) * 0.05
  const firstPrice = data.prices[0]?.close ?? 0

  return (
    <div className="card">
      {/* Chart header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-200">주가 차트</h3>
        <div className="flex items-center gap-3">
          {/* Chart type toggle */}
          <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
            <button
              onClick={() => setChartType('line')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                chartType === 'line'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              라인
            </button>
            <button
              onClick={() => setChartType('candle')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                chartType === 'candle'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              OHLC
            </button>
          </div>
          {/* Period selector */}
          <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => onPeriodChange(p.value)}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  currentPeriod === p.value
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Price chart */}
      <div className="h-64 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[minPrice - pricePadding, maxPrice + pricePadding]}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => formatYAxis(v, data.currency)}
              width={60}
            />
            <Tooltip
              content={<CustomTooltip currency={data.currency} />}
              cursor={{ stroke: '#374151', strokeWidth: 1 }}
            />
            <ReferenceLine
              y={firstPrice}
              stroke="#374151"
              strokeDasharray="4 4"
              strokeWidth={1}
            />
            {chartType === 'line' ? (
              <Line
                type="monotone"
                dataKey="close"
                stroke={lineColor}
                strokeWidth={2}
                dot={false}
                name="종가"
                activeDot={{ r: 4, fill: lineColor }}
              />
            ) : (
              <>
                <Line
                  type="monotone"
                  dataKey="high"
                  stroke="#22c55e"
                  strokeWidth={1.5}
                  dot={false}
                  name="고가"
                />
                <Line
                  type="monotone"
                  dataKey="low"
                  stroke="#ef4444"
                  strokeWidth={1.5}
                  dot={false}
                  name="저가"
                />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="#60a5fa"
                  strokeWidth={2}
                  dot={false}
                  name="종가"
                />
                <Line
                  type="monotone"
                  dataKey="open"
                  stroke="#f59e0b"
                  strokeWidth={1.5}
                  dot={false}
                  name="시가"
                />
                <Legend
                  iconType="line"
                  wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }}
                />
              </>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Volume chart */}
      <div className="h-20">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 0, right: 5, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
            <XAxis dataKey="label" hide />
            <YAxis
              tick={{ fill: '#6b7280', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => {
                if (v >= 1_000_000) return (v / 1_000_000).toFixed(0) + 'M'
                if (v >= 1_000) return (v / 1_000).toFixed(0) + 'K'
                return String(v)
              }}
              width={60}
            />
            <Tooltip
              content={<CustomTooltip currency={data.currency} />}
              cursor={{ stroke: '#374151', strokeWidth: 1 }}
            />
            <Bar dataKey="volume" fill="#3b82f620" stroke="#3b82f640" name="거래량" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-gray-600 text-center mt-1">거래량</p>
    </div>
  )
}
