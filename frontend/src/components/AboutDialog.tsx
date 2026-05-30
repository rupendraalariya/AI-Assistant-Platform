import { AnimatePresence, motion } from 'framer-motion'
import { X, Bot } from 'lucide-react'

interface AboutDialogProps {
  open: boolean
  onClose: () => void
}

const TECH_STACK = [
  'React', 'FastAPI', 'LangChain', 'RAG', 'FAISS',
  'OpenAI', 'Gemini', 'DeepSeek', 'Groq', 'Tailwind',
]

export default function AboutDialog({ open, onClose }: AboutDialogProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.92, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.92, opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md bg-cgpt-card border border-cgpt-border rounded-2xl shadow-2xl overflow-hidden"
          >
            <div className="relative p-6 text-center border-b border-cgpt-border">
              <button onClick={onClose} className="absolute right-4 top-4 icon-btn" aria-label="Close">
                <X className="h-5 w-5" />
              </button>
              <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-accent to-accent-light flex items-center justify-center mb-3">
                <Bot className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-xl font-bold text-cgpt-text">AI Assistant Platform</h2>
              <p className="text-sm text-cgpt-muted">Version 1.0.0</p>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-cgpt-muted mb-1">Developer</p>
                <p className="text-cgpt-text font-medium">Rupendra Alariya</p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-cgpt-muted mb-2">Technology Stack</p>
                <div className="flex flex-wrap gap-2">
                  {TECH_STACK.map((t) => (
                    <span key={t} className="text-xs px-2.5 py-1 rounded-full bg-accent/10 text-accent border border-accent/20">
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <p className="text-center text-[11px] text-cgpt-muted pt-2">
                All Rights Reserved © 2026
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
