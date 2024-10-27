# player.py

from typing import Any, Dict, List, Optional
from .card import Card
from .data_collector import DataCollector
from .hand_evaluator import HandEvaluator

class Player:
    """
    Represents a player in the poker game.

    Attributes:
        name (str): The name of the player.
        hand (List[Card]): The player's current hand.
        chips (int): The number of chips the player has.
        current_bet (float): The amount the player has bet in the current round.
        folded (bool): Indicates if the player has folded.
        all_in (bool): Indicates if the player is all-in.
        is_dealer (bool): Indicates if the player is the dealer.
        is_small_blind (bool): Indicates if the player is the small blind.
        is_big_blind (bool): Indicates if the player is the big blind.
        data_collector (DataCollector): The data collector instance.
        action_history (List[Dict[str, Any]]): History of player's actions.
        total_aggressive_actions (int): Count of aggressive actions.
        total_actions (int): Total number of actions taken.
        total_bluffs (int): Count of bluffs.
        total_possible_bluffs (int): Count of situations where bluffing is possible.
    """

    def __init__(
        self,
        name: str,
        chips: int = 1000,
        data_collector: Optional[DataCollector] = None
    ):
        self.name: str = name
        self.hand: List[Card] = []
        self.chips: int = chips
        self.current_bet: float = 0.0
        self.folded: bool = False
        self.all_in: bool = False
        self.is_dealer: bool = False
        self.is_small_blind: bool = False
        self.is_big_blind: bool = False

        self.data_collector = data_collector

        # Attributes for calculating aggression factor and bluff probability for human players
        self.action_history: List[Dict[str, Any]] = []
        self.total_aggressive_actions: int = 0
        self.total_actions: int = 0
        self.total_bluffs: int = 0
        self.total_possible_bluffs: int = 0

    def __repr__(self):
        return f"<Player {self.name}>"

    def reset_hand(self) -> None:
        """
        Resets the player's hand and betting status for a new round.
        """
        self.hand = []
        self.current_bet = 0.0
        self.folded = False
        self.all_in = False
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
        # Reset action history for the new hand
        self.action_history = []

    def receive_card(self, card: Card) -> None:
        """
        Adds a card to the player's hand.

        Parameters:
            card (Card): The card to add.
        """
        self.hand.append(card)

    def place_bet(self, amount: float) -> None:
        """
        Places a bet by reducing the player's chips and increasing their current bet.

        Parameters:
            amount (float): The amount to bet.
        """
        if amount > self.chips:
            raise ValueError(f"{self.name} does not have enough chips to bet {amount}.")
        self.chips -= amount
        self.current_bet += amount
        if self.chips == 0:
            self.all_in = True

    def fold(self) -> None:
        """
        Folds the player's hand.
        """
        self.folded = True

    def check(self) -> None:
        """
        Player chooses to check (no action required).
        """
        pass

    def call(self, amount: float) -> None:
        """
        Calls the current highest bet.

        Parameters:
            amount (float): The amount needed to call.
        """
        call_amount = amount - self.current_bet
        if call_amount > self.chips:
            # Player goes all-in if they cannot cover the full call amount
            self.place_bet(self.chips)
        else:
            self.place_bet(call_amount)

    def raise_bet(self, amount: float) -> None:
        """
        Raises the bet by a specified amount.

        Parameters:
            amount (float): The amount to raise.
        """
        self.place_bet(amount)

    def all_in_bet(self) -> None:
        """
        Player goes all-in with their remaining chips.
        """
        self.place_bet(self.chips)

    def win_pot(self, amount: float) -> None:
        """
        Adds the pot amount to the player's chips when they win.

        Parameters:
            amount (float): The amount won from the pot.
        """
        self.chips += amount

    def set_dealer(self, is_dealer: bool = True) -> None:
        """
        Sets the player's dealer status.

        Parameters:
            is_dealer (bool): True if the player is the dealer.
        """
        self.is_dealer = is_dealer

    def set_small_blind(self, is_small_blind: bool = True) -> None:
        """
        Sets the player's small blind status.

        Parameters:
            is_small_blind (bool): True if the player is the small blind.
        """
        self.is_small_blind = is_small_blind

    def set_big_blind(self, is_big_blind: bool = True) -> None:
        """
        Sets the player's big blind status.

        Parameters:
            is_big_blind (bool): True if the player is the big blind.
        """
        self.is_big_blind = is_big_blind

    def get_position(self, game_state: Dict[str, Any]) -> str:
        """
        Determines the player's position at the table.

        Parameters:
            game_state (dict): Information about the current game state.

        Returns:
            str: 'early', 'middle', or 'late'
        """
        total_players = len(game_state['active_players'])
        active_players = game_state['active_players']
        index = active_players.index(self)
        if index < total_players / 3:
            return 'early'
        elif index < 2 * total_players / 3:
            return 'middle'
        else:
            return 'late'

    def evaluate_hand_strength(self, game_state: Dict[str, Any]) -> float:
        """
        Evaluates the player's hand strength.

        Parameters:
            game_state (Dict[str, Any]): The current game state.

        Returns:
            float: Normalized hand strength between 0 and 1.
        """
        hand_rank_value, _ = HandEvaluator.evaluate_hand(self.hand, game_state['community_cards'])
        hand_strength = hand_rank_value / 10  # Normalize to 0.1 - 1.0
        return hand_strength

    def update_statistics(self, action: str, hand_strength: float) -> None:
        """
        Updates the player's action statistics for aggression and bluff calculations.

        Parameters:
            action (str): The action taken.
            hand_strength (float): The evaluated hand strength.
        """
        aggressive_actions = ['raise', 'all-in']
        self.total_actions += 1

        if action in aggressive_actions:
            self.total_aggressive_actions += 1

            # Check if it's a bluff (aggressive action with weak hand)
            if hand_strength < 0.3:
                self.total_bluffs += 1
            self.total_possible_bluffs += 1
        else:
            if hand_strength < 0.3:
                self.total_possible_bluffs += 1

    def calculate_aggression_factor(self) -> float:
        """
        Calculates the player's aggression factor.

        Returns:
            float: The aggression factor (aggressive actions / total actions).
        """
        if hasattr(self, 'aggression_factor'):
            return self.aggression_factor
        
        if self.total_actions == 0:
            return 0.0
        
        return self.total_aggressive_actions / self.total_actions

    def calculate_bluff_probability(self) -> float:
        """
        Calculates the player's bluff probability.

        Returns:
            float: The bluff probability (bluffs / possible bluff situations).
        """
        if hasattr(self, 'bluff_probability'):
            return self.bluff_probability
        
        if self.total_possible_bluffs == 0:
            return 0.0
        
        return self.total_bluffs / self.total_possible_bluffs

    def get_action(self, game_state: Dict[str, Any]) -> str:
        """
        Retrieves the player's action for the current turn.

        Parameters:
            game_state (dict): Information about the current game state.

        Returns:
            str: The action chosen by the player.
        """
        action = input(f"{self.name}, enter your action (fold, check, call, raise, all-in): ").lower()
        amount = 0.0
        if 'raise' in action:
            try:
                amount = float(input(f"Enter raise amount: "))
            except ValueError:
                amount = 0.0
        self.record_decision(game_state, action, amount)
        return action

    def record_decision(self, game_state: Dict[str, Any], action: str, amount: float) -> None:
        """
        Records the decision point data using the DataCollector, if available.

        Parameters:
            game_state (Dict[str, Any]): The current game state.
            action (str): The action taken.
            amount (float): The amount involved in the action.
        """
        if self.data_collector is None:
            return

        # Evaluate hand strength
        hand_strength = self.evaluate_hand_strength(game_state)

        # Update statistics
        self.update_statistics(action, hand_strength)

        # Calculate aggression factor and bluff probability
        aggression_factor = self.calculate_aggression_factor()
        bluff_probability = self.calculate_bluff_probability()
        
        data = {
            'player_name': self.name,
            'hand': [str(card) for card in self.hand],
            'community_cards': [str(card) for card in game_state['community_cards']],
            'stage': game_state['stage'],
            'position': self.get_position(game_state),
            'pot': game_state['pot'],
            'current_bet': game_state['current_bet'],
            'player_chips': self.chips,
            'aggression_factor': aggression_factor,
            'bluff_probability': bluff_probability,
            'action': action,
            'amount': amount,
            'player_current_bet': self.current_bet,
            'player_total_bet': self.current_bet + amount,
            'player_folded': self.folded,
            'player_all_in': self.all_in
        }

        # Record the data
        self.data_collector.record_decision_point(data)

    def __str__(self) -> str:
        """
        Returns a string representation of the player.

        Returns:
            str: The player's name and chip count.
        """
        return f"Player {self.name}: {self.chips} chips"

    def show_hand(self, hide_cards: bool = False) -> str:
        """
        Returns a string representation of the player's hand.

        Parameters:
            hide_cards (bool): If True, hides the cards (used for other players).

        Returns:
            str: The player's hand as a string.
        """
        if hide_cards:
            return "[Hidden Cards]"
        else:
            return ', '.join(str(card) for card in self.hand)
