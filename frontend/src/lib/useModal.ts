import { useState, useCallback } from 'react'

interface ModalState {
  open: boolean
  title?: string
  message?: string
  variant?: 'info' | 'warning' | 'error' | 'success'
  onConfirm?: () => void
}

export function useModal() {
  const [state, setState] = useState<ModalState>({ open: false })

  const showAlert = useCallback(
    (message: string, title?: string, variant?: ModalState['variant']) => {
      setState({ open: true, message, title, variant: variant || 'info' })
    },
    []
  )

  const showConfirm = useCallback(
    (message: string, onConfirm: () => void, title?: string) => {
      setState({ open: true, message, title, onConfirm, variant: 'warning' })
    },
    []
  )

  const closeModal = useCallback(() => {
    setState({ open: false })
  }, [])

  return { modalState: state, showAlert, showConfirm, closeModal }
}
