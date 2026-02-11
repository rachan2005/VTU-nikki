import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  CheckCircle2,
  Rocket,
  AlertTriangle,
  Eye,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import PlausibilityGauge from '@/components/PlausibilityGauge'
import EntryCard from '@/components/EntryCard'
import Modal from '@/components/Modal'
import { useModal } from '@/lib/useModal'
import { approveAndSubmit, type DiaryEntry, type PreviewResponse } from '@/lib/api'

export default function Preview() {
  const navigate = useNavigate()
  const { modalState, showAlert, closeModal } = useModal()
  const [data, setData] = useState<PreviewResponse | null>(null)
  const [entries, setEntries] = useState<DiaryEntry[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [dryRun, setDryRun] = useState(false)
  const [launching, setLaunching] = useState(false)
  const [showReport, setShowReport] = useState(true)

  useEffect(() => {
    const stored = sessionStorage.getItem('preview_data')
    if (stored) {
      const parsed = JSON.parse(stored) as PreviewResponse
      setData(parsed)
      setEntries(parsed.entries)
      // Auto-select all
      setSelected(new Set(parsed.entries.map((e) => e.id)))
    }
  }, [])

  const toggleEntry = (id: string) => {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelected(next)
  }

  const selectAll = () => {
    if (selected.size === entries.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(entries.map((e) => e.id)))
    }
  }

  const updateEntry = (updated: DiaryEntry) => {
    setEntries(entries.map((e) => (e.id === updated.id ? updated : e)))
  }

  const avgConfidence =
    entries.length > 0
      ? entries.reduce((s, e) => s + e.confidence, 0) / entries.length
      : 0

  const handleLaunch = async () => {
    if (selected.size === 0) return
    setLaunching(true)
    try {
      const approved = entries.filter((e) => selected.has(e.id))
      const res = await approveAndSubmit(data!.session_id, approved, dryRun)
      sessionStorage.setItem('progress_id', res.progress_id)
      sessionStorage.setItem('progress_total', String(approved.length))
      navigate('/launch')
    } catch (e: any) {
      showAlert(e.message || 'Launch failed', 'Error', 'error')
    } finally {
      setLaunching(false)
    }
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
        <Eye className="w-12 h-12 mb-4 opacity-20" />
        <p className="text-sm">No preview data. Generate entries first.</p>
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Preview & Approve</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {entries.length} entries generated &middot; {selected.size} selected
          </p>
        </div>
        <PlausibilityGauge score={avgConfidence} size="md" />
      </div>

      {/* Plausibility report */}
      {data.plausibility_report && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="border border-border rounded-xl overflow-hidden bg-card"
        >
          <button
            onClick={() => setShowReport(!showReport)}
            className="w-full flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-400" />
              <span className="text-sm font-medium">Plausibility Report</span>
              {data.plausibility_report.flags.length > 0 && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-orange-500/10 text-orange-400">
                  {data.plausibility_report.flags.length} flags
                </span>
              )}
            </div>
            {showReport ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
          </button>
          {showReport && (
            <div className="border-t border-border p-4 space-y-3">
              {data.plausibility_report.flags.map((flag, i) => (
                <div key={i} className="flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-orange-400 mt-0.5 shrink-0" />
                  <span className="text-xs text-muted-foreground">{flag}</span>
                </div>
              ))}
              {data.plausibility_report.flags.length === 0 && (
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                  <span className="text-xs text-muted-foreground">
                    All entries pass plausibility checks.
                  </span>
                </div>
              )}
              {data.warnings.map((w, i) => (
                <div key={`w-${i}`} className="flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-yellow-400 mt-0.5 shrink-0" />
                  <span className="text-xs text-muted-foreground">{w}</span>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Select all */}
      <div className="flex items-center justify-between">
        <button
          onClick={selectAll}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {selected.size === entries.length ? 'Deselect all' : 'Select all'}
        </button>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              className="rounded"
            />
            Dry run (no submission)
          </label>
        </div>
      </div>

      {/* Entry cards */}
      <div className="space-y-3">
        {entries.map((entry, i) => (
          <EntryCard
            key={entry.id}
            entry={entry}
            index={i}
            selected={selected.has(entry.id)}
            onToggle={() => toggleEntry(entry.id)}
            onUpdate={updateEntry}
          />
        ))}
      </div>

      {/* Launch button */}
      <motion.button
        onClick={handleLaunch}
        disabled={selected.size === 0 || launching}
        whileHover={{ scale: selected.size > 0 ? 1.01 : 1 }}
        whileTap={{ scale: 0.99 }}
        className={`
          w-full flex items-center justify-center gap-3 py-4 rounded-xl text-sm font-bold
          transition-all duration-300 sticky bottom-4
          ${
            selected.size > 0 && !launching
              ? 'bg-gradient-to-r from-red-600 to-orange-500 text-white shadow-2xl shadow-red-500/20'
              : 'bg-muted text-muted-foreground cursor-not-allowed'
          }
        `}
      >
        <Rocket className="w-4 h-4" />
        {launching
          ? 'Launching swarm...'
          : dryRun
            ? `Dry Run ${selected.size} Entries`
            : `Launch ${selected.size} Entries`}
      </motion.button>

      <Modal {...modalState} onClose={closeModal} />
    </div>
  )
}
