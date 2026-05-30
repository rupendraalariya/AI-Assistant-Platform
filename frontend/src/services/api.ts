import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling + automatic token refresh
let isRefreshing = false

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Attempt a one-time token refresh on 401
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/')
    ) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken && !isRefreshing) {
        isRefreshing = true
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          isRefreshing = false
          // Retry the original request with the new token
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return api(originalRequest)
        } catch {
          isRefreshing = false
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  register: (data: { email: string; username: string; password: string }) =>
    api.post('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  getProfile: () => api.get('/auth/me'),
  // Full URL to kick off the Google OAuth redirect flow
  googleLoginUrl: () => `${API_BASE_URL}/auth/google/login`,
}

// Chat API
export const chatAPI = {
  sendMessage: (data: {
    message: string
    session_id?: string
    use_rag?: boolean
    temperature?: number
  }) => api.post('/chat', data),

  streamMessage: async function* (data: {
    message: string
    session_id?: string
    use_rag?: boolean
  }) {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) return

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            yield data
          } catch {
            // Skip malformed data
          }
        }
      }
    }
  },
}

// Sessions API
export const sessionsAPI = {
  create: (data?: { title?: string; model?: string }) =>
    api.post('/sessions', data || {}),
  list: () => api.get('/sessions'),
  get: (id: string) => api.get(`/sessions/${id}`),
  delete: (id: string) => api.delete(`/sessions/${id}`),
  getHistory: (id: string) => api.get(`/sessions/${id}/history`),
  clearHistory: (id: string) => api.delete(`/sessions/${id}/history`),
}

// Multi-Provider API
export const providersAPI = {
  list: () => api.get('/providers'),
  getModels: (providerId: string) => api.get(`/providers/${providerId}/models`),
  getAllModels: () => api.get('/models'),

  chat: (data: {
    message: string
    provider?: string
    model?: string
    session_id?: string
    temperature?: number
    max_tokens?: number
    enable_fallback?: boolean
  }) => api.post('/chat/multi', data),

  compare: (data: {
    message: string
    providers: { provider: string; model: string }[]
    temperature?: number
    max_tokens?: number
  }) => api.post('/chat/compare', data),

  streamMulti: async function* (data: {
    message: string
    provider?: string
    model?: string
    session_id?: string
    enable_fallback?: boolean
  }) {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${API_BASE_URL}/chat/multi/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) return

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            yield JSON.parse(line.slice(6))
          } catch {
            // skip malformed
          }
        }
      }
    }
  },
}

// Documents API
export const documentsAPI = {
  upload: (file: File, sessionId?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (sessionId) formData.append('session_id', sessionId)
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: () => api.get('/documents'),
  delete: (id: string) => api.delete(`/documents/${id}`),
  reindex: (id: string) => api.post(`/documents/${id}/reindex`),
}

// Analytics API
export const analyticsAPI = {
  getUsage: () => api.get('/analytics/usage'),
  getCosts: () => api.get('/analytics/costs'),
  getSystem: () => api.get('/analytics/system'),
}

export default api
