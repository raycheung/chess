import { useEffect, useState } from 'react'
import { Board } from './Board'
import type { Colour, GameState } from './protocol'
import { useGame } from './useGame'

const REASONS: Record<string, string> = {
  checkmate: 'by checkmate',
  resignation: 'by resignation',
  stalemate: 'stalemate',
  'fifty-move rule': '50 moves, no captures',
  'insufficient material': 'not enough pieces to mate',
}

function seatOf(state: GameState): Colour | null {
  if (state.white === state.you) return 'white'
  if (state.black === state.you) return 'black'
  return null
}

function PlayerBar({ name, colour, active, wins }: { name: string | null; colour: Colour; active: boolean; wins: number }) {
  return (
    <div className={`player ${active ? 'active' : ''}`}>
      <span className={`dot ${colour}`} />
      <span className="name">{name ?? '…'}</span>
      {name && <span className="wins">🏆 {wins}</span>}
    </div>
  )
}

function Confetti() {
  const [pieces] = useState(() =>
    Array.from({ length: 60 }, () => ({
      left: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 0.8}s`,
      animationDuration: `${2 + Math.random() * 2}s`,
    })),
  )
  const colours = ['#f472b6', '#22d3ee', '#a3e635', '#facc15', '#a78bfa']
  return (
    <div className="confetti" aria-hidden>
      {pieces.map((style, i) => (
        <i key={i} style={{ ...style, background: colours[i % colours.length] }} />
      ))}
    </div>
  )
}

export default function App() {
  const { state, error, connected, send, clearError } = useGame()
  const [confirmResign, setConfirmResign] = useState(false)

  useEffect(() => {
    if (!error) return
    const timer = setTimeout(clearError, 3000)
    return () => clearTimeout(timer)
  }, [error, clearError])

  if (!state) return <div className="splash">♞ Connecting…</div>

  const seat = seatOf(state)
  const myColour: Colour = seat ?? 'white'
  const opponentColour: Colour = myColour === 'white' ? 'black' : 'white'
  const turn: Colour = state.fen.split(' ')[1] === 'w' ? 'white' : 'black'
  const playing = state.phase === 'playing'
  const myTurn = playing && seat === turn
  const wins = (name: string | null) => (name ? state.score.wins[name] ?? 0 : 0)
  const undoFromOpponent = playing && state.undoRequestedBy !== null && state.undoRequestedBy !== state.you
  const iWon = state.phase === 'finished' && state.winner === seat

  const banner = (() => {
    if (state.phase === 'idle') return 'Pick a side to start a game'
    if (state.phase === 'waiting') {
      return seat ? 'Waiting for your opponent to join…' : `${state.white ?? state.black} wants to play!`
    }
    if (state.phase === 'finished') {
      const reason = REASONS[state.reason ?? ''] ?? state.reason
      if (!state.winner) return `🤝 Draw — ${reason}`
      return iWon ? `🏆 You win ${reason}! GG` : `${state[state.winner]} wins ${reason}. GG`
    }
    if (state.check) return myTurn ? '⚠️ CHECK! Save your king' : '⚠️ Check!'
    return myTurn ? 'Your move 🔥' : `${state[turn]} is thinking…`
  })()

  const startButtons = (
    <>
      <button className="btn white" onClick={() => send({ type: 'start', colour: 'white' })}>Play White ♔</button>
      <button className="btn black" onClick={() => send({ type: 'start', colour: 'black' })}>Play Black ♚</button>
    </>
  )

  const controls = (() => {
    if (state.phase === 'idle' || state.phase === 'finished') return startButtons
    if (state.phase === 'waiting') {
      if (seat) return startButtons
      return (
        <button className="btn primary" onClick={() => send({ type: 'join' })}>
          Join as {state.white ? 'Black ♚' : 'White ♔'}
        </button>
      )
    }
    if (!seat) return null
    if (undoFromOpponent) {
      return (
        <>
          <span className="ask">{state.undoRequestedBy} wants to undo</span>
          <button className="btn primary" onClick={() => send({ type: 'undo_reply', accept: true })}>Allow ↩</button>
          <button className="btn" onClick={() => send({ type: 'undo_reply', accept: false })}>Nope</button>
        </>
      )
    }
    return (
      <>
        <button
          className="btn"
          disabled={state.undoRequestedBy === state.you}
          onClick={() => send({ type: 'undo_request' })}
        >
          {state.undoRequestedBy === state.you ? 'Undo asked…' : 'Undo ↩'}
        </button>
        <button
          className={`btn ${confirmResign ? 'danger' : ''}`}
          onClick={() => {
            if (!confirmResign) return setConfirmResign(true)
            setConfirmResign(false)
            send({ type: 'resign' })
          }}
          onBlur={() => setConfirmResign(false)}
        >
          {confirmResign ? 'Really give up?' : 'Resign 🏳️'}
        </button>
      </>
    )
  })()

  return (
    <main className={`app ${myTurn ? 'my-turn' : ''}`}>
      <header>
        <h1>♞ Chess Arena</h1>
        <span className={`live ${connected ? 'on' : ''}`}>{connected ? 'LIVE' : 'reconnecting…'}</span>
      </header>

      <PlayerBar
        name={state[opponentColour]}
        colour={opponentColour}
        active={playing && turn === opponentColour}
        wins={wins(state[opponentColour])}
      />
      <div className="board-wrap">
        <Board
          fen={state.fen}
          flipped={myColour === 'black'}
          myColour={seat ? seat[0] as 'w' | 'b' : null}
          legalMoves={state.legalMoves}
          lastMove={state.lastMove}
          check={state.check}
          onMove={(uci) => send({ type: 'move', uci })}
        />
        {iWon && <Confetti />}
      </div>
      <PlayerBar
        name={state[myColour]}
        colour={myColour}
        active={playing && turn === myColour}
        wins={wins(state[myColour])}
      />

      <p className={`banner ${playing && state.check ? 'alert' : ''}`}>{banner}</p>
      {state.score.draws > 0 && <p className="draws">🤝 {state.score.draws} draws</p>}
      <nav className="controls">{controls}</nav>
      {error && <div className="toast" onClick={clearError}>{error}</div>}
    </main>
  )
}
