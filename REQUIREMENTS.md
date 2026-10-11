# Chess — Requirements

## Players
- Only two people can play: the two boys.
- Each player must sign in before seeing the game. Anyone else is turned away.
- The game always shows who is playing white and who is playing black.
- A player's seat belongs to them for the whole game. Signing in again, reloading, or opening the game on another device resumes the same game with the same colour.
- One player can never play both sides. The player who started a game cannot also join it as the opponent.

## Starting a game
- There is only ever one game at a time.
- Either player can start a new game. When starting, they choose whether to move first as white or second as black. The other player takes the remaining colour.
- Until the other player joins, the starter may restart the game freely.
- Once both players have joined, the game is locked. No one can start a new game until this one ends.

## Playing
- Players take turns, white first. A player can only move their own pieces, and only on their turn.
- Selecting a piece highlights the squares it can legally move to.
- Only legal chess moves are accepted, including castling, en passant and pawn promotion. When a pawn promotes, the player chooses the piece.
- Each player sees their own pieces at the bottom of the board.
- Both players see every move immediately, without refreshing the page.
- The last move made is highlighted.
- A player whose king is in check is told so.

## Undo
- During a game, either player can ask to undo.
- The opponent is asked to accept or decline. Nothing changes unless they accept.
- If they accept, the game goes back to the requester's last turn so the requester can move again.
- A pending undo request is cancelled if a move is made or the opponent declines.
- Undo is not available after the game has ended.

## Draw offer
- During a game, either player can offer a draw.
- The opponent is asked to accept or decline. If they accept, the game ends as a draw.
- A pending offer is cancelled if a move is made or the opponent declines.
- Only one undo request or draw offer can be waiting at a time.

## Ending a game
- A game ends in one of these ways:
  - checkmate, which is a win
  - resignation, which is a win for the opponent
  - a draw by agreement
  - a draw by stalemate, the fifty-move rule, insufficient material, or the same position occurring three times
- When a game ends, both players see the result and why it ended.
- The next game can then be started by either player, who again chooses their colour.

## Score
- Every finished game is recorded with its date, players, colours and result.
- The running score between the two players is shown and is kept permanently, even if the server restarts.
- A game still in progress may be lost if the server restarts.

## iPhone
- The game is played mainly on iPhone in Safari, held upright.
- The board fills the screen width with no zooming or sideways scrolling, and every square is easy to tap.
- Moves are made by tapping: tap a piece, then tap where it should go. Tapping the piece again cancels.
- Buttons stay reachable with one thumb and never cover the board.
- The game can be added to the Home Screen and then opens full screen like an app, with its own icon.
- When a player switches away and comes back, or the phone sleeps and wakes, the board catches up to the current position on its own, with no manual refresh.
- The game also works on a computer browser.

## Access
- The game is reached at its own web address, separate from other services.
