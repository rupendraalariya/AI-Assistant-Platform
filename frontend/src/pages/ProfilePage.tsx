import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, MessageSquare, Hash, FileText, Coins } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { analyticsAPI, documentsAPI } from '../services/api'

interface Stats {
  total_sessions: number
  total_messages: number
  total_tokens: number
  documents: number
}

export default function ProfilePage() {
  const { user, loadUser } = useAuthStore()
  const navigate = useNavigate()
  const [stats, setStats] = useState<Stats>({
    total_sessions: 0, total_messages: 0, total_tokens: 0, documents: 0,
  })

  useEffect(() => {
    loadUser()
    Promise.all([
      analyticsAPI.getUsage().catch(() => ({ data: {} })),
      documentsAPI.list().catch(() => ({ data: { total: 0 } })),
    ]).then(([usage, docs]) => {
      setStats({
        total_sessions: usage.data.total_sessions || 0,
        total_messages: usage.data.total_messages || 0,
        total_tokens: usage.data.total_tokens || 0,
        documents: docs.data.total || 0,
      })
    })
  }, [])

  const statCards = [
    { icon: MessageSquare, label: 'Total Chats', value: stats.total_sessions },
    { icon: Hash, label: 'Messages', value: stats.total_messages },
    { icon: FileText, label: 'Documents', value: stats.documents },
    { icon: Coins, label: 'Tokens Used', value: stats.total_tokens.toLocaleString() },
  ]

  return (
    <div className="min-h-screen bg-cgpt-bg p-4 sm:p-8">
      <div className="max-w-3xl mx-auto">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-cgpt-muted hover:text-cgpt-text mb-6 transition-colors">
          <ArrowLeft className="h-4 w-4" /> Back to chat
        </button>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card mb-6">
          <div className="flex items-center gap-4">
            {user?.profile_picture ? (
              <img src={user.profile_picture} alt={user.username} className="h-20 w-20 rounded-full object-cover" referrerPolicy="no-referrer" />
            ) : (
              <div className="h-20 w-20 rounded-full bg-accent text-white flex items-center justify-center text-3xl font-bold">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <h1 className="text-2xl font-bold text-cgpt-text">{user?.username}</h1>
              <p className="text-cgpt-muted">{user?.email}</p>
              <span className="inline-block mt-2 text-xs uppercase tracking-wide px-2 py-0.5 rounded bg-accent/15 text-accent">
                {user?.auth_provider} account
              </span>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {statCards.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="card text-center"
            >
              <s.icon className="h-6 w-6 text-accent mx-auto mb-2" />
              <p className="text-2xl font-bold text-cgpt-text">{s.value}</p>
              <p className="text-xs text-cgpt-muted mt-1">{s.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
