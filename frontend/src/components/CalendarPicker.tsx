import { useState } from 'react'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import { X } from 'lucide-react'
import 'react-day-picker/dist/style.css'
import './calendar-picker.css'

interface Props {
  selected: Date[]
  onSelect: (dates: Date[]) => void
  skipWeekends?: boolean
  skipHolidays?: boolean
}

export default function CalendarPicker({ selected, onSelect, skipWeekends, skipHolidays }: Props) {
  const [lastClicked, setLastClicked] = useState<Date | null>(null)

  const handleDayClick = (day: Date, modifiers: any, e: React.MouseEvent) => {
    if (!day) return

    // Check if weekend
    if (skipWeekends && (day.getDay() === 0 || day.getDay() === 6)) {
      return
    }

    const selectedSet = new Set(selected.map((d) => d.getTime()))
    const dayTime = day.getTime()

    // Shift+click for range selection
    if (e.shiftKey && lastClicked) {
      const start = Math.min(lastClicked.getTime(), dayTime)
      const end = Math.max(lastClicked.getTime(), dayTime)

      const newDates = new Set(selectedSet)
      const current = new Date(start)

      while (current.getTime() <= end) {
        if (!skipWeekends || (current.getDay() !== 0 && current.getDay() !== 6)) {
          newDates.add(current.getTime())
        }
        current.setDate(current.getDate() + 1)
      }

      onSelect(Array.from(newDates).map((t) => new Date(t)))
    } else {
      // Regular click: toggle selection
      if (selectedSet.has(dayTime)) {
        selectedSet.delete(dayTime)
      } else {
        selectedSet.add(dayTime)
      }
      onSelect(Array.from(selectedSet).map((t) => new Date(t)))
      setLastClicked(day)
    }
  }

  const disabledDays = skipWeekends
    ? [{ dayOfWeek: [0, 6] }]
    : undefined

  return (
    <div className="calendar-picker-wrapper">
      <DayPicker
        mode="multiple"
        selected={selected}
        onDayClick={handleDayClick}
        disabled={disabledDays}
        modifiersClassNames={{
          selected: 'bg-primary text-primary-foreground',
          today: 'font-bold text-primary',
        }}
        className="rounded-xl border border-border bg-card p-4"
      />

      <div className="mt-3 flex items-center justify-between text-xs">
        <div className="space-y-1 text-muted-foreground">
          <div>Click dates • Shift+click for range</div>
          <div className="font-medium">
            {selected.length} dates selected
            {selected.length > 0 && (
              <span className="ml-2 text-[10px]">
                ({format(selected[0], 'MMM d')} to {format(selected[selected.length - 1], 'MMM d')})
              </span>
            )}
          </div>
        </div>
        {selected.length > 0 && (
          <button
            onClick={() => onSelect([])}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-muted hover:bg-accent text-muted-foreground hover:text-foreground rounded-md transition-colors"
          >
            <X className="w-3 h-3" /> Clear
          </button>
        )}
      </div>
    </div>
  )
}
