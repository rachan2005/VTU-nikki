import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  Rocket,
  CheckCircle2,
  XCircle,
  Loader2,
  PartyPopper,
  ArrowRight,
  RotateCw,
} from 'lucide-react'
import BrowserSwarm from '@/components/BrowserSwarm'
import { getProgress, type ProgressData, type BrowserState } from '@/lib/api'

export default function Progress() {
  const navigate = useNavigate()
  const [progress, setProgress] = useState<ProgressData | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const intervalRef = useRef<ReturnType<typeof setInterval>>()
  const logsEndRef = useRef<HTMLDivElement>(null)

  const progressId = sessionStorage.getItem('progress_id')
  const total = parseInt(sessionStorage.getItem('progress_total') || '0')

  // Mock browser states for visualization
  const [browsers, setBrowsers] = useState<BrowserState[]>(
    Array.from({ length: 5 }, (_, i) => ({
      worker_id: i,
      status: 'idle' as const,
    }))
  )

  useEffect(() => {
    if (!progressId) return

    const poll = async () => {
      try {
        const data = await getProgress(progressId)
        setProgress(data)

        // Add log entry
        if (data.current) {
          setLogs((prev) => {
            const last = prev[prev.length - 1]
            if (last !== data.current) return [...prev, data.current]
            return prev
          })
        }

        // Simulate browser states based on progress
        if (data.status === 'processing') {
          setBrowsers((prev) =>
            prev.map((b, i) => {
              const entryIdx = data.completed + i
              if (entryIdx >= data.total) return { ...b, status: 'idle' as const }
              const states: BrowserState['status'][] = ['navigating', 'filling', 'submitting']
              return {
                ...b,
                status: states[Math.floor(Math.random() * states.length)],
                current_date: `Entry ${entryIdx + 1}`,
              }
            })
          )
        } else if (data.status === 'completed') {
          setBrowsers((prev) =>
            prev.map((b) => ({ ...b, status: 'success' as const, current_date: undefined }))
          )
        }

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(intervalRef.current)
        }
      } catch {
        // Ignore polling errors
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 1500)
    return () => clearInterval(intervalRef.current)
  }, [progressId])

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const pct = progress ? Math.round((progress.completed / Math.max(progress.total, 1)) * 100) : 0
  const isDone = progress?.status === 'completed'
  const isFailed = progress?.status === 'failed'

  if (!progressId) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
        <Rocket className="w-12 h-12 mb-4 opacity-20" />
        <p className="text-sm">No active submission. Generate and approve entries first.</p>
        <button
          onClick={() => navigate('/upload')}
          className="mt-4 text-xs text-primary hover:underline"
        >
          Go to Upload
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        {isDone ? (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
          >
            <PartyPopper className="w-16 h-16 mx-auto text-green-400 mb-4" />
            <h1 className="text-3xl font-black">Mission Complete</h1>
            <p className="text-muted-foreground text-sm mt-1">
              {progress?.completed} entries submitted successfully
              {progress && progress.failed > 0 && `, ${progress.failed} failed`}
            </p>
          </motion.div>
        ) : isFailed ? (
          <div>
            <XCircle className="w-16 h-16 mx-auto text-red-400 mb-4" />
            <h1 className="text-3xl font-black">Submission Failed</h1>
            <p className="text-muted-foreground text-sm mt-1">{progress?.current}</p>
          </div>
        ) : (
          <div>
            <Loader2 className="w-12 h-12 mx-auto text-primary animate-spin mb-4" />
            <h1 className="text-2xl font-black">Swarm Active</h1>
            <p className="text-muted-foreground text-sm mt-1">{progress?.current}</p>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>
            {progress?.completed ?? 0} / {progress?.total ?? total}
          </span>
          <span>{pct}%</span>
        </div>
        <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${
              isDone
                ? 'bg-green-500'
                : isFailed
                  ? 'bg-red-500'
                  : 'bg-gradient-to-r from-red-500 to-orange-400'
            }`}
            initial={{ width: '0%' }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        {/* Completed/failed counts */}
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-1 text-green-400">
            <CheckCircle2 className="w-3 h-3" /> {progress?.completed ?? 0} done
          </span>
          {progress && progress.failed > 0 && (
            <span className="flex items-center gap-1 text-red-400">
              <XCircle className="w-3 h-3" /> {progress.failed} failed
            </span>
          )}
        </div>
      </div>

      {/* Browser swarm visualization */}
      {!isDone && !isFailed && <BrowserSwarm browsers={browsers} />}

      {/* Activity log */}
      <div className="border border-border rounded-xl bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <span className="text-xs font-medium text-muted-foreground">Activity Log</span>
        </div>
        <div className="max-h-64 overflow-y-auto p-4 space-y-1.5 font-mono text-xs">
          {logs.map((log, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-start gap-2"
            >
              <span className="text-muted-foreground/50 shrink-0 tabular-nums">
                {String(i + 1).padStart(3, '0')}
              </span>
              <span className="text-muted-foreground">{log}</span>
            </motion.div>
          ))}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Done actions */}
      {isDone && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex gap-3 justify-center"
        >
          {progress && progress.failed > 0 && (
            <button
              onClick={() => {
                navigate('/history')
                setTimeout(() => {
                  document.querySelector('[data-filter="failed"]')?.scrollIntoView({ behavior: 'smooth' })
                }, 500)
              }}
              className="flex items-center gap-2 px-5 py-2.5 bg-destructive/10 text-destructive rounded-lg text-sm font-medium hover:bg-destructive/20"
            >
              <RotateCw className="w-4 h-4" /> Retry {progress.failed} Failed
            </button>
          )}
          <button
            onClick={() => navigate('/history')}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90"
          >
            View History <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 px-5 py-2.5 bg-muted text-foreground rounded-lg text-sm font-medium hover:bg-accent"
          >
            Submit More
          </button>
        </motion.div>
      )}
    </div>
  )
}
