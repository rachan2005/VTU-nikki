import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload,
  FileSpreadsheet,
  FileAudio,
  FileText,
  FileImage,
  FileVideo,
  GitBranch,
  File,
  CheckCircle2,
  X,
} from 'lucide-react'

interface Props {
  onFile: (file: File) => void
  file: File | null
  uploadId?: string
  onClearUpload?: () => void
}

const typeConfig: Record<string, { icon: typeof File; label: string; color: string }> = {
  'text/': { icon: FileText, label: 'Text', color: 'text-blue-400' },
  'audio/': { icon: FileAudio, label: 'Audio', color: 'text-purple-400' },
  'video/': { icon: FileVideo, label: 'Video', color: 'text-pink-400' },
  'image/': { icon: FileImage, label: 'Image', color: 'text-green-400' },
  'application/vnd.': { icon: FileSpreadsheet, label: 'Spreadsheet', color: 'text-emerald-400' },
  'application/pdf': { icon: FileText, label: 'PDF', color: 'text-red-400' },
}

function getFileConfig(file: File) {
  for (const [prefix, config] of Object.entries(typeConfig)) {
    if (file.type.startsWith(prefix)) return config
  }
  if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv'))
    return typeConfig['application/vnd.']
  if (file.name.endsWith('.git') || file.name.endsWith('.log'))
    return { icon: GitBranch, label: 'Git Log', color: 'text-orange-400' }
  return { icon: File, label: 'File', color: 'text-zinc-400' }
}

export default function FileDropzone({ onFile, file, uploadId, onClearUpload }: Props) {
  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) onFile(accepted[0])
  }, [onFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      'text/*': ['.txt', '.csv', '.log'],
      'audio/*': ['.mp3', '.wav', '.ogg', '.m4a', '.webm'],
      'video/*': ['.mp4', '.webm', '.avi'],
      'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
  })

  const hasUpload = file || uploadId

  return (
    <div
      {...getRootProps()}
      className={`
        relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
        transition-all duration-300 group
        ${isDragActive
          ? 'border-primary bg-primary/5 scale-[1.02]'
          : hasUpload
            ? 'border-green-500/30 bg-green-500/5'
            : 'border-border hover:border-primary/50 hover:bg-accent/50'
        }
      `}
    >
      <input {...getInputProps()} />

      <AnimatePresence mode="wait">
        {file ? (
          <motion.div
            key="file"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex flex-col items-center gap-3"
          >
            {(() => {
              const config = getFileConfig(file)
              const Icon = config.icon
              return (
                <>
                  <div className={`p-3 rounded-xl bg-card border border-border ${config.color}`}>
                    <Icon className="w-8 h-8" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {config.label} &middot; {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground">Click or drop to replace</p>
                </>
              )
            })()}
          </motion.div>
        ) : uploadId ? (
          <motion.div
            key="saved"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex flex-col items-center gap-3"
          >
            <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/30 text-green-500">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div>
              <p className="font-medium text-sm">Previous upload ready</p>
              <p className="text-xs text-muted-foreground">ID: {uploadId.slice(0, 8)}...</p>
            </div>
            <div className="flex gap-2 items-center">
              <p className="text-xs text-muted-foreground">Click to upload new file</p>
              {onClearUpload && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onClearUpload()
                  }}
                  className="p-1 rounded hover:bg-destructive/10 text-destructive transition-colors"
                  title="Clear upload"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-4"
          >
            <div className="p-4 rounded-2xl bg-muted/50 group-hover:bg-muted transition-colors">
              <Upload className="w-8 h-8 text-muted-foreground group-hover:text-foreground transition-colors" />
            </div>
            <div>
              <p className="font-medium text-sm">Drop anything here</p>
              <p className="text-xs text-muted-foreground mt-1">
                Voice memos, Excel logs, PDFs, photos of whiteboards, git logs, text files
              </p>
            </div>
            <div className="flex gap-2 flex-wrap justify-center">
              {[
                { icon: FileAudio, label: '.mp3' },
                { icon: FileSpreadsheet, label: '.xlsx' },
                { icon: FileText, label: '.pdf' },
                { icon: FileImage, label: '.jpg' },
                { icon: GitBranch, label: '.log' },
                { icon: FileText, label: '.txt' },
              ].map(({ icon: I, label }) => (
                <span
                  key={label}
                  className="flex items-center gap-1 text-[10px] text-muted-foreground/60 bg-muted/30 px-2 py-1 rounded-full"
                >
                  <I className="w-2.5 h-2.5" />
                  {label}
                </span>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
