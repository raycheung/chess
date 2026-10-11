import { useEffect, useState } from 'react'
import { Board } from './Board'
import type { Colour, GameState } from './protocol'
import { type SignInProblem, useGame } from './useGame'

const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

const SIGN_IN_PROBLEMS: Record<SignInProblem, [string, string]> = {
  denied: ["🚫 This account isn't on the player list", 'Sign out to try a different account.'],
  retry: ["😵 Sign-in didn't finish", 'Tap Try again to sign in.'],
}

const REASONS: Record<string, string> = {
  checkmate: 'by checkmate',
  resignation: 'by resignation',
  stalemate: 'stalemate',
  'fifty-move rule': '50 moves, no captures',
  'insufficient material': 'not enough pieces to mate',
  'threefold repetition': 'same position 3 times',
  agreement: 'agreed',
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
  const { state, error, connected, signInProblem, send, clearError } = useGame()
  const [confirmResign, setConfirmResign] = useState(false)

  useEffect(() => {
    if (!error) return
    const timer = setTimeout(clearError, 3000)
    return () => clearTimeout(timer)
  }, [error, clearError])

  if (signInProblem) {
    return (
      <main className="app">
        <header>
          <h1>♞ Chess Arena</h1>
        </header>
        <div className="board-wrap">
          <Board fen={START_FEN} flipped={false} myColour={null} legalMoves={[]} lastMove={null} check={false} onMove={() => {}} />
        </div>
        <p className="banner">{SIGN_IN_PROBLEMS[signInProblem][0]}</p>
        <p className="draws">{SIGN_IN_PROBLEMS[signInProblem][1]}</p>
        <nav className="controls">
          <a className="btn primary" href="/oauth2/start?rd=/">Try again</a>
        </nav>
      </main>
    )
  }

  if (!state) return <div className="splash">♞ Connecting…</div>

  const seat = seatOf(state)
  const myColour: Colour = seat ?? 'white'
  const opponentColour: Colour = myColour === 'white' ? 'black' : 'white'
  const turn: Colour = state.fen.split(' ')[1] === 'w' ? 'white' : 'black'
  const playing = state.phase === 'playing'
  const myTurn = playing && seat === turn
  const wins = (name: string | null) => (name ? state.score.wins[name] ?? 0 : 0)
  const request = playing ? state.request : null
  const myRequest = request?.by === state.you ? request.kind : null
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
    if (request && !myRequest) {
      const undo = request.kind === 'undo'
      return (
        <>
          <span className="ask">{request.by} {undo ? 'wants to undo' : 'offers a draw 🤝'}</span>
          <button className="btn primary" onClick={() => send({ type: 'reply', accept: true })}>
            {undo ? 'Allow ↩' : 'Accept 🤝'}
          </button>
          <button className="btn" onClick={() => send({ type: 'reply', accept: false })}>
            {undo ? 'Nope' : 'Play on'}
          </button>
        </>
      )
    }
    return (
      <>
        <button className="btn" disabled={myRequest !== null} onClick={() => send({ type: 'request', kind: 'undo' })}>
          {myRequest === 'undo' ? 'Asked…' : 'Undo ↩'}
        </button>
        <button className="btn" disabled={myRequest !== null} onClick={() => send({ type: 'request', kind: 'draw' })}>
          {myRequest === 'draw' ? 'Offered…' : 'Draw? 🤝'}
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
          {confirmResign ? 'Sure?' : 'Resign 🏳️'}
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
      {state.score.draws > 0 && (
        <p className="draws">🤝 {state.score.draws} draw{state.score.draws === 1 ? '' : 's'}</p>
      )}
      <nav className="controls">{controls}</nav>
      {error && <div className="toast" onClick={clearError}>{error}</div>}
    </main>
  )
}
