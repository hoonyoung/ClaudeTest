import { TrendingUp, TrendingDown, Activity, Loader2 } from 'lucide-react'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { WeeklySentimentData, WeeklyDay } from '../api'

interface SentimentTrendChartProps {
  data: WeeklySentimentData | null
  isLoading: boolean
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

interface TooltipPayload {
  color: string
  name: string
  value: number
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: TooltipPayload[]
  label?: string
}) {
  if (!active || !payload || !payload.length) return null
  return (
    <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-gray-300 font-medium mb-2">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 mb-1">
          <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: entry.color }} />
          <span className="text-gray-400">{entry.name}:</span>
          <span className="text-white font-medium">
            {entry.name === '감성 점수' ? (entry.value > 0 ? `+${entry.value}` : entry.value) : `${entry.value}%`}
          </span>
        </div>
      ))}
    </div>
  )
}

function WeeklySummary({ days }: { days: WeeklyDay[] }) {
  const activeDays = days.filter((d) => d.total > 0)
  if (activeDays.length === 0) return null

  const totalComments = activeDays.reduce((s, d) => s + d.total, 0)
  const avgScore = Math.round(activeDays.reduce((s, d) => s + d.sentiment_score, 0) / activeDays.length)
  const avgBullish = Math.round(activeDays.reduce((s, d) => s + d.bullish_pct, 0) / activeDays.length)
  const avgBearish = Math.round(activeDays.reduce((s, d) => s + d.bearish_pct, 0) / activeDays.length)

  return (
    <div className="grid grid-cols-4 gap-3 mb-5">
      {[
        { label: '분석 댓글 수', value: totalComments.toLocaleString(), color: 'text-blue-400' },
        { label: '주간 평균 감성', value: avgScore > 0 ? `+${avgScore}` : `${avgScore}`, color: avgScore > 0 ? 'text-green-400' : avgScore < 0 ? 'text-red-400' : 'text-gray-400' },
        { label: '평균 긍정', value: `${avgBullish}%`, color: 'text-green-400' },
        { label: '평균 부정', value: `${avgBearish}%`, color: 'text-red-400' },
      ].map(({ label, value, color }) => (
        <div key={label} className="p-3 bg-gray-800/40 rounded-lg border border-gray-700/50 text-center">
          <p className="text-xs text-gray-500 mb-1">{label}</p>
          <p className={`text-lg font-bold ${color}`}>{value}</p>
        </div>
      ))}
    </div>
  )
}

export default function SentimentTrendChart({ data, isLoading }: SentimentTrendChartProps) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-5">
        <div className="p-1.5 bg-purple-900/40 rounded-lg">
          <Activity className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-200">주간 감성 트렌드</h3>
          <p className="text-xs text-gray-500">최근 7일 · 일별 긍부정 댓글 분석 (일 최대 500개)</p>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-16 gap-3 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">주간 댓글 데이터 수집 중...</span>
        </div>
      )}

      {!isLoading && !data && (
        <p className="text-sm text-gray-500 text-center py-10">감성 트렌드 데이터를 불러올 수 없습니다.</p>
      )}

      {!isLoading && data && (
        <>
          <WeeklySummary days={data.days} />

          {/* Stacked bar chart: bullish / neutral / bearish % */}
          <div className="mb-2">
            <p className="text-xs text-gray-500 mb-2">일별 감성 비율 (%)</p>
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={data.days.map((d) => ({ ...d, date: formatDate(d.date) }))} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{ fontSize: '11px', color: '#9ca3af', paddingTop: '8px' }}
                  formatter={(value) => <span style={{ color: '#d1d5db' }}>{value}</span>}
                />
                <Bar dataKey="bullish_pct" name="긍정 %" stackId="a" fill="#16a34a" radius={[0, 0, 0, 0]} />
                <Bar dataKey="neutral_pct" name="중립 %" stackId="a" fill="#4b5563" radius={[0, 0, 0, 0]} />
                <Bar dataKey="bearish_pct" name="부정 %" stackId="a" fill="#dc2626" radius={[4, 4, 0, 0]} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Line chart: sentiment score */}
          <div>
            <p className="text-xs text-gray-500 mb-2">일별 감성 점수 (긍정% − 부정%)</p>
            <ResponsiveContainer width="100%" height={160}>
              <ComposedChart data={data.days.map((d) => ({ ...d, date: formatDate(d.date) }))} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[-100, 100]} tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="4 4" />
                <Line
                  type="monotone"
                  dataKey="sentiment_score"
                  name="감성 점수"
                  stroke="#a78bfa"
                  strokeWidth={2.5}
                  dot={(props) => {
                    const { cx, cy, payload } = props
                    const color = payload.sentiment_score > 0 ? '#4ade80' : payload.sentiment_score < 0 ? '#f87171' : '#9ca3af'
                    return <circle key={`dot-${cx}-${cy}`} cx={cx} cy={cy} r={4} fill={color} stroke="#1f2937" strokeWidth={1.5} />
                  }}
                  activeDot={{ r: 6, stroke: '#a78bfa', strokeWidth: 2 }}
                  connectNulls={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* No-data notice */}
          {data.days.every((d) => d.total === 0) && (
            <div className="flex items-center gap-2 mt-4 p-3 bg-yellow-900/20 border border-yellow-800/40 rounded-lg">
              <TrendingUp className="w-4 h-4 text-yellow-500 flex-shrink-0" />
              <p className="text-xs text-yellow-400">
                최근 7일 내 날짜가 기록된 댓글이 없습니다. 전체 수집 댓글은 투자자 댓글 섹션에서 확인하세요.
              </p>
            </div>
          )}

          <div className="flex items-center gap-4 mt-3 text-xs text-gray-600">
            <span className="flex items-center gap-1"><TrendingUp className="w-3 h-3 text-green-600" />긍정 우세</span>
            <span className="flex items-center gap-1"><TrendingDown className="w-3 h-3 text-red-600" />부정 우세</span>
            <span className="text-gray-700">· 감성 점수 = 긍정% − 부정%</span>
          </div>
        </>
      )}
    </div>
  )
}
