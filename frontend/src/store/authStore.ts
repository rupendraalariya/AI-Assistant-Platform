import { create } from 'zustand'
import { authAPI } from '../services/api'

interface User {
  id: string
  email: string
  username: string
  role: string
  auth_provider: string
  profile_picture?: string | null
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loadUser: () => Promise<void>
  setTokens: (accessToken: string, refreshToken: string) => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true })
    try {
      const response = await authAPI.login({ email, password })
      const { access_token, refresh_token } = response.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)

      const profileResponse = await authAPI.getProfile()
      set({
        user: profileResponse.data,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  register: async (email: string, username: string, password: string) => {
    set({ isLoading: true })
    try {
      await authAPI.register({ email, username, password })
      set({ isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  logout: async () => {
    try {
      await authAPI.logout()
    } catch {
      // ignore - logout should always succeed client-side
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  loadUser: async () => {
    try {
      const response = await authAPI.getProfile()
      set({ user: response.data, isAuthenticated: true })
    } catch {
      set({ user: null, isAuthenticated: false })
      localStorage.removeItem('access_token')
    }
  },

  // Called by the Google OAuth callback page after tokens land in the URL
  setTokens: async (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    set({ isAuthenticated: true })
    try {
      const profileResponse = await authAPI.getProfile()
      set({ user: profileResponse.data })
    } catch {
      // profile load failure is non-fatal here
    }
  },
}))
