import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'
import { Bot } from 'lucide-react'
import GoogleButton from '../components/GoogleButton'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const { register, isLoading } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }
    try {
      await register(email, username, password)
      toast.success('Account created! Please sign in.')
      navigate('/login')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-cgpt-bg px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="max-w-md w-full space-y-6"
      >
        <div className="text-center">
          <div className="flex justify-center">
            <div className="bg-gradient-to-br from-accent to-accent-light p-3 rounded-2xl">
              <Bot className="h-8 w-8 text-white" />
            </div>
          </div>
          <h2 className="mt-4 text-3xl font-bold text-cgpt-text">Create Account</h2>
          <p className="mt-2 text-cgpt-muted">Join the AI Assistant Platform</p>
        </div>

        <form className="card space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-cgpt-text mb-1.5">Email</label>
            <input id="email" type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} className="input-field" placeholder="you@example.com" />
          </div>

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-cgpt-text mb-1.5">Username</label>
            <input id="username" type="text" required minLength={3} value={username}
              onChange={(e) => setUsername(e.target.value)} className="input-field" placeholder="johndoe" />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-cgpt-text mb-1.5">Password</label>
            <input id="password" type="password" required minLength={8} value={password}
              onChange={(e) => setPassword(e.target.value)} className="input-field" placeholder="••••••••" />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-cgpt-text mb-1.5">Confirm Password</label>
            <input id="confirmPassword" type="password" required value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)} className="input-field" placeholder="••••••••" />
          </div>

          <button type="submit" disabled={isLoading} className="w-full btn-primary py-3 disabled:opacity-50">
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-cgpt-border" />
            <span className="text-xs text-cgpt-muted uppercase">or</span>
            <div className="flex-1 h-px bg-cgpt-border" />
          </div>

          <GoogleButton label="Sign up with Google" />

          <p className="text-center text-sm text-cgpt-muted">
            Already have an account?{' '}
            <Link to="/login" className="text-accent hover:text-accent-hover font-medium">Sign in</Link>
          </p>
        </form>
      </motion.div>
    </div>
  )
}
