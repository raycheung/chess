import { useCallback, useEffect, useRef, useState } from 'react'
import type { ClientMessage, GameState, ServerMessage } from './protocol'

export type SignInProblem = 'denied' | 'retry'
const PROBLEMS: SignInProblem[] = ['denied', 'retry']

export function useGame() {
  const [state, setState] = useState<GameState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)
  const [signInProblem, setSignInProblem] = useState<SignInProblem | null>(null)
  const socket = useRef<WebSocket | null>(null)

  useEffect(() => {
    let retries = 0
    let attempt = 0
    let timer: number | undefined

    const connect = async () => {
      const current = ++attempt
      const auth = await fetch('/oauth2/auth').catch(() => null)
      if (current !== attempt) return
      const params = new URLSearchParams(location.search)
      const problem = PROBLEMS.find((p) => params.has(p))
      if (auth?.status === 401) {
        if (problem) return setSignInProblem(problem)
        location.href = `/oauth2/start?rd=${encodeURIComponent(location.pathname)}`
        return
      }
      if (problem) {
        PROBLEMS.forEach((p) => params.delete(p))
        history.replaceState(null, '', `${location.pathname}${params.size ? `?${params}` : ''}`)
      }
      const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${scheme}://${location.host}/ws${location.search}`)
      socket.current = ws
      ws.onopen = () => {
        retries = 0
        setConnected(true)
      }
      ws.onmessage = (event) => {
        const message: ServerMessage = JSON.parse(event.data)
        if (message.type === 'error') return setError(message.message)
        setState(message)
        setError(null)
      }
      ws.onclose = () => {
        if (socket.current !== ws) return
        setConnected(false)
        timer = window.setTimeout(connect, Math.min(1000 * 2 ** retries++, 10000))
      }
    }

    // iOS Safari silently kills sockets in the background, so always start fresh on return
    const reconnectNow = () => {
      if (document.visibilityState !== 'visible') return
      clearTimeout(timer)
      const old = socket.current
      socket.current = null
      old?.close()
      retries = 0
      connect()
    }

    const onPageShow = (e: PageTransitionEvent) => e.persisted && reconnectNow()

    connect()
    document.addEventListener('visibilitychange', reconnectNow)
    window.addEventListener('online', reconnectNow)
    window.addEventListener('pageshow', onPageShow)
    return () => {
      attempt++
      clearTimeout(timer)
      document.removeEventListener('visibilitychange', reconnectNow)
      window.removeEventListener('online', reconnectNow)
      window.removeEventListener('pageshow', onPageShow)
      const ws = socket.current
      socket.current = null
      ws?.close()
    }
  }, [])

  const send = useCallback((message: ClientMessage) => socket.current?.send(JSON.stringify(message)), [])

  const clearError = useCallback(() => setError(null), [])

  return { state, error, connected, signInProblem, send, clearError }
}
