import { motion } from 'framer-motion'
import { getPlausibilityLevel } from '@/lib/utils'
import { AlertTriangle, Shield, Skull } from 'lucide-react'

interface Props {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showMessage?: boolean
}

export default function PlausibilityGauge({ score, size = 'md', showMessage = true }: Props) {
  const level = getPlausibilityLevel(score)
  const percentage = Math.round(score * 100)

  const dims = {
    sm: { w: 80, h: 80, stroke: 6, text: 'text-lg', icon: 14 },
    md: { w: 140, h: 140, stroke: 8, text: 'text-3xl', icon: 20 },
    lg: { w: 200, h: 200, stroke: 10, text: 'text-5xl', icon: 28 },
  }[size]

  const radius = (dims.w - dims.stroke) / 2
  const circumference = 2 * Math.PI * radius

  const getColor = () => {
    if (score >= 0.95) return '#ef4444'
    if (score >= 0.85) return '#f97316'
    if (score >= 0.7) return '#eab308'
    if (score >= 0.5) return '#3b82f6'
    return '#71717a'
  }

  const Icon = score >= 0.95 ? Skull : score >= 0.7 ? AlertTriangle : Shield

  return (
    <div className="flex flex-col items-center gap-3">
      <div className={`relative ${level.class}`} style={{ width: dims.w, height: dims.w }}>
        <svg width={dims.w} height={dims.w} className="-rotate-90">
          {/* Background circle */}
          <circle
            cx={dims.w / 2}
            cy={dims.w / 2}
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth={dims.stroke}
          />
          {/* Progress circle */}
          <motion.circle
            cx={dims.w / 2}
            cy={dims.w / 2}
            r={radius}
            fill="none"
            stroke={getColor()}
            strokeWidth={dims.stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference * (1 - score) }}
            transition={{ duration: 1.5, ease: 'easeOut' }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <Icon className={level.color} style={{ width: dims.icon, height: dims.icon }} />
          <motion.span
            className={`${dims.text} font-black ${level.color} tabular-nums`}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: 'spring', stiffness: 200 }}
          >
            {percentage}
          </motion.span>
        </div>
      </div>

      {/* Label */}
      <div className="text-center">
        <div className={`text-xs font-bold uppercase tracking-widest ${level.color}`}>
          {level.label}
        </div>
        {showMessage && (
          <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">{level.message}</p>
        )}
      </div>
    </div>
  )
}
