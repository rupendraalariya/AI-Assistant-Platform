import { create } from 'zustand'

export type Theme = 'dark' | 'light' | 'system'
export type CodeFontSize = 'small' | 'medium' | 'large'

interface SettingsState {
  theme: Theme
  codeFontSize: CodeFontSize
  temperature: number
  maxTokens: number

  setTheme: (theme: Theme) => void
  setCodeFontSize: (size: CodeFontSize) => void
  setTemperature: (t: number) => void
  setMaxTokens: (n: number) => void
  applyTheme: () => void
}

function resolveTheme(theme: Theme): 'dark' | 'light' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return theme
}

function applyThemeToDOM(theme: Theme) {
  const resolved = resolveTheme(theme)
  const root = document.documentElement
  if (resolved === 'dark') {
    root.classList.add('dark')
    root.classList.remove('light')
  } else {
    root.classList.add('light')
    root.classList.remove('dark')
  }
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  theme: (localStorage.getItem('theme') as Theme) || 'dark',
  codeFontSize: (localStorage.getItem('codeFontSize') as CodeFontSize) || 'medium',
  temperature: Number(localStorage.getItem('temperature') || 0.7),
  maxTokens: Number(localStorage.getItem('maxTokens') || 2000),

  setTheme: (theme) => {
    localStorage.setItem('theme', theme)
    applyThemeToDOM(theme)
    set({ theme })
  },

  setCodeFontSize: (codeFontSize) => {
    localStorage.setItem('codeFontSize', codeFontSize)
    set({ codeFontSize })
  },

  setTemperature: (temperature) => {
    localStorage.setItem('temperature', String(temperature))
    set({ temperature })
  },

  setMaxTokens: (maxTokens) => {
    localStorage.setItem('maxTokens', String(maxTokens))
    set({ maxTokens })
  },

  applyTheme: () => {
    applyThemeToDOM(get().theme)
  },
}))
