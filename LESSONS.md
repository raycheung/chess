# Lessons

Each lesson matches one part of the code. Read the lesson, open the file, then try the challenge.

## 1. A board is just a list of 64 things — `board.py`

The computer doesn't see a chessboard. It sees a list of 64 strings, numbered 0 to 63. Square `a1` is 0, `b1` is 1, … `h8` is 63. `"P"` is a white pawn, `"p"` a black one, `""` an empty square.

To turn a name like `e4` into a number: file `e` is 4 (counting from 0), rank `4` is row 3, so `4 + 8 × 3 = 28`.

**FEN** is a one-line way to write down a whole position, so it can be saved or sent over the network:

```
rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
```

The ranks run from 8 down to 1, digits mean "this many empty squares", then come whose turn it is, castling rights, the en passant square, and two move counters.

> **Try this:** what number is square `h1`? `a8`? Write a formula that turns a number back into a name.

To spot a **threefold repetition** (a draw), the game remembers every position and counts how many times the current one has appeared. Two positions are "the same" only if the pieces, whose turn it is, and castling rights all match.

> **Try this:** play knight out, knight back, twice each. On which move does the game end, and why that one?

## 2. Moves are arrows — `rules.py`

A knight's jumps are eight arrows: `(1, 2)`, `(2, 1)`, `(2, -1)` … meaning "one file right, two ranks up" and so on. A rook uses four arrows but keeps sliding until it hits something. A queen is just a rook plus a bishop.

The trick for check: to see whether a square is attacked, stand on it and look *outward* like each kind of piece. If you look like a knight and see an enemy knight, it's attacking you.

A move is **legal** only if, after making it, your own king isn't attacked. So we try every move and throw away the ones that leave the king in danger.

> **Try this:** find `KNIGHT` in `rules.py`. Why are there exactly 8 arrows? Draw them on paper.

## 3. Counting to check our work — `tests/test_perft.py`

How do we know the rules are right? We count. From the starting position:

| Moves ahead | Positions possible |
|---|---|
| 1 | 20 |
| 2 | 400 |
| 3 | 8,902 |
| 4 | 197,281 |

These numbers are famous: chess programmers everywhere agree on them. If our rules had a single bug (say, castling through check), the count would be off. This is called **perft**.

Notice how fast it grows: about 20× and then 22× each step. That's **exponential growth**, and it's why computers can't just "look at every possible game".

> **Try this:** 20 × 20 = 400 exactly. Why is the third number not 400 × 20 = 8,000? (Hint: what changes after a pawn moves?)

## 4. Tests are promises — `tests/test_rules.py`, `tests/test_game.py`

Each test is a tiny story: "set up this position, do this, the result must be that". Run `uv run pytest` and they all run in about 3 seconds. Change a rule by mistake and a test goes red immediately.

> **Try this:** break something on purpose. Delete `"K"` from `CASTLES` in `rules.py` and run the tests. Which ones fail? Put it back.

## 5. Client and server — `main.py`, `useGame.ts`

Your iPhone runs the **client** (the React app). The **server** runs on Dad's computer. They talk through a **WebSocket**: a phone line that stays open, so the server can call *you* the moment your brother moves. Normal web pages can only ask; they can't be told.

The messages are just JSON text:

```json
→ {"type": "move", "uci": "e2e4"}
← {"type": "state", "fen": "...", "lastMove": ["e2", "e4"], ...}
```

The server is the **referee**. The phone only *suggests* a move. The server checks it against the rules and, if it's legal, tells *both* phones the new position. That's why you can't cheat by editing the app.

> **Try this:** open Safari's Web Inspector (or Chrome DevTools → Network → WS) and watch the messages fly while you play.

## 6. Getting from the internet to the game

When you open https://chess.my-own-domain.com:

1. **DNS** turns `chess.my-own-domain.com` into Dad's IP address.
2. A **reverse proxy** answers. It shows a certificate (the 🔒) from **Let's Encrypt** proving it really is chess.my-own-domain.com, then encrypts everything (**TLS**).
3. The proxy asks a **login gate**: "Is this person signed in?" If not, you're sent to the family login page (**OpenID Connect**), and you only get through if you're on the player list.
4. The proxy passes the request on to the chess **container**, adding a note saying who you are (`X-User`). The game uses that note to know which side you're on.

> **Try this:** tap the 🔒 in Safari's address bar and look at the certificate. Who issued it? When does it expire?
