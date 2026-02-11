import { motion } from 'framer-motion'
import { Globe, Loader2, Check, X, Navigation, PenTool, Send } from 'lucide-react'
import type { BrowserState } from '@/lib/api'

interface Props {
  browsers: BrowserState[]
}

const statusConfig: Record<string, { icon: typeof Globe; color: string; label: string }> = {
  idle: { icon: Globe, color: 'text-zinc-500', label: 'Idle' },
  navigating: { icon: Navigation, color: 'text-blue-400', label: 'Navigating' },
  filling: { icon: PenTool, color: 'text-yellow-400', label: 'Filling form' },
  submitting: { icon: Send, color: 'text-orange-400', label: 'Submitting' },
  success: { icon: Check, color: 'text-green-400', label: 'Done' },
  error: { icon: X, color: 'text-red-400', label: 'Failed' },
}

export default function BrowserSwarm({ browsers }: Props) {
  return (
    <div className="grid grid-cols-5 gap-3">
      {browsers.map((b) => {
        const config = statusConfig[b.status] || statusConfig.idle
        const Icon = config.icon
        const isActive = b.status === 'navigating' || b.status === 'filling' || b.status === 'submitting'

        return (
          <motion.div
            key={b.worker_id}
            animate={isActive ? { scale: [1, 1.03, 1] } : {}}
            transition={{ repeat: Infinity, duration: 1.5 }}
            className={`
              relative border rounded-xl p-4 flex flex-col items-center gap-2
              transition-all duration-300
              ${isActive ? 'border-primary/30 bg-primary/5' : 'border-border bg-card'}
            `}
          >
            {/* Spinner ring for active */}
            {isActive && (
              <div className="absolute inset-0 rounded-xl border-2 border-transparent border-t-primary/40 animate-spin" />
            )}

            <div className={`p-2 rounded-lg bg-muted/50 ${config.color}`}>
              {isActive ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Icon className="w-5 h-5" />
              )}
            </div>

            <div className="text-center">
              <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Worker {b.worker_id + 1}
              </div>
              <div className={`text-xs font-medium ${config.color}`}>{config.label}</div>
              {b.current_date && (
                <div className="text-[10px] text-muted-foreground mt-0.5">{b.current_date}</div>
              )}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
