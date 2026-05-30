import { useEffect } from 'react'
import { useProviderStore } from '../store/providerStore'
import { Cpu, Sparkles, Zap } from 'lucide-react'

export default function ModelSelector() {
  const {
    providers,
    models,
    selectedProvider,
    selectedModel,
    enableFallback,
    loadProviders,
    setProvider,
    setModel,
    toggleFallback,
  } = useProviderStore()

  useEffect(() => {
    loadProviders()
  }, [])

  const selectClass =
    'text-sm rounded-lg border border-cgpt-border bg-cgpt-card text-cgpt-text px-3 py-1.5 outline-none focus:ring-2 focus:ring-accent cursor-pointer hover:bg-cgpt-hover transition-colors'

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className="flex items-center gap-1.5">
        <Sparkles className="h-4 w-4 text-accent" />
        <select
          value={selectedProvider}
          onChange={(e) => setProvider(e.target.value)}
          className={selectClass}
          aria-label="Select provider"
        >
          <option value="auto">🪄 Auto Route</option>
          {providers.map((p) => (
            <option key={p.id} value={p.id} disabled={!p.configured}>
              {p.name}{p.configured ? '' : ' (no key)'}
            </option>
          ))}
        </select>
      </div>

      {selectedProvider !== 'auto' && models.length > 0 && (
        <div className="flex items-center gap-1.5">
          <Cpu className="h-4 w-4 text-cgpt-muted" />
          <select
            value={selectedModel}
            onChange={(e) => setModel(e.target.value)}
            className={selectClass}
            aria-label="Select model"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>
      )}

      <button
        onClick={toggleFallback}
        title="Auto-switch providers if one fails"
        className={`flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg transition-colors ${
          enableFallback
            ? 'bg-accent/15 text-accent'
            : 'bg-cgpt-card text-cgpt-muted'
        }`}
      >
        <Zap className="h-3 w-3" />
        Fallback {enableFallback ? 'ON' : 'OFF'}
      </button>
    </div>
  )
}
