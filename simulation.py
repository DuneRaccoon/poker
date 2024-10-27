from app.logger import logger
from app.game import Game
from app.player import Player
from app.ai import AIPlayer
from app.data_collector import DataCollector

def get_game(ai_only: bool = True):
    data_collector = DataCollector()
    
    players = [
        AIPlayer(name='Bot1', chips=1000, personality='aggressive', data_collector=data_collector),
        AIPlayer(name='Bot2', chips=1000, personality='passive', data_collector=data_collector),
        AIPlayer(name='Bot3', chips=1000, personality='randomize', data_collector=data_collector),
        AIPlayer(name='Bot4', chips=1000, personality='randomize', data_collector=data_collector),
    ]
    
    if not ai_only:
        players.append(Player(name='You', chips=1000, data_collector=data_collector))
    
    return Game(data_collector=data_collector, players=players)

# game = get_game(ai_only=True)

def main(ai_only: bool = True):
    data_collector = DataCollector()

    players = [
        AIPlayer(name='Bot1', chips=1000, personality='aggressive', data_collector=data_collector),
        AIPlayer(name='Bot2', chips=1000, personality='passive', data_collector=data_collector),
        AIPlayer(name='Bot3', chips=1000, personality='randomize', data_collector=data_collector),
        AIPlayer(name='Bot4', chips=1000, personality='randomize', data_collector=data_collector),
    ]
    
    if not ai_only:
        players.append(Player(name='You', chips=1000, data_collector=data_collector))
    
    game = Game(data_collector=data_collector, players=players)

    if ai_only:
        # Run simulations
        num_simulations = 10000
        for i in range(num_simulations):
            logger.info(f"Starting simulation {i+1}")
            game.play_round()
            if not game.round_active:
                logger.info("Game has ended due to insufficient players.")
                break
    else:
        # Run the game loop
        while True:
            game.play_round()
            if not game.round_active:
                break

    # Export the dataset
    data_collector.save_to_csv('poker_game_data.csv')

if __name__ == '__main__':
    main()
