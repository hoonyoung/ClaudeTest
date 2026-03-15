import { MessageSquare, ThumbsUp, ThumbsDown, Minus, TrendingUp, TrendingDown, Loader2 } from 'lucide-react'
import { CommentsData, Comment } from '../api'

interface CommentsSectionProps {
  data: CommentsData | null
  isLoading: boolean
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  if (sentiment === '긍정') {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-green-900/40 text-green-400 border border-green-800/50">
        <ThumbsUp className="w-3 h-3" />긍정
      </span>
    )
  }
  if (sentiment === '부정') {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-red-900/40 text-red-400 border border-red-800/50">
        <ThumbsDown className="w-3 h-3" />부정
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-gray-800/60 text-gray-400 border border-gray-700/50">
      <Minus className="w-3 h-3" />중립
    </span>
  )
}

function CommentCard({ comment }: { comment: Comment }) {
  return (
    <div className="p-3 bg-gray-800/40 hover:bg-gray-800/60 border border-gray-700/50 rounded-lg transition-colors">
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-medium text-blue-400 truncate">{comment.author}</span>
          <span className="text-xs text-gray-600 flex-shrink-0">{comment.date}</span>
          <span className="text-xs text-gray-700 flex-shrink-0">· {comment.source}</span>
        </div>
        <SentimentBadge sentiment={comment.sentiment} />
      </div>
      <p className="text-sm text-gray-300 leading-relaxed break-words">{comment.content}</p>
      {comment.likes > 0 && (
        <div className="flex items-center gap-3 mt-2 text-xs text-gray-600">
          <span className="flex items-center gap-1">
            <ThumbsUp className="w-3 h-3" />{comment.likes}
          </span>
          {comment.views > 0 && <span>조회 {comment.views}</span>}
        </div>
      )}
    </div>
  )
}

function SentimentBar({ data }: { data: CommentsData }) {
  const { bullish_pct, bearish_pct, neutral_pct, bullish, bearish, neutral } = data.sentiment_summary
  return (
    <div className="p-4 bg-gray-800/30 border border-gray-700/50 rounded-xl mb-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-300">투자자 심리</h4>
        <span className="text-xs text-gray-500">총 {data.total}개 댓글 분석</span>
      </div>
      {/* Bar */}
      <div className="flex rounded-full overflow-hidden h-3 mb-3">
        {bullish_pct > 0 && (
          <div className="bg-green-600 transition-all" style={{ width: `${bullish_pct}%` }} />
        )}
        {neutral_pct > 0 && (
          <div className="bg-gray-600 transition-all" style={{ width: `${neutral_pct}%` }} />
        )}
        {bearish_pct > 0 && (
          <div className="bg-red-600 transition-all" style={{ width: `${bearish_pct}%` }} />
        )}
      </div>
      <div className="flex justify-between text-xs">
        <div className="flex items-center gap-1.5 text-green-400">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>긍정 {bullish_pct}% ({bullish})</span>
        </div>
        <div className="text-gray-500">중립 {neutral_pct}% ({neutral})</div>
        <div className="flex items-center gap-1.5 text-red-400">
          <TrendingDown className="w-3.5 h-3.5" />
          <span>부정 {bearish_pct}% ({bearish})</span>
        </div>
      </div>
    </div>
  )
}

export default function CommentsSection({ data, isLoading }: CommentsSectionProps) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-5">
        <div className="p-1.5 bg-orange-900/40 rounded-lg">
          <MessageSquare className="w-5 h-5 text-orange-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-200">투자자 댓글</h3>
          <p className="text-xs text-gray-500">실시간 투자자 반응 · 감성 분석</p>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12 gap-3 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">댓글 수집 중...</span>
        </div>
      )}

      {!isLoading && !data && (
        <p className="text-sm text-gray-500 text-center py-8">댓글을 불러올 수 없습니다.</p>
      )}

      {!isLoading && data && (
        <>
          <SentimentBar data={data} />
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {data.comments.map((comment, i) => (
              <CommentCard key={comment.id || i} comment={comment} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
