import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Monitor, Moon, Sun } from 'lucide-react'
import { useSettingsStore, type Theme, type CodeFontSize } from '../store/settingsStore'
import { useProviderStore } from '../store/providerStore'

export default function SettingsPage() {
  const navigate = useNavigate()
  const {
    theme, codeFontSize, temperature, maxTokens,
    setTheme, setCodeFontSize, setTemperature, setMaxTokens,
  } = useSettingsStore()
  const { providers, selectedProvider, setProvider } = useProviderStore()

  const themes: { value: Theme; label: string; icon: any }[] = [
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'system', label: 'System', icon: Monitor },
  ]

  const fontSizes: CodeFontSize[] = ['small', 'medium', 'large']

  return (
    <div className="min-h-screen bg-cgpt-bg p-4 sm:p-8">
      <div className="max-w-2xl mx-auto">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-cgpt-muted hover:text-cgpt-text mb-6 transition-colors">
          <ArrowLeft className="h-4 w-4" /> Back to chat
        </button>

        <h1 className="text-2xl font-bold text-cgpt-text mb-6">Settings</h1>

        {/* Theme */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card mb-4">
          <h2 className="text-lg font-semibold text-cgpt-text mb-3">Appearance</h2>
          <p className="text-sm text-cgpt-muted mb-3">Theme</p>
          <div className="grid grid-cols-3 gap-3">
            {themes.map((t) => (
              <button
                key={t.value}
                onClick={() => setTheme(t.value)}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition-colors ${
                  theme === t.value
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-cgpt-border text-cgpt-muted hover:bg-cgpt-hover'
                }`}
              >
                <t.icon className="h-5 w-5" />
                <span className="text-sm">{t.label}</span>
              </button>
            ))}
          </div>
        </motion.div>

        {/* Code font size */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="card mb-4">
          <h2 className="text-lg font-semibold text-cgpt-text mb-3">Code Display</h2>
          <p className="text-sm text-cgpt-muted mb-3">Font Size</p>
          <div className="grid grid-cols-3 gap-3">
            {fontSizes.map((size) => (
              <button
                key={size}
                onClick={() => setCodeFontSize(size)}
                className={`p-3 rounded-xl border capitalize transition-colors ${
                  codeFontSize === size
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-cgpt-border text-cgpt-muted hover:bg-cgpt-hover'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Model settings */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card">
          <h2 className="text-lg font-semibold text-cgpt-text mb-4">Model Settings</h2>

          <div className="mb-4">
            <label className="text-sm text-cgpt-muted block mb-2">Default Provider</label>
            <select
              value={selectedProvider}
              onChange={(e) => setProvider(e.target.value)}
              className="input-field"
            >
              <option value="auto">Auto Route</option>
              {providers.map((p) => (
                <option key={p.id} value={p.id} disabled={!p.configured}>
                  {p.name}{p.configured ? '' : ' (no key)'}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="text-sm text-cgpt-muted flex justify-between mb-2">
              <span>Temperature</span>
              <span className="text-accent">{temperature.toFixed(1)}</span>
            </label>
            <input
              type="range" min="0" max="2" step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="w-full accent-accent"
            />
            <p className="text-xs text-cgpt-muted mt-1">Lower = focused, Higher = creative</p>
          </div>

          <div>
            <label className="text-sm text-cgpt-muted flex justify-between mb-2">
              <span>Max Tokens</span>
              <span className="text-accent">{maxTokens}</span>
            </label>
            <input
              type="range" min="256" max="8000" step="256"
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
              className="w-full accent-accent"
            />
          </div>
        </motion.div>
      </div>
    </div>
  )
}
