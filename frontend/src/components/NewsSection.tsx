import { Newspaper, ExternalLink, AlertCircle, ThumbsUp, ThumbsDown, Minus } from 'lucide-react'
import { NewsData, NewsItem } from '../api'

interface NewsSectionProps {
  data: NewsData
}

function SentimentBadge({ sentiment }: { sentiment?: string }) {
  if (sentiment === '긍정') {
    return (
      <span className="badge-positive flex items-center gap-1">
        <ThumbsUp className="w-3 h-3" />
        긍정
      </span>
    )
  }
  if (sentiment === '부정') {
    return (
      <span className="badge-negative flex items-center gap-1">
        <ThumbsDown className="w-3 h-3" />
        부정
      </span>
    )
  }
  return (
    <span className="badge-neutral flex items-center gap-1">
      <Minus className="w-3 h-3" />
      중립
    </span>
  )
}

function NewsItemCard({ item, index }: { item: NewsItem; index: number }) {
  const inner = (
    <div className="flex gap-3 p-4 bg-gray-800/40 hover:bg-gray-800/60 border border-gray-700/50 rounded-lg transition-colors">
      <div className="flex-shrink-0 w-8 h-8 bg-blue-900/40 border border-blue-800/50 rounded-lg flex items-center justify-center text-blue-400 text-sm font-bold">
        {index + 1}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h4 className="text-sm font-semibold text-gray-200 leading-snug">
            {item.title}
          </h4>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {item.sentiment && <SentimentBadge sentiment={item.sentiment} />}
            {item.link && <ExternalLink className="w-3.5 h-3.5 text-gray-500" />}
          </div>
        </div>
        {(item.source || item.date) && (
          <p className="text-xs text-gray-500">
            {item.source}{item.source && item.date ? '  ' : ''}{item.date}
          </p>
        )}
      </div>
    </div>
  )

  if (item.link) {
    return (
      <a href={item.link} target="_blank" rel="noopener noreferrer" className="block">
        {inner}
      </a>
    )
  }
  return <div>{inner}</div>
}

export default function NewsSection({ data }: NewsSectionProps) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-5">
        <div className="p-1.5 bg-blue-900/40 rounded-lg">
          <Newspaper className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-200">주요 뉴스</h3>
          <p className="text-xs text-gray-500">{data.company_name} 최신 뉴스</p>
        </div>
        {data.note && (
          <div className="ml-auto flex items-center gap-1 text-xs text-yellow-400 bg-yellow-900/20 px-2 py-1 rounded-lg border border-yellow-800/40">
            <AlertCircle className="w-3 h-3" />
            {data.note}
          </div>
        )}
      </div>

      {data.news_items && data.news_items.length > 0 ? (
        <div className="space-y-2">
          {data.news_items.map((item, i) => (
            <NewsItemCard key={i} item={item} index={i} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500">뉴스를 불러오지 못했습니다.</p>
      )}
    </div>
  )
}
