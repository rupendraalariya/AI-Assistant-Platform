import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { FileText, Trash2, RefreshCw, CheckCircle2, Loader2, XCircle, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { documentsAPI } from '../services/api'

interface Doc {
  id: string
  filename: string
  file_type: string
  chunk_count: number
  status: string
}

interface DocumentsPanelProps {
  open: boolean
  onClose: () => void
  refreshKey?: number
}

const STATUS_ICON: Record<string, JSX.Element> = {
  ready: <CheckCircle2 className="h-4 w-4 text-accent" />,
  processing: <Loader2 className="h-4 w-4 text-warning animate-spin" />,
  failed: <XCircle className="h-4 w-4 text-error" />,
}

export default function DocumentsPanel({ open, onClose, refreshKey }: DocumentsPanelProps) {
  const [docs, setDocs] = useState<Doc[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await documentsAPI.list()
      setDocs(res.data.documents)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (open) load()
  }, [open, refreshKey])

  const handleDelete = async (id: string) => {
    try {
      await documentsAPI.delete(id)
      setDocs((d) => d.filter((x) => x.id !== id))
      toast.success('Document deleted')
    } catch {
      toast.error('Delete failed')
    }
  }

  const handleReindex = async (id: string) => {
    try {
      await documentsAPI.reindex(id)
      toast.success('Document reindexed')
      load()
    } catch {
      toast.error('Reindex failed')
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[90] flex justify-end bg-black/40"
          onClick={onClose}
        >
          <motion.div
            initial={{ x: 320 }}
            animate={{ x: 0 }}
            exit={{ x: 320 }}
            transition={{ type: 'tween', duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            className="w-80 h-full bg-cgpt-sidebar border-l border-cgpt-border flex flex-col"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-cgpt-border">
              <h3 className="font-semibold text-cgpt-text">Documents</h3>
              <button onClick={onClose} className="icon-btn"><X className="h-5 w-5" /></button>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {loading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-accent" />
                </div>
              ) : docs.length === 0 ? (
                <p className="text-center text-sm text-cgpt-muted py-8">
                  No documents uploaded yet.
                </p>
              ) : (
                docs.map((doc) => (
                  <div
                    key={doc.id}
                    className="group bg-cgpt-card border border-cgpt-border rounded-lg p-3"
                  >
                    <div className="flex items-start gap-2">
                      <FileText className="h-4 w-4 text-accent flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-cgpt-text truncate">{doc.filename}</p>
                        <div className="flex items-center gap-1.5 mt-1">
                          {STATUS_ICON[doc.status] || STATUS_ICON.ready}
                          <span className="text-xs text-cgpt-muted capitalize">{doc.status}</span>
                          <span className="text-xs text-cgpt-muted">· {doc.chunk_count} chunks</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleReindex(doc.id)}
                        className="flex items-center gap-1 text-xs px-2 py-1 rounded text-cgpt-muted hover:bg-cgpt-hover"
                      >
                        <RefreshCw className="h-3 w-3" /> Reindex
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="flex items-center gap-1 text-xs px-2 py-1 rounded text-error hover:bg-error/10"
                      >
                        <Trash2 className="h-3 w-3" /> Delete
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
