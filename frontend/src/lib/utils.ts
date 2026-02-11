import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-IN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function getPlausibilityLevel(score: number): {
  label: string
  color: string
  class: string
  message: string
} {
  if (score >= 0.95) {
    return {
      label: 'TERRIFYING',
      color: 'text-red-500',
      class: 'gauge-danger',
      message: 'This is indistinguishable from a real entry. You should be scared.',
    }
  }
  if (score >= 0.85) {
    return {
      label: 'DANGEROUS',
      color: 'text-orange-500',
      class: 'gauge-warning',
      message: 'Extremely convincing. An evaluator would need to try hard to doubt this.',
    }
  }
  if (score >= 0.7) {
    return {
      label: 'SOLID',
      color: 'text-yellow-500',
      class: 'gauge-warning',
      message: 'Passes casual inspection. Specific details add strong credibility.',
    }
  }
  if (score >= 0.5) {
    return {
      label: 'PASSABLE',
      color: 'text-blue-400',
      class: 'gauge-safe',
      message: 'Acceptable but generic. Consider adding more specific context.',
    }
  }
  return {
    label: 'WEAK',
    color: 'text-zinc-400',
    class: 'gauge-safe',
    message: 'Needs more input data to generate convincing entries.',
  }
}
