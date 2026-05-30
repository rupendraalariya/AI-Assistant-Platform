import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { providersAPI } from '../services/api'
import { useProviderStore } from '../store/providerStore'
import { Send, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import MarkdownRenderer from './MarkdownRenderer'

interface CompareResult {
  provider: string
  model: string
  content: string
  error: boolean
  total_tokens: number
  latency_ms: number
  cost: number
}

const PROVIDER_ACCENT: Record<string, string> = {
  openai: 'border-t-emerald-500',
  gemini: 'border-t-blue-500',
  claude: 'border-t-orange-500',
  groq: 'border-t-red-500',
  deepseek: 'border-t-purple-500',
  mistral: 'border-t-amber-500',
}

export default function CompareMode() {
  const { providers, loadProviders } = useProviderStore()
  const [message, setMessage] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [results, setResults] = useState<CompareResult[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => { loadProviders() }, [])

  useEffect(() => {
    if (selected.length === 0 && providers.length > 0) {
      setSelected(providers.filter((p) => p.configured).slice(0, 4).map((p) => p.id))
    }
  }, [providers])

  const toggleProvider = (id: string) => {
    setSelected((prev) => prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id])
  }

  const handleCompare = async () => {
    if (!message.trim() || selected.length === 0) {
      toast.error('Enter a prompt and select at least one provider')
      return
    }
    setLoading(true)
    setResults([])
    try {
      const response = await providersAPI.compare({
        message: message.trim(),
        providers: selected.map((id) => ({ provider: id, model: '' })),
      })
      setResults(response.data.results)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Compare failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-cgpt-bg">
      {/* Provider selection */}
      <div className="p-4 border-b border-cgpt-border">
        <p className="text-sm text-cgpt-muted mb-2">Select providers to compare:</p>
        <div className="flex flex-wrap gap-2">
          {providers.map((p) => (
            <button
              key={p.id}
              disabled={!p.configured}
              onClick={() => toggleProvider(p.id)}
              className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${
                selected.includes(p.id)
                  ? 'bg-accent text-white border-accent'
                  : p.configured
                  ? 'bg-cgpt-card text-cgpt-text border-cgpt-border hover:bg-cgpt-hover'
                  : 'opacity-40 cursor-not-allowed border-cgpt-border text-cgpt-muted'
              }`}
            >
              {p.name}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-4">
        {results.length === 0 && !loading && (
          <div className="text-center text-cgpt-muted mt-16">
            Enter a prompt below and hit Compare to see responses side by side.
          </div>
        )}
        {loading && (
          <div className="flex items-center justify-center mt-16 gap-2 text-cgpt-muted">
            <Loader2 className="h-5 w-5 animate-spin" />
            Querying {selected.length} providers in parallel...
          </div>
        )}
        {results.length > 0 && (
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${Math.min(results.length, 4)}, minmax(280px, 1fr))` }}>
            {results.map((r, i) => (
              <motion.div
                key={r.provider}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`rounded-xl border border-cgpt-border border-t-2 ${PROVIDER_ACCENT[r.provider] || 'border-t-gray-500'} bg-cgpt-card flex flex-col`}
              >
                <div className="px-4 py-2.5 border-b border-cgpt-border">
                  <div className="font-semibold text-cgpt-text capitalize">{r.provider}</div>
                  <div className="text-xs text-cgpt-muted truncate">{r.model}</div>
                </div>
                <div className="p-4 flex-1 overflow-y-auto max-h-[55vh]">
                  {r.error ? (
                    <p className="text-sm text-error">{r.content}</p>
                  ) : (
                    <MarkdownRenderer content={r.content} />
                  )}
                </div>
                {!r.error && (
                  <div className="px-4 py-2 border-t border-cgpt-border flex gap-3 text-xs text-cgpt-muted">
                    <span>{r.total_tokens} tok</span>
                    <span>{r.latency_ms}ms</span>
                    <span>${r.cost.toFixed(5)}</span>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-cgpt-border p-4">
        <div className="flex items-end gap-2 max-w-4xl mx-auto bg-cgpt-input border border-cgpt-border rounded-2xl px-3 py-2">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter a prompt to send to all selected providers..."
            rows={1}
            className="flex-1 resize-none bg-transparent text-cgpt-text placeholder-cgpt-muted outline-none py-2"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleCompare() }
            }}
          />
          <button
            onClick={handleCompare}
            disabled={loading}
            className="p-2 rounded-lg bg-accent hover:bg-accent-hover text-white disabled:opacity-40"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </div>
  )
}
