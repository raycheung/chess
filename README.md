# Chess Arena

Two-player chess for the web, built to play on iPhone. See [REQUIREMENTS.md](REQUIREMENTS.md) for what it does and [LESSONS.md](LESSONS.md) for how it works.

## Run it locally

Two terminals:

```sh
cd backend
uv run pytest                                   # all rules + game tests
CHESS_DEV=1 uv run fastapi dev chess_app/main.py
```

```sh
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/?name=ann` and `http://localhost:5173/?name=bob` in two windows. On a phone on the same Wi-Fi, use the "Network" address `npm run dev` prints. `?name=` only works with `CHESS_DEV=1`; in production the name comes from the login.

## Layout

| Path | What lives there |
|------|------------------|
| `backend/chess_app/board.py` | The board as 64 squares, and FEN text ⇄ board |
| `backend/chess_app/rules.py` | Every chess rule: moves, check, mate, draws |
| `backend/chess_app/game.py` | The one game: seats, turns, undo, results |
| `backend/chess_app/main.py` | The web server: WebSocket `/ws` + the built frontend |
| `frontend/src/useGame.ts` | Talks to the server, reconnects when the phone wakes |
| `frontend/src/Board.tsx` | Draws the board, handles taps |
| `frontend/src/App.tsx` | Everything around the board: players, buttons, messages |
| `Containerfile` | Builds the frontend, then packs it with the server into one image |

## Deploy

Build the image from `Containerfile` and run it behind a reverse proxy that signs players in and passes each player's name to `/ws` in an `X-User` header. Mount a volume at `/data` to keep the results.
