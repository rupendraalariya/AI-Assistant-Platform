import { useState, useRef, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Bot, Plus, Search, MessageSquare, Trash2, Pin, PinOff,
  Pencil, MoreHorizontal, Upload, Github, Linkedin, Globe, Info, FileText,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useChatStore, type Session } from '../store/chatStore'
import { documentsAPI } from '../services/api'
import AboutDialog from './AboutDialog'
import DocumentsPanel from './DocumentsPanel'

interface SidebarProps {
  isOpen: boolean
}

export default function Sidebar({ isOpen }: SidebarProps) {
  const {
    sessions, currentSessionId, createSession, selectSession,
    deleteSession, togglePinSession, renameSession,
  } = useChatStore()

  const [search, setSearch] = useState('')
  const [menuFor, setMenuFor] = useState<string | null>(null)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [uploading, setUploading] = useState(false)
  const [aboutOpen, setAboutOpen] = useState(false)
  const [docsOpen, setDocsOpen] = useState(false)
  const [docsRefresh, setDocsRefresh] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const close = () => setMenuFor(null)
    if (menuFor) {
      document.addEventListener('click', close)
      return () => document.removeEventListener('click', close)
    }
  }, [menuFor])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const response = await documentsAPI.upload(file, currentSessionId || undefined)
      toast.success(response.data.message || 'Document uploaded')
      setDocsRefresh((n) => n + 1)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const filtered = sessions.filter((s) =>
    s.title.toLowerCase().includes(search.toLowerCase())
  )
  const pinned = filtered.filter((s) => s.pinned)
  const recent = filtered.filter((s) => !s.pinned)

  const handleRename = (session: Session) => {
    setRenamingId(session.id)
    setRenameValue(session.title)
    setMenuFor(null)
  }

  const saveRename = () => {
    if (renamingId && renameValue.trim()) {
      renameSession(renamingId, renameValue.trim())
      toast.success('Chat renamed')
    }
    setRenamingId(null)
  }

  const handleExport = (session: Session) => {
    const data = JSON.stringify(session, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-${session.id}.json`
    a.click()
    URL.revokeObjectURL(url)
    setMenuFor(null)
    toast.success('Chat exported')
  }

  const renderSession = (session: Session) => {
    const active = currentSessionId === session.id
    return (
      <div
        key={session.id}
        onClick={() => {
          console.log('Clicked Session:', session.id)
          selectSession(session.id)
        }}
        className={`group relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors border-l-4 ${
          active
            ? 'bg-cgpt-card border-l-accent text-cgpt-text'
            : 'border-l-transparent text-cgpt-muted hover:bg-cgpt-hover'
        }`}
      >
        {session.pinned ? (
          <Pin className="h-3.5 w-3.5 flex-shrink-0 text-accent" />
        ) : (
          <MessageSquare className="h-3.5 w-3.5 flex-shrink-0" />
        )}

        {renamingId === session.id ? (
          <input
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onBlur={saveRename}
            onKeyDown={(e) => e.key === 'Enter' && saveRename()}
            onClick={(e) => e.stopPropagation()}
            autoFocus
            className="flex-1 bg-transparent border-b border-accent text-sm text-cgpt-text outline-none"
          />
        ) : (
          <span className="text-sm truncate flex-1">{session.title}</span>
        )}

        {/* Context menu trigger */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            setMenuFor(menuFor === session.id ? null : session.id)
          }}
          className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-cgpt-border transition-all"
          aria-label="Chat options"
        >
          <MoreHorizontal className="h-4 w-4" />
        </button>

        {/* Context menu */}
        <AnimatePresence>
          {menuFor === session.id && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.12 }}
              onClick={(e) => e.stopPropagation()}
              className="absolute right-2 top-9 w-40 bg-cgpt-card border border-cgpt-border rounded-lg shadow-2xl z-50 p-1"
            >
              <button onClick={() => handleRename(session)} className="menu-item text-xs">
                <Pencil className="h-3.5 w-3.5" /> Rename
              </button>
              <button onClick={() => { togglePinSession(session.id); setMenuFor(null) }} className="menu-item text-xs">
                {session.pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
                {session.pinned ? 'Unpin' : 'Pin'}
              </button>
              <button onClick={() => handleExport(session)} className="menu-item text-xs">
                <Upload className="h-3.5 w-3.5" /> Export
              </button>
              <button
                onClick={() => { deleteSession(session.id); setMenuFor(null) }}
                className="menu-item text-xs text-error hover:bg-error/10"
              >
                <Trash2 className="h-3.5 w-3.5" /> Delete
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  return (
    <AnimatePresence initial={false}>
      {isOpen && (
        <motion.aside
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 280, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="bg-cgpt-sidebar border-r border-cgpt-border flex flex-col h-full overflow-hidden flex-shrink-0"
        >
          <div className="w-[280px] flex flex-col h-full">
            {/* Header */}
            <div className="p-3 border-b border-cgpt-border">
              <div className="flex items-center gap-2 mb-3 px-1">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent to-accent-light flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <span className="font-semibold text-cgpt-text">AI Assistant</span>
              </div>

              <button
                onClick={createSession}
                className="w-full flex items-center justify-center gap-2 text-sm bg-cgpt-card hover:bg-cgpt-hover border border-cgpt-border text-cgpt-text rounded-lg py-2 transition-colors"
              >
                <Plus className="h-4 w-4" />
                New Chat
              </button>
            </div>

            {/* Search */}
            <div className="px-3 py-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-cgpt-muted" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search chats..."
                  className="w-full bg-cgpt-card border border-cgpt-border rounded-lg pl-8 pr-3 py-1.5 text-sm text-cgpt-text placeholder-cgpt-muted outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
            </div>

            {/* Chat list */}
            <div className="flex-1 overflow-y-auto px-2 space-y-1">
              {pinned.length > 0 && (
                <>
                  <p className="px-3 pt-2 pb-1 text-[10px] uppercase tracking-wider text-cgpt-muted font-semibold">
                    Pinned
                  </p>
                  {pinned.map(renderSession)}
                </>
              )}
              {recent.length > 0 && (
                <>
                  <p className="px-3 pt-3 pb-1 text-[10px] uppercase tracking-wider text-cgpt-muted font-semibold">
                    Recent
                  </p>
                  {recent.map(renderSession)}
                </>
              )}
              {filtered.length === 0 && (
                <p className="text-center text-sm text-cgpt-muted py-8">
                  {search ? 'No chats found' : 'No chats yet'}
                </p>
              )}
            </div>

            {/* Upload */}
            <div className="px-3 py-2 border-t border-cgpt-border space-y-1">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.csv"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="w-full flex items-center justify-center gap-2 text-sm text-cgpt-muted hover:text-cgpt-text hover:bg-cgpt-hover rounded-lg py-2 transition-colors"
              >
                <Upload className="h-4 w-4" />
                {uploading ? 'Uploading...' : 'Upload Document'}
              </button>
              <button
                onClick={() => setDocsOpen(true)}
                className="w-full flex items-center justify-center gap-2 text-sm text-cgpt-muted hover:text-cgpt-text hover:bg-cgpt-hover rounded-lg py-2 transition-colors"
              >
                <FileText className="h-4 w-4" />
                View Documents
              </button>
            </div>

            {/* Developer branding footer */}
            <div className="px-3 py-3 border-t border-cgpt-border">
              <div className="flex items-center justify-center gap-3 mb-2">
                <a href="https://github.com/" target="_blank" rel="noreferrer" className="icon-btn" title="GitHub">
                  <Github className="h-4 w-4" />
                </a>
                <a href="https://linkedin.com/" target="_blank" rel="noreferrer" className="icon-btn" title="LinkedIn">
                  <Linkedin className="h-4 w-4" />
                </a>
                <a href="https://portfolio.com/" target="_blank" rel="noreferrer" className="icon-btn" title="Portfolio">
                  <Globe className="h-4 w-4" />
                </a>
                <button onClick={() => setAboutOpen(true)} className="icon-btn" title="About">
                  <Info className="h-4 w-4" />
                </button>
              </div>
              <p className="text-center text-[11px] text-cgpt-muted">
                Developed by <span className="text-cgpt-text font-medium">Rupendra Alariya</span>
              </p>
              <p className="text-center text-[10px] text-cgpt-muted">
                All Rights Reserved © 2026
              </p>
            </div>
          </div>
        </motion.aside>
      )}
      <AboutDialog open={aboutOpen} onClose={() => setAboutOpen(false)} />
      <DocumentsPanel open={docsOpen} onClose={() => setDocsOpen(false)} refreshKey={docsRefresh} />
    </AnimatePresence>
  )
}
