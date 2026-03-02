import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Zap,
  TrendingUp,
  CheckCircle2,
  XCircle,
  Calendar,
  ArrowRight,
  Skull,
  Activity,
  Settings,
} from 'lucide-react'
import { getHistoryStats, type HistoryStats } from '@/lib/api'
import { isConfigured } from '@/lib/credentials'

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  delay,
}: {
  label: string
  value: string | number
  icon: typeof Zap
  color: string
  delay: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="border border-border rounded-xl p-5 bg-card hover:border-primary/30 transition-colors"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
          <motion.p
            className="text-3xl font-black mt-1 tabular-nums"
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: delay + 0.2, type: 'spring', stiffness: 200 }}
          >
            {value}
          </motion.p>
        </div>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </motion.div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState<HistoryStats | null>(null)

  useEffect(() => {
    getHistoryStats().then(setStats).catch(() => {})
  }, [])

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-8">
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 via-transparent to-orange-500/5" />
        <div className="relative">
          <div className="flex items-center gap-3 mb-2">
            <Skull className="w-6 h-6 text-red-500" />
            <span className="text-xs font-bold uppercase tracking-widest text-red-500">
              GOD MODE ACTIVE
            </span>
          </div>
          <h1 className="text-4xl font-black tracking-tight">VTU Diary Automation</h1>
          <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-relaxed">
            Feed it anything — voice memos, messy Excel logs, git histories, photos of whiteboards.
            It generates months of perfectly plausible, evaluator-satisfying diary entries in seconds.
            Parallel browser swarm submits them all while you watch.
          </p>
          <div className="flex items-center gap-3 mt-6">
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
            >
              Start Generating <ArrowRight className="w-4 h-4" />
            </Link>
            {!isConfigured() && (
              <Link
                to="/settings"
                className="inline-flex items-center gap-2 px-4 py-2.5 border border-orange-500/30 text-orange-400 rounded-lg text-xs font-medium hover:bg-orange-500/10 transition-colors"
              >
                <Settings className="w-3.5 h-3.5" />
                Configure AI
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total Submitted"
          value={stats?.total_submissions ?? '—'}
          icon={Calendar}
          color="bg-blue-500/10 text-blue-400"
          delay={0}
        />
        <StatCard
          label="Successful"
          value={stats?.successful ?? '—'}
          icon={CheckCircle2}
          color="bg-green-500/10 text-green-400"
          delay={0.1}
        />
        <StatCard
          label="Failed"
          value={stats?.failed ?? '—'}
          icon={XCircle}
          color="bg-red-500/10 text-red-400"
          delay={0.2}
        />
        <StatCard
          label="Success Rate"
          value={stats ? `${stats.success_rate}%` : '—'}
          icon={TrendingUp}
          color="bg-purple-500/10 text-purple-400"
          delay={0.3}
        />
      </div>

      {/* Capabilities grid */}
      <div>
        <h2 className="text-lg font-bold mb-4">Capabilities</h2>
        <div className="grid grid-cols-3 gap-4">
          {[
            {
              title: 'Multi-Input Ingestion',
              desc: 'Voice memos, Excel sheets, PDFs, photos, git logs — throw anything at it.',
              icon: Activity,
            },
            {
              title: 'Plausibility Engine',
              desc: 'Scores every entry. Warns you when it gets too convincing. Adjusts embellishment dynamically.',
              icon: Skull,
            },
            {
              title: 'Parallel Browser Swarm',
              desc: '5 headless browsers submitting simultaneously. Months of entries in minutes.',
              icon: Zap,
            },
          ].map((cap, i) => (
            <motion.div
              key={cap.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.1 }}
              className="border border-border rounded-xl p-5 bg-card hover:border-primary/20 transition-colors"
            >
              <cap.icon className="w-5 h-5 text-muted-foreground mb-3" />
              <h3 className="font-semibold text-sm">{cap.title}</h3>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{cap.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
