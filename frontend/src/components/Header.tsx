import { Menu, Columns2 } from 'lucide-react'
import ModelSelector from './ModelSelector'
import UserMenu from './UserMenu'

interface HeaderProps {
  onToggleSidebar: () => void
  onToggleCompare?: () => void
  compareMode?: boolean
}

export default function Header({ onToggleSidebar, onToggleCompare, compareMode }: HeaderProps) {
  return (
    <header className="h-14 border-b border-cgpt-border bg-cgpt-bg flex items-center justify-between px-4 gap-2 flex-shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="icon-btn"
          aria-label="Toggle sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>
        <ModelSelector />
      </div>

      <div className="flex items-center gap-2">
        {onToggleCompare && (
          <button
            onClick={onToggleCompare}
            title="Compare mode"
            className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-colors ${
              compareMode
                ? 'bg-accent/15 text-accent'
                : 'text-cgpt-muted hover:bg-cgpt-hover hover:text-cgpt-text'
            }`}
          >
            <Columns2 className="h-4 w-4" />
            <span className="hidden sm:inline">Compare</span>
          </button>
        )}
        <UserMenu />
      </div>
    </header>
  )
}
