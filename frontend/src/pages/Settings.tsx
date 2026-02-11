import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  Key,
  User,
  Save,
  Eye,
  EyeOff,
  Shield,
  Trash2,
  CheckCircle2,
  Loader2,
  Download,
  Upload,
  AlertTriangle,
} from 'lucide-react'
import {
  getCredentials,
  saveCredentials,
  clearCredentials,
  exportCredentials,
  importCredentials,
  type Credentials,
} from '@/lib/credentials'
import Modal from '@/components/Modal'

const LLM_PROVIDERS = [
  { id: 'auto', label: 'Auto (fallback chain)' },
  { id: 'groq', label: 'Groq' },
  { id: 'gemini', label: 'Gemini' },
  { id: 'cerebras', label: 'Cerebras' },
  { id: 'openai', label: 'OpenAI' },
]

const API_KEY_FIELDS: { key: keyof Credentials; label: string; placeholder: string }[] = [
  { key: 'groq_api_key', label: 'Groq API Key', placeholder: 'gsk_...' },
  { key: 'gemini_api_key', label: 'Gemini API Key', placeholder: 'AIza...' },
  { key: 'cerebras_api_key', label: 'Cerebras API Key', placeholder: 'csk-...' },
  { key: 'openai_api_key', label: 'OpenAI API Key', placeholder: 'sk-...' },
]

export default function Settings() {
  const saved = getCredentials()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [form, setForm] = useState<Credentials>({ ...saved })
  const [showFields, setShowFields] = useState<Record<string, boolean>>({})
  const [saving, setSaving] = useState(false)
  const [showSaved, setShowSaved] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [importError, setImportError] = useState('')

  const update = (key: keyof Credentials, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const toggleShow = (key: string) => {
    setShowFields((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const handleSave = () => {
    setSaving(true)
    saveCredentials(form)
    setTimeout(() => {
      setSaving(false)
      setShowSaved(true)
      setTimeout(() => setShowSaved(false), 2000)
    }, 300)
  }

  const handleClear = () => {
    clearCredentials()
    setForm({})
    setShowClearConfirm(false)
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImportError('')
    try {
      const creds = await importCredentials(file)
      setForm({ ...creds })
      setShowSaved(true)
      setTimeout(() => setShowSaved(false), 2000)
    } catch (err: any) {
      setImportError(err.message || 'Import failed')
    }
    // Reset input so same file can be re-imported
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const hasChanges =
    JSON.stringify(form) !== JSON.stringify(saved)

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <div>
        <h1 className="text-2xl font-black tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Your credentials are stored locally in this browser only. Never sent to our servers.
        </p>
      </div>

      {/* Security notice */}
      <div className="flex items-start gap-3 px-4 py-3 bg-green-500/5 border border-green-500/20 rounded-xl">
        <Shield className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
        <p className="text-xs text-green-400 leading-relaxed">
          All credentials are stored in your browser's localStorage. They are passed directly to
          the backend API via request headers and never persisted on the server.
        </p>
      </div>

      {/* Session loss warning */}
      <div className="flex items-start gap-3 px-4 py-3 bg-orange-500/5 border border-orange-500/20 rounded-xl">
        <AlertTriangle className="w-4 h-4 text-orange-400 mt-0.5 shrink-0" />
        <div className="text-xs text-orange-400 leading-relaxed space-y-1">
          <p>
            <strong>Clearing browser data, using incognito mode, or switching browsers will lose your settings.</strong>
          </p>
          <p>
            Use <strong>Export</strong> below to save a backup file, and <strong>Import</strong> to restore on any device.
          </p>
        </div>
      </div>

      {/* LLM API Keys */}
      <div className="border border-border rounded-xl p-5 bg-card space-y-4">
        <div className="flex items-center gap-2">
          <Key className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">LLM API Keys</span>
          <span className="text-[10px] text-muted-foreground ml-auto">At least one required</span>
        </div>

        {/* Provider selector */}
        <div>
          <label className="text-xs text-muted-foreground mb-1.5 block">Preferred Provider</label>
          <div className="flex flex-wrap gap-1.5">
            {LLM_PROVIDERS.map((p) => (
              <button
                key={p.id}
                onClick={() => update('llm_provider', p.id)}
                className={`px-3 py-1.5 text-xs rounded-lg transition-all ${
                  (form.llm_provider || 'auto') === p.id
                    ? 'bg-primary text-primary-foreground font-medium'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* API key inputs */}
        {API_KEY_FIELDS.map(({ key, label, placeholder }) => (
          <div key={key}>
            <label className="text-xs text-muted-foreground mb-1 block">{label}</label>
            <div className="relative">
              <input
                type={showFields[key] ? 'text' : 'password'}
                value={form[key] || ''}
                onChange={(e) => update(key, e.target.value)}
                placeholder={placeholder}
                className="w-full bg-muted rounded-lg px-3 py-2 pr-10 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50 placeholder:text-muted-foreground/30"
              />
              <button
                onClick={() => toggleShow(key)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showFields[key] ? (
                  <EyeOff className="w-3.5 h-3.5" />
                ) : (
                  <Eye className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Portal Credentials */}
      <div className="border border-border rounded-xl p-5 bg-card space-y-4">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">VTU Portal Login</span>
          <span className="text-[10px] text-muted-foreground ml-auto">Required for submission</span>
        </div>

        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Email / Username</label>
          <input
            type="text"
            value={form.vtu_username || ''}
            onChange={(e) => update('vtu_username', e.target.value)}
            placeholder="your_vtu_email@example.com"
            className="w-full bg-muted rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 placeholder:text-muted-foreground/30"
          />
        </div>

        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Password</label>
          <div className="relative">
            <input
              type={showFields['vtu_password'] ? 'text' : 'password'}
              value={form.vtu_password || ''}
              onChange={(e) => update('vtu_password', e.target.value)}
              placeholder="Your VTU portal password"
              className="w-full bg-muted rounded-lg px-3 py-2 pr-10 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50 placeholder:text-muted-foreground/30"
            />
            <button
              onClick={() => toggleShow('vtu_password')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showFields['vtu_password'] ? (
                <EyeOff className="w-3.5 h-3.5" />
              ) : (
                <Eye className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={saving || !hasChanges}
          className={`
            flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold transition-all
            ${
              hasChanges && !saving
                ? 'bg-gradient-to-r from-red-600 to-orange-500 text-white hover:shadow-lg hover:shadow-red-500/25'
                : 'bg-muted text-muted-foreground cursor-not-allowed'
            }
          `}
        >
          {saving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : showSaved ? (
            <>
              <CheckCircle2 className="w-4 h-4" />
              Saved
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Settings
            </>
          )}
        </button>

        <button
          onClick={() => setShowClearConfirm(true)}
          className="px-4 py-3 text-xs font-medium bg-muted text-destructive rounded-xl hover:bg-destructive/10 transition-colors"
          title="Clear all credentials"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Export / Import */}
      <div className="border border-border rounded-xl p-5 bg-card space-y-3">
        <span className="text-sm font-medium">Backup & Restore</span>
        <p className="text-xs text-muted-foreground">
          Export your credentials as a JSON file to back them up or move to another browser/device.
        </p>
        <div className="flex gap-2">
          <button
            onClick={exportCredentials}
            className="flex items-center gap-2 px-4 py-2 text-xs font-medium bg-muted rounded-lg hover:bg-accent transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Export
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 px-4 py-2 text-xs font-medium bg-muted rounded-lg hover:bg-accent transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            Import
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleImport}
            className="hidden"
          />
        </div>
        {importError && (
          <p className="text-xs text-destructive">{importError}</p>
        )}
      </div>

      {/* Clear confirmation modal */}
      <Modal
        open={showClearConfirm}
        onClose={() => setShowClearConfirm(false)}
        title="Clear All Credentials"
        variant="warning"
        message="This will remove all saved API keys and portal credentials from this browser. You'll need to re-enter them."
        confirmLabel="Clear All"
        cancelLabel="Cancel"
        onConfirm={handleClear}
      />
    </div>
  )
}
