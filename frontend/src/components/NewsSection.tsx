import { Newspaper, Bot, AlertCircle, ThumbsUp, ThumbsDown, Minus } from 'lucide-react'
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
  return (
    <div className="flex gap-3 p-4 bg-gray-800/40 hover:bg-gray-800/60 border border-gray-700/50 rounded-lg transition-colors">
      <div className="flex-shrink-0 w-8 h-8 bg-blue-900/40 border border-blue-800/50 rounded-lg flex items-center justify-center text-blue-400 text-sm font-bold">
        {index + 1}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          {item.title && (
            <h4 className="text-sm font-semibold text-gray-200 leading-snug">{item.title}</h4>
          )}
          {item.sentiment && <SentimentBadge sentiment={item.sentiment} />}
        </div>
        {item.content && (
          <p className="text-sm text-gray-400 leading-relaxed">{item.content}</p>
        )}
      </div>
    </div>
  )
}

function formatSummary(text: string): Array<{ type: 'heading' | 'text' | 'bullet'; content: string }> {
  const lines = text.split('\n').filter((l) => l.trim())
  return lines.map((line) => {
    const trimmed = line.trim()
    if (trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
      return { type: 'heading', content: trimmed.replace(/^#+\s*/, '').replace(/\*\*/g, '') }
    }
    if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
      return { type: 'heading', content: trimmed.replace(/\*\*/g, '') }
    }
    if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      return { type: 'bullet', content: trimmed.replace(/^[-•]\s*/, '').replace(/\*\*/g, '') }
    }
    return { type: 'text', content: trimmed.replace(/\*\*/g, '') }
  })
}

export default function NewsSection({ data }: NewsSectionProps) {
  const formattedLines = formatSummary(data.summary)

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-5">
        <div className="p-1.5 bg-purple-900/40 rounded-lg">
          <Bot className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-200">AI 뉴스 분석</h3>
          <p className="text-xs text-gray-500">Claude AI가 분석한 최신 뉴스 요약</p>
        </div>
        {data.note && (
          <div className="ml-auto flex items-center gap-1 text-xs text-yellow-400 bg-yellow-900/20 px-2 py-1 rounded-lg border border-yellow-800/40">
            <AlertCircle className="w-3 h-3" />
            {data.note}
          </div>
        )}
      </div>

      {/* Parsed news items */}
      {data.news_items && data.news_items.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <Newspaper className="w-4 h-4 text-blue-400" />
            <h4 className="text-sm font-medium text-gray-300">주요 뉴스</h4>
          </div>
          <div className="space-y-2">
            {data.news_items.map((item, i) => (
              <NewsItemCard key={i} item={item} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* Full AI summary */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Bot className="w-4 h-4 text-purple-400" />
          <h4 className="text-sm font-medium text-gray-300">상세 분석</h4>
        </div>
        <div className="prose prose-sm prose-invert max-w-none space-y-2">
          {formattedLines.map((line, i) => {
            if (line.type === 'heading') {
              return (
                <h4 key={i} className="text-sm font-semibold text-blue-300 mt-4 mb-1 first:mt-0">
                  {line.content}
                </h4>
              )
            }
            if (line.type === 'bullet') {
              return (
                <div key={i} className="flex gap-2 text-sm text-gray-400">
                  <span className="text-blue-500 flex-shrink-0 mt-0.5">•</span>
                  <span>{line.content}</span>
                </div>
              )
            }
            return (
              <p key={i} className="text-sm text-gray-400 leading-relaxed">
                {line.content}
              </p>
            )
          })}
        </div>
      </div>
    </div>
  )
}
