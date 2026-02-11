import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { format } from 'date-fns'
import {
  CalendarRange,
  Calendar as CalendarIcon,
  Loader2,
  Zap,
  ToggleLeft,
  ToggleRight,
  ArrowRight,
  Settings,
} from 'lucide-react'
import FileDropzone from '@/components/FileDropzone'
import CalendarPicker from '@/components/CalendarPicker'
import { isConfigured } from '@/lib/credentials'
import { uploadFile, uploadText, generatePreview } from '@/lib/api'

// Helper to get saved state
const getSavedState = () => {
  try {
    const saved = localStorage.getItem('upload_form_state')
    return saved ? JSON.parse(saved) : {}
  } catch {
    return {}
  }
}

export default function UploadPage() {
  const navigate = useNavigate()

  // Load saved state once
  const saved = getSavedState()

  // Initialize state with saved values or defaults
  const [inputMode, setInputMode] = useState<'file' | 'text'>(saved.inputMode || 'file')
  const [dateMode, setDateMode] = useState<'range' | 'calendar'>(saved.dateMode || 'calendar')
  const [file, setFile] = useState<File | null>(null)
  const [uploadId, setUploadId] = useState<string>(saved.uploadId || '')
  const [text, setText] = useState(saved.text || '')
  const [dateFrom, setDateFrom] = useState(saved.dateFrom || '')
  const [dateTo, setDateTo] = useState(saved.dateTo || '')
  const [selectedDates, setSelectedDates] = useState<Date[]>(
    saved.selectedDates?.length > 0
      ? saved.selectedDates.map((d: string) => new Date(d))
      : [new Date()]
  )
  const [skipWeekends, setSkipWeekends] = useState(saved.skipWeekends ?? true)
  const [skipHolidays, setSkipHolidays] = useState(saved.skipHolidays ?? true)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  // Save state to localStorage
  useEffect(() => {
    const state = {
      text,
      uploadId,
      dateFrom,
      dateTo,
      selectedDates: selectedDates.map((d) => d.toISOString()),
      inputMode,
      dateMode,
      skipWeekends,
      skipHolidays,
    }
    localStorage.setItem('upload_form_state', JSON.stringify(state))
  }, [text, uploadId, dateFrom, dateTo, selectedDates, inputMode, dateMode, skipWeekends, skipHolidays])

  // Auto-upload file when dropped
  const handleFileSelect = async (f: File) => {
    setFile(f)
    setUploading(true)
    try {
      const res = await uploadFile(f)
      setUploadId(res.upload_id)
    } catch (e: any) {
      setError(e.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const hasInput = inputMode === 'file' ? !!file || !!uploadId : text.trim().length > 10
  const hasDates = dateMode === 'range' ? dateFrom && dateTo : selectedDates.length > 0
  const canSubmit = hasInput && hasDates

  const handleGenerate = async () => {
    if (!canSubmit) return
    setLoading(true)
    setError('')

    try {
      let finalUploadId = uploadId

      // If file mode but no uploadId yet, upload now
      if (inputMode === 'file' && !uploadId && file) {
        const res = await uploadFile(file)
        finalUploadId = res.upload_id
        setUploadId(finalUploadId)
      }

      // If text mode, upload text
      if (inputMode === 'text') {
        const res = await uploadText(text)
        finalUploadId = res.upload_id
      }

      // Generate preview
      let dateRange: string
      if (dateMode === 'range') {
        dateRange = `${dateFrom} to ${dateTo}`
      } else {
        const sorted = selectedDates.sort((a, b) => a.getTime() - b.getTime())
        dateRange = sorted.map((d) => format(d, 'yyyy-MM-dd')).join(',')
      }

      const preview = await generatePreview(finalUploadId, dateRange, skipWeekends, skipHolidays)
      sessionStorage.setItem('preview_data', JSON.stringify(preview))
      navigate('/preview')
    } catch (e: any) {
      setError(e.message || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black tracking-tight">Feed the Machine</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload anything. It will figure out the rest.
        </p>
      </div>

      {/* Input mode toggle */}
      <div className="flex gap-2">
        {(['file', 'text'] as const).map((m) => (
          <button
            key={m}
            onClick={() => setInputMode(m)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              inputMode === m
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {m === 'file' ? 'File Upload' : 'Paste Text'}
          </button>
        ))}
      </div>

      {/* Input area */}
      <motion.div
        key={inputMode}
        initial={{ opacity: 0, x: inputMode === 'file' ? -20 : 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2 }}
      >
        {inputMode === 'file' ? (
          <div className="relative">
            <FileDropzone
              file={file}
              onFile={handleFileSelect}
              uploadId={uploadId}
              onClearUpload={() => {
                setUploadId('')
                setFile(null)
              }}
            />
            {uploading && (
              <div className="absolute inset-0 bg-background/80 backdrop-blur-sm rounded-xl flex items-center justify-center">
                <div className="flex items-center gap-2 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading...
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="relative">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your notes, git log output, meeting minutes, anything..."
              className="w-full h-48 bg-card border border-border rounded-xl p-4 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50 placeholder:text-muted-foreground/40"
            />
            <div className="absolute bottom-3 right-3 text-[10px] text-muted-foreground/50">
              {text.split(/\s+/).filter(Boolean).length} words
            </div>
          </div>
        )}
      </motion.div>

      {/* Date selection */}
      <div className="border border-border rounded-xl p-5 bg-card space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CalendarIcon className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">Select Dates</span>
          </div>

          <div className="flex gap-1 text-xs">
            {(['range', 'calendar'] as const).map((dm) => (
              <button
                key={dm}
                onClick={() => setDateMode(dm)}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  dateMode === dm
                    ? 'bg-muted text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {dm === 'range' ? (
                  <CalendarRange className="w-3.5 h-3.5" />
                ) : (
                  <CalendarIcon className="w-3.5 h-3.5" />
                )}
              </button>
            ))}
          </div>
        </div>

        <motion.div
          key={dateMode}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {dateMode === 'range' ? (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">From</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full bg-muted rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">To</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full bg-muted rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
            </div>
          ) : (
            <CalendarPicker
              selected={selectedDates}
              onSelect={setSelectedDates}
              skipWeekends={skipWeekends}
              skipHolidays={skipHolidays}
            />
          )}
        </motion.div>

        <div className="flex gap-6">
          <button
            onClick={() => setSkipWeekends(!skipWeekends)}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            {skipWeekends ? (
              <ToggleRight className="w-5 h-5 text-primary" />
            ) : (
              <ToggleLeft className="w-5 h-5" />
            )}
            Skip weekends
          </button>
          <button
            onClick={() => setSkipHolidays(!skipHolidays)}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            {skipHolidays ? (
              <ToggleRight className="w-5 h-5 text-primary" />
            ) : (
              <ToggleLeft className="w-5 h-5" />
            )}
            Skip holidays
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-destructive/10 border border-destructive/30 text-destructive rounded-lg px-4 py-3 text-sm"
        >
          {error}
        </motion.div>
      )}

      {/* Configure AI warning */}
      {!isConfigured() && (
        <div className="flex items-center gap-2 text-xs text-orange-400">
          <Settings className="w-3.5 h-3.5" />
          <span>No AI provider configured.</span>
          <Link to="/settings" className="underline hover:text-orange-300">
            Set up in Settings
          </Link>
        </div>
      )}

      {/* Generate button */}
      <button
        onClick={handleGenerate}
        disabled={!canSubmit || loading || uploading}
        className={`
          w-full flex items-center justify-center gap-3 py-4 rounded-xl text-sm font-bold
          transition-all duration-300
          ${
            canSubmit && !loading && !uploading
              ? 'bg-gradient-to-r from-red-600 to-orange-500 text-white hover:shadow-lg hover:shadow-red-500/25 hover:scale-[1.01]'
              : 'bg-muted text-muted-foreground cursor-not-allowed'
          }
        `}
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            AI is generating entries...
          </>
        ) : uploading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Uploading file...
          </>
        ) : (
          <>
            <Zap className="w-4 h-4" />
            Generate Entries
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>
    </div>
  )
}
