import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'
import { Bot } from 'lucide-react'
import GoogleButton from '../components/GoogleButton'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, isLoading } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      toast.success('Welcome back!')
      navigate('/')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-cgpt-bg px-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="max-w-md w-full space-y-8"
      >
        <div className="text-center">
          <div className="flex justify-center">
            <div className="bg-gradient-to-br from-accent to-accent-light p-3 rounded-2xl">
              <Bot className="h-8 w-8 text-white" />
            </div>
          </div>
          <h2 className="mt-4 text-3xl font-bold text-cgpt-text">AI Assistant Platform</h2>
          <p className="mt-2 text-cgpt-muted">Sign in to your account</p>
        </div>

        <form className="card space-y-5" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-cgpt-text mb-1.5">Email</label>
            <input
              id="email" type="email" required
              value={email} onChange={(e) => setEmail(e.target.value)}
              className="input-field" placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-cgpt-text mb-1.5">Password</label>
            <input
              id="password" type="password" required
              value={password} onChange={(e) => setPassword(e.target.value)}
              className="input-field" placeholder="••••••••"
            />
          </div>

          <button type="submit" disabled={isLoading} className="w-full btn-primary py-3 disabled:opacity-50">
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-cgpt-border" />
            <span className="text-xs text-cgpt-muted uppercase">or</span>
            <div className="flex-1 h-px bg-cgpt-border" />
          </div>

          <GoogleButton label="Continue with Google" />

          <p className="text-center text-sm text-cgpt-muted">
            Don't have an account?{' '}
            <Link to="/register" className="text-accent hover:text-accent-hover font-medium">Sign up</Link>
          </p>
        </form>
      </motion.div>
    </div>
  )
}
