import { credentialHeaders } from './credentials'

const BASE = '/api'

/** Inject client-side credentials into every fetch call */
function authFetch(url: string, opts: RequestInit = {}): Promise<Response> {
  const creds = credentialHeaders()
  const existing = (opts.headers || {}) as Record<string, string>
  return fetch(url, {
    ...opts,
    headers: { ...existing, ...creds },
  })
}

export interface DiaryEntry {
  id: string
  date: string
  hours: number
  activities: string
  learnings: string
  blockers: string
  links: string
  skills: string[]
  confidence: number
  plausibility?: number
  editable: boolean
}

export interface PreviewResponse {
  session_id: string
  entries: DiaryEntry[]
  total_entries: number
  high_confidence_count: number
  needs_review_count: number
  warnings: string[]
  plausibility_report: PlausibilityReport
}

export interface PlausibilityReport {
  overall_score: number
  avg_confidence: number
  flags: string[]
  entry_scores: { date: string; score: number; flags: string[] }[]
}

export interface ProgressData {
  total: number
  completed: number
  failed: number
  current: string
  status: 'processing' | 'completed' | 'failed'
  browser_states?: BrowserState[]
}

export interface BrowserState {
  worker_id: number
  status: 'idle' | 'navigating' | 'filling' | 'submitting' | 'success' | 'error'
  current_date?: string
}

export interface HistoryStats {
  total_submissions: number
  successful: number
  failed: number
  success_rate: number
}

export interface HistoryEntry {
  id: number
  date: string
  hours: number
  activities: string
  learnings: string
  blockers: string
  links: string
  skills: string[]
  status: string
  confidence_score: number
  submitted_at: string
}

export async function uploadFile(file: File): Promise<{ upload_id: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await authFetch(`${BASE}/upload-file`, { method: 'POST', body: form })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function uploadText(text: string): Promise<{ upload_id: string }> {
  const form = new FormData()
  form.append('text', text)
  const res = await authFetch(`${BASE}/upload-text`, { method: 'POST', body: form })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function generatePreview(
  uploadId: string,
  dateRange: string,
  skipWeekends: boolean,
  skipHolidays: boolean
): Promise<PreviewResponse> {
  const form = new FormData()
  form.append('upload_id', uploadId)
  form.append('date_range', dateRange)
  form.append('skip_weekends', String(skipWeekends))
  form.append('skip_holidays', String(skipHolidays))
  const res = await authFetch(`${BASE}/generate-preview`, { method: 'POST', body: form })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function approveAndSubmit(
  sessionId: string,
  entries: DiaryEntry[],
  dryRun: boolean
): Promise<{ progress_id: string }> {
  const res = await authFetch(`${BASE}/approve-and-submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      approved_entries: entries,
      dry_run: dryRun,
    }),
  })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function getProgress(progressId: string): Promise<ProgressData> {
  const res = await authFetch(`${BASE}/progress/${progressId}`)
  if (!res.ok) throw new Error('Failed to fetch progress')
  return res.json()
}

export async function getHistory(limit = 50): Promise<{ total: number; submissions: HistoryEntry[] }> {
  const res = await authFetch(`${BASE}/history?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch history')
  return res.json()
}

export async function getHistoryStats(): Promise<HistoryStats> {
  const res = await authFetch(`${BASE}/history/stats`)
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}
