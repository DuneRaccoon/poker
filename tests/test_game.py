from app.game import Game
from app.player import Player
from app.ai import AIPlayer

# Create a game instance
game = Game(
    players=[
        Player(name="Ben"),
        AIPlayer(name="Bot1", personality='aggressive'),
        AIPlayer(name="Bot2", personality='passive'),
        AIPlayer(name="Bot2", personality='randomize')
    ]
)

# Play multiple rounds
for _ in range(10):
    game.play_round()
    # Check if the game should continue based on players' chips
    active_players = [player for player in game.players if player.chips > 0]
    if len(active_players) < 2:
        print("Game over. Not enough players with chips to continue.")
        break
