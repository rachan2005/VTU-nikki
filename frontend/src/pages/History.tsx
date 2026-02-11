import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  Search,
  Download,
  RefreshCw,
  RotateCw,
} from 'lucide-react'
import { getHistory, approveAndSubmit, type HistoryEntry, type DiaryEntry } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import PlausibilityGauge from '@/components/PlausibilityGauge'
import Modal from '@/components/Modal'
import { useModal } from '@/lib/useModal'

export default function HistoryPage() {
  const navigate = useNavigate()
  const { modalState, showAlert, closeModal } = useModal()
  const [entries, setEntries] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState(false)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'success' | 'failed'>('all')

  const loadHistory = async () => {
    setLoading(true)
    try {
      const res = await getHistory(100)
      setEntries(res.submissions)
    } catch {
      // Ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const filtered = entries.filter((e) => {
    if (filter !== 'all' && e.status !== filter) return false
    if (search) {
      const q = search.toLowerCase()
      return (
        e.date.includes(q) ||
        e.activities.toLowerCase().includes(q) ||
        e.learnings.toLowerCase().includes(q)
      )
    }
    return true
  })

  const totalSuccess = entries.filter((e) => e.status === 'success').length
  const totalFailed = entries.filter((e) => e.status === 'failed').length

  const handleExport = () => {
    const csv = [
      'Date,Hours,Activities,Learnings,Status,Confidence',
      ...filtered.map(
        (e) =>
          `"${e.date}",${e.hours},"${e.activities.replace(/"/g, '""')}","${e.learnings.replace(/"/g, '""')}","${e.status}",${e.confidence_score}`
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'diary_history.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleRetryFailed = async () => {
    const failedEntries = entries.filter((e) => e.status === 'failed')
    if (failedEntries.length === 0) return

    setRetrying(true)
    try {
      // Convert HistoryEntry to DiaryEntry format
      const retryEntries: DiaryEntry[] = failedEntries.map((e) => ({
        id: String(e.id),
        date: e.date,
        hours: e.hours,
        activities: e.activities,
        learnings: e.learnings,
        blockers: e.blockers || 'None',
        links: e.links || '',
        skills: Array.isArray(e.skills) ? e.skills : [],
        confidence: e.confidence_score || 0.8,
        editable: true,
      }))

      // Create temp session and submit
      const sessionId = 'retry-' + Date.now()
      const res = await approveAndSubmit(sessionId, retryEntries, false)

      // Navigate to progress
      sessionStorage.setItem('progress_id', res.progress_id)
      sessionStorage.setItem('progress_total', String(retryEntries.length))
      navigate('/launch')
    } catch (e: any) {
      showAlert(e.message || 'Retry failed', 'Error', 'error')
    } finally {
      setRetrying(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Submission History</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {entries.length} total &middot; {totalSuccess} successful &middot; {totalFailed} failed
          </p>
        </div>
        <div className="flex gap-2">
          {totalFailed > 0 && (
            <button
              onClick={handleRetryFailed}
              disabled={retrying}
              className="flex items-center gap-1.5 px-3 py-2 text-xs bg-destructive/10 text-destructive rounded-lg hover:bg-destructive/20 transition-colors disabled:opacity-50"
            >
              <RotateCw className={`w-3.5 h-3.5 ${retrying ? 'animate-spin' : ''}`} />
              Retry {totalFailed} Failed
            </button>
          )}
          <button
            onClick={loadHistory}
            className="p-2 rounded-lg hover:bg-accent transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 text-muted-foreground ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-1.5 px-3 py-2 text-xs bg-muted rounded-lg hover:bg-accent transition-colors"
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search entries..."
            className="w-full pl-9 pr-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
        <div className="flex gap-1">
          {(['all', 'success', 'failed'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-all ${
                filter === f
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <RefreshCw className="w-6 h-6 text-muted-foreground animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-muted-foreground">
          <Calendar className="w-12 h-12 mb-4 opacity-20" />
          <p className="text-sm">No entries found</p>
        </div>
      ) : (
        <div className="border border-border rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                  Date
                </th>
                <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                  Activities
                </th>
                <th className="text-center text-xs font-medium text-muted-foreground px-4 py-3">
                  Hours
                </th>
                <th className="text-center text-xs font-medium text-muted-foreground px-4 py-3">
                  Confidence
                </th>
                <th className="text-center text-xs font-medium text-muted-foreground px-4 py-3">
                  Status
                </th>
                <th className="text-right text-xs font-medium text-muted-foreground px-4 py-3">
                  Submitted
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry, i) => (
                <motion.tr
                  key={entry.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                  className="border-b border-border last:border-0 hover:bg-accent/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium">{formatDate(entry.date)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-xs text-muted-foreground truncate max-w-xs">
                      {entry.activities.substring(0, 80)}...
                    </p>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {entry.hours}h
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center">
                      <PlausibilityGauge
                        score={entry.confidence_score}
                        size="sm"
                        showMessage={false}
                      />
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {entry.status === 'success' ? (
                      <span className="inline-flex items-center gap-1 text-xs text-green-400">
                        <CheckCircle2 className="w-3 h-3" /> Success
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-red-400">
                        <XCircle className="w-3 h-3" /> Failed
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-xs text-muted-foreground">
                      {entry.submitted_at
                        ? new Date(entry.submitted_at).toLocaleString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '—'}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal {...modalState} onClose={closeModal} />
    </div>
  )
}
