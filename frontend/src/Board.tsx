import { useState } from 'react'

const FILES = 'abcdefgh'

const squareName = (index: number) => `${FILES[index % 8]}${Math.floor(index / 8) + 1}`

function parsePlacement(fen: string): string[] {
  const squares: string[] = Array(64).fill('')
  fen.split(' ')[0].split('/').forEach((rankText, row) => {
    let file = 0
    for (const char of rankText) {
      if (/\d/.test(char)) file += Number(char)
      else squares[(7 - row) * 8 + file++] = char
    }
  })
  return squares
}

const pieceImage = (piece: string) =>
  `/pieces/${piece === piece.toUpperCase() ? 'w' : 'b'}${piece.toUpperCase()}.svg`

type Props = {
  fen: string
  flipped: boolean
  myColour: 'w' | 'b' | null
  legalMoves: string[]
  lastMove: [string, string] | null
  check: boolean
  onMove: (uci: string) => void
}

export function Board({ fen, flipped, myColour, legalMoves, lastMove, check, onMove }: Props) {
  const [selected, setSelected] = useState<string | null>(null)
  const [promoting, setPromoting] = useState<string | null>(null)
  const [selectedFen, setSelectedFen] = useState(fen)

  if (selectedFen !== fen) {
    setSelectedFen(fen)
    setSelected(null)
    setPromoting(null)
  }

  const squares = parsePlacement(fen)
  const turn = fen.split(' ')[1]
  const myMoves = myColour === turn ? legalMoves : []
  const targets = new Set(myMoves.filter((m) => m.startsWith(selected ?? '-')).map((m) => m.slice(2, 4)))
  const checkedKing = check ? squareName(squares.indexOf(turn === 'w' ? 'K' : 'k')) : null
  const order = [...Array(64).keys()].map((i) => {
    const row = Math.floor(i / 8)
    const col = i % 8
    return flipped ? row * 8 + 7 - col : (7 - row) * 8 + col
  })

  const tap = (name: string) => {
    if (selected && targets.has(name)) {
      const uci = selected + name
      if (myMoves.includes(uci + 'q')) return setPromoting(uci)
      return onMove(uci)
    }
    setSelected(name !== selected && myMoves.some((m) => m.startsWith(name)) ? name : null)
  }

  return (
    <div className="board">
      {order.map((index) => {
        const name = squareName(index)
        const piece = squares[index]
        const dark = (index % 8 + Math.floor(index / 8)) % 2 === 0
        const classes = [
          'square',
          dark ? 'dark' : 'light',
          name === selected && 'selected',
          lastMove?.includes(name) && 'last',
          name === checkedKing && 'checked',
          targets.has(name) && (piece ? 'capture' : 'target'),
        ].filter(Boolean).join(' ')
        return (
          <button key={name} className={classes} onClick={() => tap(name)} aria-label={name}>
            {piece && (
              <img
                key={`${piece}${lastMove?.[1] === name ? lastMove.join('') : ''}`}
                className={lastMove?.[1] === name ? 'piece arrived' : 'piece'}
                src={pieceImage(piece)}
                alt={piece}
                draggable={false}
              />
            )}
          </button>
        )
      })}
      {promoting && (
        <div className="promotion">
          {'qrbn'.split('').map((kind) => (
            <button key={kind} onClick={() => onMove(promoting + kind)}>
              <img src={pieceImage(myColour === 'w' ? kind.toUpperCase() : kind)} alt={kind} />
            </button>
          ))}
          <button className="cancel" onClick={() => setPromoting(null)}>✕</button>
        </div>
      )}
    </div>
  )
}
