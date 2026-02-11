import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Clock,
  BookOpen,
  AlertCircle,
  Code2,
  ChevronDown,
  ChevronUp,
  Pencil,
  Check,
  X,
} from 'lucide-react'
import PlausibilityGauge from './PlausibilityGauge'
import { formatDate } from '@/lib/utils'
import type { DiaryEntry } from '@/lib/api'

interface Props {
  entry: DiaryEntry
  index: number
  selected: boolean
  onToggle: () => void
  onUpdate: (entry: DiaryEntry) => void
}

export default function EntryCard({ entry, index, selected, onToggle, onUpdate }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(entry)

  const save = () => {
    onUpdate(draft)
    setEditing(false)
  }

  const cancel = () => {
    setDraft(entry)
    setEditing(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`
        border rounded-xl overflow-hidden transition-all duration-200
        ${selected ? 'border-primary/50 bg-primary/5' : 'border-border bg-card'}
      `}
    >
      {/* Header row */}
      <div className="flex items-center gap-4 p-4">
        {/* Checkbox */}
        <button
          onClick={onToggle}
          className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all shrink-0 ${
            selected
              ? 'bg-primary border-primary'
              : 'border-muted-foreground/30 hover:border-primary/50'
          }`}
        >
          {selected && <Check className="w-3 h-3 text-primary-foreground" />}
        </button>

        {/* Date & hours */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm">{formatDate(entry.date)}</span>
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              {entry.hours}h
            </span>
          </div>
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {entry.activities.substring(0, 100)}...
          </p>
        </div>

        {/* Skills pills */}
        <div className="flex gap-1 shrink-0">
          {entry.skills.slice(0, 3).map((skill) => (
            <span
              key={skill}
              className="text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground"
            >
              {skill}
            </span>
          ))}
        </div>

        {/* Plausibility mini */}
        <PlausibilityGauge score={entry.confidence} size="sm" showMessage={false} />

        {/* Expand/Edit */}
        <div className="flex gap-1 shrink-0">
          <button
            onClick={() => setEditing(!editing)}
            className="p-1.5 rounded-md hover:bg-accent transition-colors"
          >
            <Pencil className="w-3.5 h-3.5 text-muted-foreground" />
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-md hover:bg-accent transition-colors"
          >
            {expanded ? (
              <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="border-t border-border"
        >
          <div className="p-4 space-y-4">
            {editing ? (
              /* Edit mode */
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">
                    Activities
                  </label>
                  <textarea
                    value={draft.activities}
                    onChange={(e) => setDraft({ ...draft, activities: e.target.value })}
                    className="w-full bg-muted rounded-lg p-3 text-sm resize-none h-32 focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                  <span className="text-[10px] text-muted-foreground">
                    {draft.activities.split(/\s+/).filter(Boolean).length} words
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1 block">
                      Learnings
                    </label>
                    <textarea
                      value={draft.learnings}
                      onChange={(e) => setDraft({ ...draft, learnings: e.target.value })}
                      className="w-full bg-muted rounded-lg p-3 text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1 block">
                      Blockers
                    </label>
                    <textarea
                      value={draft.blockers}
                      onChange={(e) => setDraft({ ...draft, blockers: e.target.value })}
                      className="w-full bg-muted rounded-lg p-3 text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <button
                    onClick={cancel}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-md hover:bg-accent transition-colors"
                  >
                    <X className="w-3 h-3" /> Cancel
                  </button>
                  <button
                    onClick={save}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
                  >
                    <Check className="w-3 h-3" /> Save
                  </button>
                </div>
              </div>
            ) : (
              /* View mode */
              <>
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <Code2 className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className="text-xs font-medium text-muted-foreground">Activities</span>
                  </div>
                  <p className="text-sm leading-relaxed">{entry.activities}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-muted-foreground" />
                      <span className="text-xs font-medium text-muted-foreground">Learnings</span>
                    </div>
                    <p className="text-sm">{entry.learnings}</p>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <AlertCircle className="w-3.5 h-3.5 text-muted-foreground" />
                      <span className="text-xs font-medium text-muted-foreground">Blockers</span>
                    </div>
                    <p className="text-sm">{entry.blockers}</p>
                  </div>
                </div>
              </>
            )}
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
