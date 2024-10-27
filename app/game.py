from typing import List, Literal, Optional, Dict, Tuple
from .logger import logger
from .card import Card
from .deck import Deck
from .player import Player
from .ai import AIPlayer
from .hand_evaluator import HandEvaluator
from .data_collector import DataCollector

class Game:
    """
    Represents the poker game, managing players, rounds, and game flow.
    """

    def __init__(
        self,
        small_blind: float = 5.0,
        big_blind: float = 10.0,
        players: Optional[List[Player]] = None,
        data_collector: Optional[DataCollector] = None
    ):
        self.players: List[Player] = players or []
        self.deck: Deck = Deck()
        self.community_cards: List[Card] = []
        self.pot: float = 0.0
        self.current_bet: float = 0.0
        self.small_blind: float = small_blind
        self.big_blind: float = big_blind
        self.dealer_position: int = -1  # Will be set in rotate_positions
        self.game_stage: Literal[
            'pre-flop',
            'flop',
            'turn',
            'river'
        ] = 'pre-flop'
        self.active_players: List[Player] = []
        self.round_active: bool = False
        self.betting_phase: bool = False
        self.current_player_index: int = 0
        self.data_collector = data_collector or DataCollector()

    def __repr__(self):
        return "\n".join([f"{k.title()}: {v}" for k,v in self.get_game_state().items()])

    def add_player(self, player: Player) -> None:
        """
        Adds a player to the game.
        """
        player.data_collector = self.data_collector
        self.players.append(player)
        logger.info(f"Added player {player.name} with {player.chips} chips.")

    def remove_broke_players(self) -> None:
        """
        Removes players who have no chips left from the game.
        """
        self.players = [player for player in self.players if player.chips > 0]
        logger.info("Removed players with zero chips.")

    def rotate_positions(self) -> None:
        """
        Rotates the dealer button and updates blinds.
        """
        self.dealer_position = (self.dealer_position + 1) % len(self.players)
        # Reset roles
        for player in self.players:
            player.set_dealer(False)
            player.set_small_blind(False)
            player.set_big_blind(False)

        # Set new dealer
        dealer = self.players[self.dealer_position]
        dealer.set_dealer(True)

        # Set blinds
        num_players = len(self.players)
        small_blind_position = (self.dealer_position + 1) % num_players
        big_blind_position = (self.dealer_position + 2) % num_players
        self.players[small_blind_position].set_small_blind(True)
        self.players[big_blind_position].set_big_blind(True)

        logger.info(f"Dealer is {dealer.name}.")
        logger.info(f"Small blind is {self.players[small_blind_position].name}.")
        logger.info(f"Big blind is {self.players[big_blind_position].name}.")

    def collect_blinds(self) -> None:
        """
        Collects blinds from the small blind and big blind players.
        """
        for player in self.players:
            if player.is_small_blind:
                blind_amount = min(self.small_blind, player.chips)
                player.place_bet(blind_amount)
                self.pot += blind_amount
                self.current_bet = blind_amount
                logger.info(f"{player.name} posts small blind of {blind_amount}.")
            elif player.is_big_blind:
                blind_amount = min(self.big_blind, player.chips)
                player.place_bet(blind_amount)
                self.pot += blind_amount
                self.current_bet = blind_amount
                logger.info(f"{player.name} posts big blind of {blind_amount}.")

    def start_new_round(self) -> None:
        """
        Starts a new round by resetting the deck, dealing hands, and collecting blinds.
        """
        self.remove_broke_players()
        if len(self.players) < 2:
            logger.info("Not enough players to continue the game.")
            self.round_active = False
            return

        self.deck = Deck()
        self.deck.cut()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0.0
        self.current_bet = 0.0
        self.game_stage = 'pre-flop'
        self.round_active = True
        self.betting_phase = True
        self.current_player_index = 0

        # Rotate dealer and blinds
        self.rotate_positions()

        # Reset players and deal hands
        self.active_players = [player for player in self.players if player.chips > 0]
        for player in self.active_players:
            player.reset_hand()
            player.receive_card(self.deck.deal())
            player.receive_card(self.deck.deal())
            logger.info(f"{player.name} receives two cards.")

        # Collect blinds
        self.collect_blinds()

    def get_game_state(self) -> Dict[str, any]:
        """
        Returns a dictionary containing the current game state.
        """
        return {
            'community_cards': self.community_cards,
            'current_bet': self.current_bet,
            'pot': self.pot,
            'players': self.players,
            'active_players': self.active_players,
            'stage': self.game_stage,
            'dealer_position': self.dealer_position,
            'current_bet': self.current_bet,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'betting_phase': self.betting_phase,
            'current_player_index': self.current_player_index,
            'round_active': self.round_active,
            'data_collector': self.data_collector.get_stats() if self.data_collector else None
        }

    def parse_action(self, action_str: str) -> Tuple[str, float]:
        """
        Parses the action string into an action and amount.
        """
        parts = action_str.lower().split()
        if 'fold' in parts:
            return 'fold', 0.0
        elif 'check' in parts:
            return 'check', 0.0
        elif 'call' in parts:
            return 'call', self.current_bet
        elif 'raise' in parts:
            # Extract the amount
            try:
                amount_index = parts.index('to') + 1
                amount = float(parts[amount_index])
            except (ValueError, IndexError):
                amount = self.current_bet * 2  # Default raise amount
            return 'raise', amount
        elif 'all-in' in parts:
            return 'all-in', 0.0
        else:
            return 'fold', 0.0  # Default action

    def betting_round(self) -> None:
        """
        Executes a betting round where players can fold, check, call, raise, or go all-in.
        """
        # Reset current bets for the new betting round
        for player in self.active_players:
            player.current_bet = 0.0

        # Build action order starting from the player after the dealer
        num_players = len(self.players)
        action_order = []
        index = (self.dealer_position + 1) % num_players
        while len(action_order) < len(self.active_players):
            player = self.players[index]
            if player in self.active_players and not player.folded and not player.all_in:
                action_order.append(player)
            index = (index + 1) % num_players

        # Keep track of players who have acted
        players_who_acted = set()

        while True:
            all_bets_equal = True
            for player in action_order:
                if player.folded or player.all_in:
                    continue

                # Check if all players have acted and bets are equal
                if players_who_acted == set(self.active_players) and all_bets_equal:
                    logger.info("Betting round complete.")
                    return

                # Prepare game state to pass to players
                game_state = self.get_game_state()

                # Get player's action
                action_str = player.get_action(game_state)
                action, amount = self.parse_action(action_str)
                logger.info(f"{player.name} decides to {action_str}")

                # Handle the player's action
                if action == 'fold':
                    player.fold()
                    logger.info(f"{player.name} folds.")
                    self.active_players.remove(player)
                elif action == 'check':
                    if player.current_bet < self.current_bet:
                        logger.warning(f"{player.name} cannot check and must call or fold.")
                        continue
                    logger.info(f"{player.name} checks.")
                elif action == 'call':
                    call_amount = self.current_bet - player.current_bet
                    if call_amount > player.chips:
                        call_amount = player.chips
                    player.call(self.current_bet)
                    self.pot += call_amount
                    logger.info(f"{player.name} calls {call_amount}.")
                elif action == 'raise':
                    raise_amount = amount - player.current_bet
                    if raise_amount > player.chips:
                        raise_amount = player.chips
                    player.raise_bet(amount)
                    self.current_bet = amount
                    self.pot += raise_amount
                    logger.info(f"{player.name} raises to {self.current_bet}.")
                    players_who_acted = set()  # Reset because the bet increased
                elif action == 'all-in':
                    all_in_amount = player.chips
                    player.all_in_bet()
                    self.pot += all_in_amount
                    self.current_bet = max(self.current_bet, player.current_bet)
                    logger.info(f"{player.name} goes all-in with {all_in_amount}.")
                    if player.chips == 0:
                        player.all_in = True
                else:
                    logger.warning(f"{player.name} performed an invalid action.")
                    continue

                players_who_acted.add(player)

                # Check if all active players have matched the current bet
                all_bets_equal = all(
                    p.folded or p.all_in or p.current_bet == self.current_bet
                    for p in self.active_players
                )
                if all_bets_equal and players_who_acted == set(self.active_players):
                    logger.info("Betting round complete.")
                    return

            # Remove folded players from action_order
            action_order = [p for p in action_order if not p.folded]
            # Check if only one player remains
            if len(action_order) <= 1:
                logger.info("Only one player remains. Betting round ends.")
                return

    def deal_community_cards(self, number: int) -> None:
        """
        Deals community cards onto the table.
        """
        for _ in range(number):
            card = self.deck.deal()
            self.community_cards.append(card)
            logger.info(f"Dealt community card: {card}")

    def play_round(self) -> None:
        """
        Manages the flow of a complete round of poker.
        """
        self.start_new_round()
        if not self.round_active:
            return

        logger.info("Starting a new round...")
        logger.info(f"Dealer is {self.players[self.dealer_position].name}")

        # Pre-flop betting round
        self.betting_round()

        # If more than one player remains, proceed to the flop
        if len(self.active_players) > 1:
            self.game_stage = 'flop'
            self.deal_community_cards(3)  # Flop
            self.betting_round()

        # If more than one player remains, proceed to the turn
        if len(self.active_players) > 1:
            self.game_stage = 'turn'
            self.deal_community_cards(1)  # Turn
            self.betting_round()

        # If more than one player remains, proceed to the river
        if len(self.active_players) > 1:
            self.game_stage = 'river'
            self.deal_community_cards(1)  # River
            self.betting_round()

        # Showdown if more than one player remains
        self.showdown()
        self.reset_round()

    def showdown(self) -> None:
        """
        Determines the winner(s) of the round and distributes the pot.
        """
        if len(self.active_players) > 1:
            winner = self.determine_winner()
            logger.info(f"The winner is {winner.name} with hand: {winner.show_hand()}")
            winner.win_pot(self.pot)
            logger.info(f"{winner.name} wins the pot of {self.pot} chips.")
        elif len(self.active_players) == 1:
            # Only one player remains, they win the pot
            winner = self.active_players[0]
            logger.info(f"{winner.name} wins the pot by default.")
            winner.win_pot(self.pot)
            logger.info(f"{winner.name} wins the pot of {self.pot} chips.")
        else:
            logger.info("All players have folded. No winner.")

    def determine_winner(self) -> Player:
        """
        Determines the winner among the remaining players.
        """
        evaluator = HandEvaluator()
        best_rank = 0
        best_hand = None
        winner = None
        for player in self.active_players:
            rank_value, highest_cards = evaluator.evaluate_hand(player.hand, self.community_cards)
            logger.info(f"{player.name} has a hand rank of {rank_value} with cards {highest_cards}.")
            if rank_value > best_rank or (rank_value == best_rank and highest_cards > best_hand):
                best_rank = rank_value
                best_hand = highest_cards
                winner = player
        return winner

    def reset_round(self) -> None:
        """
        Resets the game state for the next round.
        """
        self.community_cards = []
        self.pot = 0.0
        self.current_bet = 0.0
        self.game_stage = 'pre-flop'
        self.round_active = False
        self.betting_phase = False
        self.current_player_index = 0
        for player in self.players:
            player.reset_hand()
            player.current_bet = 0.0
            player.folded = False
            player.all_in = False
        logger.info("Round reset. Ready for the next round.")
