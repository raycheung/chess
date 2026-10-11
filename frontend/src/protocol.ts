export type Colour = 'white' | 'black'

export type GameState = {
  type: 'state'
  you: string
  phase: 'idle' | 'waiting' | 'playing' | 'finished'
  fen: string
  white: string | null
  black: string | null
  legalMoves: string[]
  check: boolean
  lastMove: [string, string] | null
  undoRequestedBy: string | null
  winner: Colour | null
  reason: string | null
  score: { wins: Record<string, number>; draws: number }
}

export type ServerMessage = GameState | { type: 'error'; message: string }

export type ClientMessage =
  | { type: 'start'; colour: Colour }
  | { type: 'join' }
  | { type: 'move'; uci: string }
  | { type: 'resign' }
  | { type: 'undo_request' }
  | { type: 'undo_reply'; accept: boolean }
