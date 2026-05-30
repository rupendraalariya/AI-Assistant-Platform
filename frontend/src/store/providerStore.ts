import { create } from 'zustand'
import { providersAPI } from '../services/api'

export interface Provider {
  id: string
  name: string
  configured: boolean
  requires_key: boolean
  model_count: number
}

export interface Model {
  id: string
  name: string
  context_window: number
  input_cost: number
  output_cost: number
  supports_streaming: boolean
}

interface ProviderState {
  providers: Provider[]
  models: Model[]
  selectedProvider: string
  selectedModel: string
  enableFallback: boolean
  isLoading: boolean

  loadProviders: () => Promise<void>
  loadModels: (providerId: string) => Promise<void>
  setProvider: (providerId: string) => Promise<void>
  setModel: (modelId: string) => void
  toggleFallback: () => void
}

export const useProviderStore = create<ProviderState>((set, get) => ({
  providers: [],
  models: [],
  selectedProvider: 'auto',
  selectedModel: '',
  enableFallback: true,
  isLoading: false,

  loadProviders: async () => {
    set({ isLoading: true })
    try {
      const response = await providersAPI.list()
      set({ providers: response.data, isLoading: false })

      // Auto-select first configured provider's models
      const configured = response.data.find((p: Provider) => p.configured)
      if (configured && get().selectedProvider !== 'auto') {
        await get().loadModels(configured.id)
      }
    } catch (error) {
      set({ isLoading: false })
      console.error('Failed to load providers:', error)
    }
  },

  loadModels: async (providerId: string) => {
    if (providerId === 'auto') {
      set({ models: [], selectedModel: '' })
      return
    }
    try {
      const response = await providersAPI.getModels(providerId)
      const models: Model[] = response.data
      set({
        models,
        selectedModel: models.length > 0 ? models[0].id : '',
      })
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  },

  setProvider: async (providerId: string) => {
    set({ selectedProvider: providerId })
    await get().loadModels(providerId)
  },

  setModel: (modelId: string) => set({ selectedModel: modelId }),

  toggleFallback: () => set((state) => ({ enableFallback: !state.enableFallback })),
}))
