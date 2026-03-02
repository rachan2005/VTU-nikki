import { Routes, Route, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  Upload,
  Eye,
  Rocket,
  History,
  Settings,
  Zap,
  Moon,
  Sun,
  Skull,
} from 'lucide-react'
import Dashboard from './pages/Dashboard'
import UploadPage from './pages/Upload'
import Preview from './pages/Preview'
import Progress from './pages/Progress'
import HistoryPage from './pages/History'
import SettingsPage from './pages/Settings'
import Modal from './components/Modal'
import { isConfigured } from './lib/credentials'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload', icon: Upload, label: 'Upload' },
  { to: '/preview', icon: Eye, label: 'Preview' },
  { to: '/launch', icon: Rocket, label: 'Launch' },
  { to: '/history', icon: History, label: 'History' },
]

export default function App() {
  const [dark, setDark] = useState(true)
  const [showConfigPrompt, setShowConfigPrompt] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  const toggleTheme = () => {
    setDark(!dark)
    document.documentElement.classList.toggle('dark')
  }

  // Check if AI is configured on first load (once per session)
  useEffect(() => {
    if (sessionStorage.getItem('config_checked')) return
    sessionStorage.setItem('config_checked', 'true')
    if (!isConfigured()) {
      setShowConfigPrompt(true)
    }
  }, [])

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-50 border-r border-border bg-card flex flex-col shrink-0">
        {/* Logo */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-600 to-orange-500 flex items-center justify-center">
              <Skull className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight">VTU Diary</h1>
              <div className="flex items-center gap-1.5">
                <Zap className="w-3 h-3 text-red-500" />
                <span className="text-[10px] uppercase tracking-widest text-red-500 font-bold">
                  GOD MODE
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}

          {/* Settings — separated at bottom of nav */}
          <div className="pt-2 mt-2 border-t border-border">
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                }`
              }
            >
              <Settings className="w-4 h-4" />
              Settings
            </NavLink>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border space-y-3">
          <button
            onClick={toggleTheme}
            className="flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full rounded-lg hover:bg-accent"
          >
            {dark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            {dark ? 'Light Mode' : 'Dark Mode'}
          </button>
          <div className="text-[10px] text-muted-foreground/50 text-center">
            v3.0 // parallel-swarm engine
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="p-8 max-w-7xl mx-auto"
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/preview" element={<Preview />} />
              <Route path="/launch" element={<Progress />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Config prompt modal — shown once per session if AI not configured */}
      <Modal
        open={showConfigPrompt}
        onClose={() => setShowConfigPrompt(false)}
        title="Configure AI Provider"
        variant="warning"
        message="No AI API keys found. You need at least one LLM API key to generate diary entries. Set it up in Settings."
        confirmLabel="Go to Settings"
        cancelLabel="Later"
        onConfirm={() => {
          setShowConfigPrompt(false)
          navigate('/settings')
        }}
      />
    </div>
  )
}
