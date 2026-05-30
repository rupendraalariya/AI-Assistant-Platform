import { Bot } from 'lucide-react'

export default function TypingIndicator() {
  return (
    <div className="flex gap-4 px-4 py-5 bg-cgpt-card/30">
      <div className="flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-accent-light flex items-center justify-center">
          <Bot className="h-5 w-5 text-white" />
        </div>
      </div>
      <div className="flex items-center gap-1.5 pt-2">
        <span className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}
