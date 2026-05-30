import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

/**
 * Handles the redirect back from the backend after Google OAuth.
 * The backend appends access_token & refresh_token as query params.
 */
export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setTokens } = useAuthStore()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const accessToken = searchParams.get('access_token')
    const refreshToken = searchParams.get('refresh_token')
    const errParam = searchParams.get('error')

    if (errParam) {
      setError(errParam)
      toast.error('Google sign-in failed. Please try again.')
      setTimeout(() => navigate('/login', { replace: true }), 2000)
      return
    }

    if (accessToken && refreshToken) {
      setTokens(accessToken, refreshToken).then(() => {
        toast.success('Signed in with Google!')
        navigate('/', { replace: true })
      })
    } else {
      setError('missing_tokens')
      setTimeout(() => navigate('/login', { replace: true }), 2000)
    }
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-cgpt-bg">
      <div className="text-center">
        {error ? (
          <p className="text-error">Sign-in failed. Redirecting to login...</p>
        ) : (
          <div className="flex flex-col items-center gap-3 text-cgpt-muted">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
            <p>Completing sign-in...</p>
          </div>
        )}
      </div>
    </div>
  )
}
