import { create } from 'zustand'
import { sessionsAPI, providersAPI } from '../services/api'
import { useProviderStore } from './providerStore'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  tokens_used?: number
  latency_ms?: number
  provider?: string
  model?: string
  reaction?: 'like' | 'dislike' | null
  created_at: string
}

export interface Session {
  id: string
  title: string
  model: string
  total_tokens: number
  pinned?: boolean
  created_at: string
}

interface ChatState {
  messages: Message[]
  sessions: Session[]
  currentSessionId: string | null
  isStreaming: boolean
  isLoading: boolean
  isLoadingMessages: boolean

  streamMessage: (message: string) => Promise<void>
  regenerateLast: () => Promise<void>
  editUserMessage: (messageId: string, newContent: string) => Promise<void>
  deleteMessage: (messageId: string) => void
  setReaction: (messageId: string, reaction: 'like' | 'dislike') => void

  loadSessions: () => Promise<void>
  createSession: () => Promise<void>
  setActiveSession: (sessionId: string) => void
  loadMessages: (sessionId: string) => Promise<void>
  selectSession: (sessionId: string) => Promise<void>
  deleteSession: (sessionId: string) => Promise<void>
  renameSession: (sessionId: string, title: string) => void
  togglePinSession: (sessionId: string) => void
}

// Core streaming routine, reusable for send + regenerate
async function runStream(
  set: any,
  get: any,
  message: string,
  appendUserMessage: boolean
) {
  const { currentSessionId } = get()

  if (appendUserMessage) {
    const userMessage: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    }
    set((state: ChatState) => ({ messages: [...state.messages, userMessage] }))
  }

  const assistantMessage: Message = {
    id: `a-${Date.now()}`,
    role: 'assistant',
    content: '',
    reaction: null,
    created_at: new Date().toISOString(),
  }
  set((state: ChatState) => ({
    messages: [...state.messages, assistantMessage],
    isStreaming: true,
  }))

  const { selectedProvider, selectedModel, enableFallback } = useProviderStore.getState()

  for await (const chunk of providersAPI.streamMulti({
    message,
    provider: selectedProvider,
    model: selectedModel || undefined,
    session_id: currentSessionId || undefined,
    enable_fallback: enableFallback,
  })) {
    if (chunk.error) {
      set((state: ChatState) => {
        const messages = [...state.messages]
        const last = messages[messages.length - 1]
        if (last.role === 'assistant') last.content = `⚠️ ${chunk.error}`
        return { messages, isStreaming: false }
      })
      break
    }

    if (chunk.meta) {
      set((state: ChatState) => {
        const messages = [...state.messages]
        const last = messages[messages.length - 1]
        if (last.role === 'assistant') {
          last.provider = chunk.provider
          last.model = chunk.model
        }
        return { messages }
      })
      continue
    }

    if (chunk.done) {
      set((state: ChatState) => {
        const messages = [...state.messages]
        const last = messages[messages.length - 1]
        if (last.role === 'assistant') {
          last.provider = chunk.provider || last.provider
          last.model = chunk.model || last.model
        }
        const newSessionId = chunk.session_id || state.currentSessionId
        if (newSessionId) localStorage.setItem('last_session_id', newSessionId)
        return {
          messages,
          currentSessionId: newSessionId,
          isStreaming: false,
        }
      })
      break
    }

    set((state: ChatState) => {
      const messages = [...state.messages]
      const last = messages[messages.length - 1]
      if (last.role === 'assistant') last.content += chunk.content
      return { messages }
    })
  }
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessions: [],
  currentSessionId: localStorage.getItem('last_session_id') || null,
  isStreaming: false,
  isLoading: false,
  isLoadingMessages: false,

  streamMessage: async (message: string) => {
    try {
      await runStream(set, get, message, true)
      await get().loadSessions()
    } catch (error) {
      set({ isStreaming: false })
      throw error
    }
  },

  regenerateLast: async () => {
    const { messages } = get()
    // Find the last user message
    const lastUser = [...messages].reverse().find((m) => m.role === 'user')
    if (!lastUser) return

    // Remove the last assistant message if present
    set((state) => {
      const msgs = [...state.messages]
      if (msgs.length && msgs[msgs.length - 1].role === 'assistant') {
        msgs.pop()
      }
      return { messages: msgs }
    })

    try {
      await runStream(set, get, lastUser.content, false)
    } catch {
      set({ isStreaming: false })
    }
  },

  editUserMessage: async (messageId: string, newContent: string) => {
    const { messages } = get()
    const idx = messages.findIndex((m) => m.id === messageId)
    if (idx === -1) return

    // Truncate everything from this message onward, then re-send
    set({ messages: messages.slice(0, idx) })
    try {
      await runStream(set, get, newContent, true)
      await get().loadSessions()
    } catch {
      set({ isStreaming: false })
    }
  },

  deleteMessage: (messageId: string) => {
    set((state) => ({
      messages: state.messages.filter((m) => m.id !== messageId),
    }))
  },

  setReaction: (messageId: string, reaction: 'like' | 'dislike') => {
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId
          ? { ...m, reaction: m.reaction === reaction ? null : reaction }
          : m
      ),
    }))
  },

  loadSessions: async () => {
    try {
      const response = await sessionsAPI.list()
      const pinned = JSON.parse(localStorage.getItem('pinned_sessions') || '[]')
      const sessions = response.data.sessions.map((s: Session) => ({
        ...s,
        pinned: pinned.includes(s.id),
      }))
      set({ sessions })
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  },

  createSession: async () => {
    localStorage.removeItem('last_session_id')
    set({ messages: [], currentSessionId: null })
  },

  setActiveSession: (sessionId: string) => {
    localStorage.setItem('last_session_id', sessionId)
    set({ currentSessionId: sessionId })
  },

  loadMessages: async (sessionId: string) => {
    console.log('Loading History:', sessionId)
    set({ isLoadingMessages: true })
    try {
      const response = await sessionsAPI.getHistory(sessionId)
      const loaded = response.data.messages.map((m: any) => ({ ...m, reaction: null }))
      console.log('Messages:', loaded)
      set({
        messages: loaded,
        isLoadingMessages: false,
      })
    } catch (error) {
      console.error('[chatStore] Failed to load messages:', error)
      set({ isLoadingMessages: false, messages: [] })
    }
  },

  // Full select = set active + persist + load messages
  selectSession: async (sessionId: string) => {
    console.debug('[chatStore] selectSession', sessionId)
    get().setActiveSession(sessionId)
    await get().loadMessages(sessionId)
  },

  renameSession: (sessionId: string, title: string) => {
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === sessionId ? { ...s, title } : s
      ),
    }))
  },

  deleteSession: async (sessionId: string) => {
    try {
      await sessionsAPI.delete(sessionId)
      const { currentSessionId } = get()
      if (currentSessionId === sessionId) {
        localStorage.removeItem('last_session_id')
        set({ messages: [], currentSessionId: null })
      }
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
      }))
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  },

  togglePinSession: (sessionId: string) => {
    set((state) => {
      const sessions = state.sessions.map((s) =>
        s.id === sessionId ? { ...s, pinned: !s.pinned } : s
      )
      const pinnedIds = sessions.filter((s) => s.pinned).map((s) => s.id)
      localStorage.setItem('pinned_sessions', JSON.stringify(pinnedIds))
      return { sessions }
    })
  },
}))
