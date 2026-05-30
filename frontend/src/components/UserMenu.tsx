import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { User as UserIcon, Settings, LogOut, ChevronDown } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function UserMenu() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const initial = user?.username?.charAt(0).toUpperCase() || 'U'

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 p-1 rounded-lg hover:bg-cgpt-hover transition-colors"
        aria-label="User menu"
      >
        {user?.profile_picture ? (
          <img
            src={user.profile_picture}
            alt={user.username}
            className="h-8 w-8 rounded-full object-cover"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="h-8 w-8 rounded-full bg-accent text-white flex items-center justify-center text-sm font-medium">
            {initial}
          </div>
        )}
        <ChevronDown className="h-4 w-4 text-cgpt-muted" />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-64 bg-cgpt-card border border-cgpt-border rounded-xl shadow-2xl overflow-hidden z-50"
          >
            {/* User info */}
            <div className="px-4 py-3 border-b border-cgpt-border">
              <p className="text-sm font-semibold text-cgpt-text truncate">{user?.username}</p>
              <p className="text-xs text-cgpt-muted truncate">{user?.email}</p>
              <span className="inline-block mt-1 text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-accent/15 text-accent">
                {user?.auth_provider}
              </span>
            </div>

            <div className="p-1.5">
              <button
                onClick={() => { setOpen(false); navigate('/profile') }}
                className="menu-item"
              >
                <UserIcon className="h-4 w-4" /> Profile
              </button>
              <button
                onClick={() => { setOpen(false); navigate('/settings') }}
                className="menu-item"
              >
                <Settings className="h-4 w-4" /> Settings
              </button>
              <button
                onClick={handleLogout}
                className="menu-item text-error hover:bg-error/10"
              >
                <LogOut className="h-4 w-4" /> Logout
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
