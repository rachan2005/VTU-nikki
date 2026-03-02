/**
 * Client-side credential storage.
 * All secrets stay in the user's browser (localStorage).
 * Passed to backend via request headers on each API call.
 */

const STORAGE_KEY = 'vtu_credentials'

export interface Credentials {
  // LLM API keys
  groq_api_key?: string
  gemini_api_key?: string
  cerebras_api_key?: string
  openai_api_key?: string
  llm_provider?: string

  // Portal credentials
  vtu_username?: string
  vtu_password?: string
}

export function getCredentials(): Credentials {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export function saveCredentials(creds: Credentials): void {
  const existing = getCredentials()
  const merged = { ...existing, ...creds }
  // Remove empty strings
  for (const key of Object.keys(merged) as (keyof Credentials)[]) {
    if (merged[key] === '') delete merged[key]
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(merged))
}

export function clearCredentials(): void {
  localStorage.removeItem(STORAGE_KEY)
}

export function hasAnyLLMKey(): boolean {
  const c = getCredentials()
  return !!(c.groq_api_key || c.gemini_api_key || c.cerebras_api_key || c.openai_api_key)
}

export function hasPortalCreds(): boolean {
  const c = getCredentials()
  return !!(c.vtu_username && c.vtu_password)
}

export function isConfigured(): boolean {
  return hasAnyLLMKey()
}

/**
 * Build headers object to inject credentials into API requests.
 * Backend reads these from X-* headers and uses them instead of env vars.
 */
export function credentialHeaders(): Record<string, string> {
  const c = getCredentials()
  const headers: Record<string, string> = {}

  if (c.groq_api_key) headers['X-Groq-Key'] = c.groq_api_key
  if (c.gemini_api_key) headers['X-Gemini-Key'] = c.gemini_api_key
  if (c.cerebras_api_key) headers['X-Cerebras-Key'] = c.cerebras_api_key
  if (c.openai_api_key) headers['X-Openai-Key'] = c.openai_api_key
  if (c.llm_provider) headers['X-LLM-Provider'] = c.llm_provider
  if (c.vtu_username) headers['X-Portal-User'] = c.vtu_username
  if (c.vtu_password) headers['X-Portal-Pass'] = c.vtu_password

  return headers
}

/**
 * Mask a secret for display (show last 4 chars).
 */
export function maskSecret(value?: string): string {
  if (!value) return ''
  if (value.length <= 4) return '****'
  return '*'.repeat(value.length - 4) + value.slice(-4)
}

/**
 * Export credentials as a downloadable JSON file for backup/recovery.
 */
export function exportCredentials(): void {
  const creds = getCredentials()
  if (!Object.keys(creds).length) return
  const blob = new Blob([JSON.stringify(creds, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'vtu-credentials.json'
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * Import credentials from a JSON file.
 */
export function importCredentials(file: File): Promise<Credentials> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const creds = JSON.parse(reader.result as string) as Credentials
        saveCredentials(creds)
        resolve(creds)
      } catch {
        reject(new Error('Invalid credentials file'))
      }
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsText(file)
  })
}
