import { useState, useRef, useEffect } from 'react'
import { useChatStore } from '../store/chatStore'
import { Send, Paperclip, Square } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ChatInput() {
  const [message, setMessage] = useState('')
  const [useRag, setUseRag] = useState(false)
  const { streamMessage, isStreaming } = useChatStore()
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [message])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || isStreaming) return
    const text = message.trim()
    setMessage('')
    try {
      await streamMessage(text)
    } catch {
      toast.error('Failed to send message')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="border-t border-cgpt-border bg-cgpt-bg px-4 py-4">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2 bg-cgpt-input border border-cgpt-border rounded-2xl px-3 py-2 focus-within:ring-2 focus-within:ring-accent/50 transition-all">
          {/* RAG toggle */}
          <button
            type="button"
            onClick={() => setUseRag(!useRag)}
            title="Use document context (RAG)"
            className={`flex-shrink-0 p-2 rounded-lg transition-colors ${
              useRag ? 'bg-accent/15 text-accent' : 'text-cgpt-muted hover:bg-cgpt-hover'
            }`}
          >
            <Paperclip className="h-5 w-5" />
          </button>

          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message AI Assistant..."
            rows={1}
            className="flex-1 resize-none bg-transparent text-cgpt-text placeholder-cgpt-muted outline-none py-2 max-h-[200px]"
            disabled={isStreaming}
          />

          <button
            type="submit"
            disabled={!message.trim() || isStreaming}
            className="flex-shrink-0 p-2 rounded-lg bg-accent hover:bg-accent-hover text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Send message"
          >
            {isStreaming ? <Square className="h-5 w-5" /> : <Send className="h-5 w-5" />}
          </button>
        </div>

        <p className="text-xs text-cgpt-muted mt-2 text-center">
          {useRag && <span className="text-accent">RAG enabled · </span>}
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </div>
  )
}
