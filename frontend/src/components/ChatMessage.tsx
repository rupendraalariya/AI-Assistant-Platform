import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Bot, User, Copy, Check, Pencil, Trash2, RefreshCw,
  ThumbsUp, ThumbsDown, Share2, X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import MarkdownRenderer from './MarkdownRenderer'
import { useChatStore, type Message } from '../store/chatStore'

interface ChatMessageProps {
  message: Message
  isLast: boolean
  isStreaming: boolean
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: 'bg-emerald-500/15 text-emerald-400',
  gemini: 'bg-blue-500/15 text-blue-400',
  claude: 'bg-orange-500/15 text-orange-400',
  groq: 'bg-red-500/15 text-red-400',
  deepseek: 'bg-purple-500/15 text-purple-400',
  mistral: 'bg-amber-500/15 text-amber-400',
  together: 'bg-pink-500/15 text-pink-400',
  ollama: 'bg-gray-500/15 text-gray-400',
}

export default function ChatMessage({ message, isLast, isStreaming }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const { deleteMessage, editUserMessage, regenerateLast, setReaction } = useChatStore()

  const [copied, setCopied] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(message.content)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    toast.success(isUser ? 'Message copied' : 'Response copied')
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSaveEdit = () => {
    if (editValue.trim() && editValue !== message.content) {
      editUserMessage(message.id, editValue.trim())
    }
    setEditing(false)
  }

  const handleShare = async () => {
    const shareData = { title: 'AI Response', text: message.content }
    if (navigator.share) {
      try {
        await navigator.share(shareData)
      } catch {
        /* user cancelled */
      }
    } else {
      await navigator.clipboard.writeText(message.content)
      toast.success('Response copied to share')
    }
  }

  const showStreamingCursor = !isUser && isLast && isStreaming

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`group flex gap-4 px-4 py-5 ${isUser ? '' : 'bg-cgpt-card/30'}`}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center">
            <User className="h-5 w-5 text-white" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-accent-light flex items-center justify-center">
            <Bot className="h-5 w-5 text-white" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-semibold text-cgpt-text">
            {isUser ? 'You' : 'Assistant'}
          </span>
          {!isUser && message.provider && message.provider !== 'none' && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PROVIDER_COLORS[message.provider] || 'bg-gray-500/15 text-gray-400'}`}>
              {message.provider}{message.model ? ` · ${message.model}` : ''}
            </span>
          )}
        </div>

        {/* Editing mode for user messages */}
        {editing ? (
          <div className="space-y-2">
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="input-field min-h-[80px] resize-y"
              autoFocus
            />
            <div className="flex gap-2">
              <button onClick={handleSaveEdit} className="btn-primary text-xs py-1.5 px-3">
                Save &amp; Submit
              </button>
              <button
                onClick={() => { setEditing(false); setEditValue(message.content) }}
                className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
              >
                <X className="h-3 w-3" /> Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="text-cgpt-text">
            {isUser ? (
              <p className="whitespace-pre-wrap leading-7">{message.content}</p>
            ) : (
              <>
                <MarkdownRenderer content={message.content} />
                {showStreamingCursor && (
                  <span className="inline-block w-2 h-4 bg-accent animate-blink align-middle ml-0.5" />
                )}
              </>
            )}
          </div>
        )}

        {/* Action toolbar */}
        {!editing && (
          <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button onClick={handleCopy} className="icon-btn" title="Copy" aria-label="Copy">
              {copied ? <Check className="h-4 w-4 text-accent" /> : <Copy className="h-4 w-4" />}
            </button>

            {isUser ? (
              <>
                <button onClick={() => setEditing(true)} className="icon-btn" title="Edit" aria-label="Edit message">
                  <Pencil className="h-4 w-4" />
                </button>
                <button onClick={() => deleteMessage(message.id)} className="icon-btn hover:text-error" title="Delete" aria-label="Delete message">
                  <Trash2 className="h-4 w-4" />
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => regenerateLast()}
                  className="icon-btn"
                  title="Regenerate"
                  aria-label="Regenerate response"
                  disabled={isStreaming}
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setReaction(message.id, 'like')}
                  className={`icon-btn ${message.reaction === 'like' ? 'text-accent' : ''}`}
                  title="Like"
                  aria-label="Like"
                >
                  <ThumbsUp className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setReaction(message.id, 'dislike')}
                  className={`icon-btn ${message.reaction === 'dislike' ? 'text-error' : ''}`}
                  title="Dislike"
                  aria-label="Dislike"
                >
                  <ThumbsDown className="h-4 w-4" />
                </button>
                <button onClick={handleShare} className="icon-btn" title="Share" aria-label="Share">
                  <Share2 className="h-4 w-4" />
                </button>
                {message.tokens_used ? (
                  <span className="text-xs text-cgpt-muted ml-2">
                    {message.tokens_used} tokens{message.latency_ms ? ` · ${message.latency_ms}ms` : ''}
                  </span>
                ) : null}
              </>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}
