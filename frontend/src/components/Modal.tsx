import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertTriangle, Info, CheckCircle2, XCircle } from 'lucide-react'

const variantConfig = {
  info: { icon: Info, color: 'text-blue-400' },
  warning: { icon: AlertTriangle, color: 'text-orange-400' },
  error: { icon: XCircle, color: 'text-destructive' },
  success: { icon: CheckCircle2, color: 'text-green-400' },
}

interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  children?: React.ReactNode
  variant?: 'info' | 'warning' | 'error' | 'success'
  message?: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm?: () => void
  persistent?: boolean
}

export default function Modal({
  open,
  onClose,
  title,
  children,
  variant = 'info',
  message,
  confirmLabel = 'OK',
  cancelLabel = 'Cancel',
  onConfirm,
  persistent = false,
}: ModalProps) {
  const confirmRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (open) {
      setTimeout(() => confirmRef.current?.focus(), 100)
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !persistent) onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, persistent, onClose])

  const cfg = variantConfig[variant]
  const Icon = cfg.icon

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={() => !persistent && onClose()}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.15 }}
            className="relative bg-card border border-border rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            {!persistent && (
              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            {/* Icon + Title */}
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-xl bg-muted ${cfg.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              {title && <h3 className="text-sm font-semibold mt-1.5">{title}</h3>}
            </div>

            {/* Content */}
            {message && (
              <p className="text-sm text-muted-foreground leading-relaxed">{message}</p>
            )}
            {children}

            {/* Actions */}
            <div className="flex gap-2 justify-end pt-2">
              {onConfirm && (
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-medium bg-muted rounded-lg hover:bg-accent transition-colors"
                >
                  {cancelLabel}
                </button>
              )}
              <button
                ref={confirmRef}
                onClick={() => {
                  if (onConfirm) onConfirm()
                  else onClose()
                }}
                className="px-4 py-2 text-xs font-medium bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
              >
                {onConfirm ? confirmLabel : 'OK'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
