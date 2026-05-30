import { useEffect, useRef, useState } from 'react'
import { Bot, Sparkles, Code2, FileText, Lightbulb } from 'lucide-react'
import { useChatStore } from '../store/chatStore'
import { useAuthStore } from '../store/authStore'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'
import Header from '../components/Header'
import CompareMode from '../components/CompareMode'
import TypingIndicator from '../components/TypingIndicator'

const SUGGESTIONS = [
  { icon: Lightbulb, text: 'Explain quantum computing in simple terms' },
  { icon: Code2, text: 'Write a Python function to sort a list' },
  { icon: FileText, text: 'Summarize the key points of RAG systems' },
  { icon: Sparkles, text: 'Give me creative startup ideas for 2026' },
]

export default function ChatPage() {
  const {
    messages, isStreaming, isLoadingMessages,
    loadSessions, loadMessages, streamMessage,
  } = useChatStore()
  const { loadUser } = useAuthStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [compareMode, setCompareMode] = useState(false)

  useEffect(() => {
    loadUser()
    loadSessions()
    // Reopen last session after refresh (persisted in localStorage)
    const lastSession = localStorage.getItem('last_session_id')
    if (lastSession) {
      loadMessages(lastSession)
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const lastIsUser = messages.length > 0 && messages[messages.length - 1].role === 'user'

  return (
    <div className="flex h-screen overflow-hidden bg-cgpt-bg">
      <Sidebar isOpen={sidebarOpen} />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onToggleCompare={() => setCompareMode(!compareMode)}
          compareMode={compareMode}
        />

        {compareMode ? (
          <CompareMode />
        ) : (
          <>
            <div className="flex-1 overflow-y-auto">
              {isLoadingMessages ? (
                <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex gap-4 animate-pulse">
                      <div className="w-8 h-8 rounded-full bg-cgpt-card flex-shrink-0" />
                      <div className="flex-1 space-y-2">
                        <div className="h-3 bg-cgpt-card rounded w-1/4" />
                        <div className="h-3 bg-cgpt-card rounded w-3/4" />
                        <div className="h-3 bg-cgpt-card rounded w-1/2" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center px-4">
                  <div className="bg-gradient-to-br from-accent to-accent-light p-4 rounded-2xl mb-4">
                    <Bot className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-cgpt-text mb-2">
                    How can I help you today?
                  </h2>
                  <p className="text-cgpt-muted max-w-md mb-8">
                    Choose a provider above or use Auto smart-routing. Ask anything,
                    upload documents, or compare AI models side by side.
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
                    {SUGGESTIONS.map((s) => (
                      <button
                        key={s.text}
                        onClick={() => streamMessage(s.text)}
                        className="flex items-center gap-3 text-left p-4 rounded-xl border border-cgpt-border bg-cgpt-card hover:bg-cgpt-hover transition-colors group"
                      >
                        <s.icon className="h-5 w-5 text-accent flex-shrink-0" />
                        <span className="text-sm text-cgpt-text">{s.text}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="max-w-3xl mx-auto">
                  {messages.map((message, idx) => (
                    <ChatMessage
                      key={message.id}
                      message={message}
                      isLast={idx === messages.length - 1}
                      isStreaming={isStreaming}
                    />
                  ))}
                  {isStreaming && lastIsUser && <TypingIndicator />}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            <ChatInput />
          </>
        )}
      </div>
    </div>
  )
}
