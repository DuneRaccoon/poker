import random
from typing import Literal, Dict, Any, Tuple, List, Optional
from .player import Player
from .hand_evaluator import HandEvaluator

class AIPlayer(Player):
    """
    Represents an AI-controlled player in the poker game.

    Attributes:
        personality (str): The AI's playing style.
            Personality Types:
                'aggressive': Bets and raises frequently, applies pressure on opponents.
                'passive': Calls and checks more often, avoids confrontation.
                'balanced': A mix of aggressive and passive play, adapts to situations.
                'loose': Plays many hands, willing to gamble with weaker holdings.
                'tight': Plays few hands, waits for strong cards.
                
        aggression_factor (float): Adjusts the aggressiveness of the AI.
        bluff_probability (float): The probability that the AI will bluff.
        observed_players (Dict[str, Dict[str, Any]]): Information about other players' tendencies.
    """

    PERSONALITIES = ['aggressive', 'passive', 'balanced', 'loose', 'tight']

    def __init__(
        self,
        name: str,
        *args,
        chips: int = 1000,
        personality: Literal['aggressive', 'passive', 'balanced', 'loose', 'tight', 'randomize'] = 'randomize',
        **kwargs
    ):
        super().__init__(name, *args, chips, **kwargs)
        
        self.personality = personality
        if self.personality == 'randomize':
            self.personality = random.choice(self.PERSONALITIES)
            
        self.aggression_factor = self.set_aggression_factor()
        self.bluff_probability = self.set_bluff_probability()
        self.observed_players: Dict[str, Dict[str, Any]] = {}
        self.previous_actions: List[Dict[str, Any]] = []

    def set_aggression_factor(self) -> float:
        """
        Sets the aggression factor based on personality.
        """
        personality_factors = {
            'aggressive': 1.5,
            'passive': 0.5,
            'balanced': 1.0,
            'loose': 1.2,
            'tight': 0.8
        }
        return personality_factors.get(self.personality, 1.0)

    def set_bluff_probability(self) -> float:
        """
        Sets the bluff probability based on personality.
        """
        personality_bluffs = {
            'aggressive': 0.2,
            'passive': 0.05,
            'balanced': 0.1,
            'loose': 0.15,
            'tight': 0.05
        }
        return personality_bluffs.get(self.personality, 0.1)

    def update_observations(self, game_state: Dict[str, Any]) -> None:
        """
        Updates observations about other players based on game state.

        Parameters:
            game_state (dict): Information about the current game state.
        """
        for player in game_state['players']:
            if player.name == self.name:
                continue
            if player.name not in self.observed_players:
                self.observed_players[player.name] = {
                    'aggressiveness': 0.5,
                    'bluffing_tendency': 0.1,
                    'hands_played': 0,
                    'raises': 0,
                    'calls': 0,
                    'folds': 0
                }
            # Update observations based on player's actions
            # For simplicity, we'll increment counts based on observed actions
            last_action = player.last_action if hasattr(player, 'last_action') else None
            if last_action:
                self.observed_players[player.name]['hands_played'] += 1
                if 'raise' in last_action:
                    self.observed_players[player.name]['raises'] += 1
                elif 'call' in last_action:
                    self.observed_players[player.name]['calls'] += 1
                elif 'fold' in last_action:
                    self.observed_players[player.name]['folds'] += 1
            # Calculate aggressiveness and bluffing tendency
            total_actions = self.observed_players[player.name]['hands_played']
            if total_actions > 0:
                raises = self.observed_players[player.name]['raises']
                self.observed_players[player.name]['aggressiveness'] = raises / total_actions
                folds = self.observed_players[player.name]['folds']
                self.observed_players[player.name]['bluffing_tendency'] = folds / total_actions

    def decide_action(self, game_state: Dict[str, Any]) -> Tuple[str, float]:
        """
        Decides the action to take based on the game state.

        Parameters:
            game_state (dict): Information about the current game state.

        Returns:
            Tuple[str, float]: The action ('fold', 'check', 'call', 'raise', 'all-in') and the bet amount.
        """
        # Update observations about other players
        self.update_observations(game_state)

        # Evaluate hand strength
        hand_rank_value, highest_cards = HandEvaluator.evaluate_hand(self.hand, game_state['community_cards'])
        hand_strength = hand_rank_value / 10  # Normalize to 0.1 - 1.0

        # Adjust hand strength based on the stage of the game
        stage_multiplier = self.get_stage_multiplier(game_state)
        hand_strength *= stage_multiplier

        # Calculate pot odds
        pot = game_state['pot']
        current_bet = game_state['current_bet']
        call_amount = current_bet - self.current_bet
        pot_odds = call_amount / (pot + call_amount) if (pot + call_amount) > 0 else 0

        # Adjust hand strength based on position
        position = self.get_position(game_state)
        position_factor = self.get_position_factor(position)
        hand_strength *= position_factor

        # Adjust hand strength based on observed players
        hand_strength = self.adjust_hand_strength_based_on_observations(hand_strength, game_state)

        # Decide whether to bluff
        if self.should_bluff(hand_strength, game_state):
            action = self.choose_bluff_action(call_amount)
        else:
            action = self.choose_action_based_on_hand_strength(hand_strength, pot_odds, call_amount)

        # Store the action for observation purposes
        self.last_action = action[0]
        return action

    def get_stage_multiplier(self, game_state: Dict[str, Any]) -> float:
        """
        Adjusts hand strength based on the stage of the game (pre-flop, flop, turn, river).

        Parameters:
            game_state (dict): Information about the current game state.

        Returns:
            float: Multiplier to adjust hand strength.
        """
        stage = game_state['stage']  # 'pre-flop', 'flop', 'turn', 'river'
        stage_multipliers = {
            'pre-flop': 1.0,
            'flop': 1.2,
            'turn': 1.3,
            'river': 1.4
        }
        return stage_multipliers.get(stage, 1.0)

    def get_position(self, game_state: Dict[str, Any]) -> str:
        """
        Determines the player's position at the table.

        Parameters:
            game_state (dict): Information about the current game state.

        Returns:
            str: 'early', 'middle', or 'late'
        """
        total_players = len(game_state['players'])
        active_players = [p for p in game_state['players'] if not p.folded]
        index = active_players.index(self)
        if index < len(active_players) / 3:
            return 'early'
        elif index < 2 * len(active_players) / 3:
            return 'middle'
        else:
            return 'late'

    def get_position_factor(self, position: str) -> float:
        """
        Returns a multiplier based on the player's position.

        Parameters:
            position (str): The player's position ('early', 'middle', 'late').

        Returns:
            float: Position factor.
        """
        position_factors = {
            'early': 0.9,
            'middle': 1.0,
            'late': 1.1
        }
        return position_factors.get(position, 1.0)

    def adjust_hand_strength_based_on_observations(self, hand_strength: float, game_state: Dict[str, Any]) -> float:
        """
        Adjusts hand strength based on observations of other players.

        Parameters:
            hand_strength (float): The current evaluated hand strength.
            game_state (dict): Information about the current game state.

        Returns:
            float: Adjusted hand strength.
        """
        for player in game_state['players']:
            if player.name == self.name or player.folded:
                continue
            observed = self.observed_players.get(player.name, {})
            aggressiveness = observed.get('aggressiveness', 0.5)
            if aggressiveness > 0.7:
                # Be cautious if opponents are aggressive
                hand_strength *= 0.95
            elif aggressiveness < 0.3:
                # Exploit passive players
                hand_strength *= 1.05
        return hand_strength

    def should_bluff(self, hand_strength: float, game_state: Dict[str, Any]) -> bool:
        """
        Determines if the AI should attempt a bluff.

        Parameters:
            hand_strength (float): The evaluated strength of the AI's hand.
            game_state (dict): Information about the current game state.

        Returns:
            bool: True if the AI decides to bluff, False otherwise.
        """
        bluff_chance = random.random()
        if hand_strength < 0.3 and bluff_chance < self.bluff_probability:
            # Consider game context
            if self.is_good_bluff_spot(game_state):
                return True
        return False

    def is_good_bluff_spot(self, game_state: Dict[str, Any]) -> bool:
        """
        Determines if the current game state is a good opportunity to bluff.

        Parameters:
            game_state (dict): Information about the current game state.

        Returns:
            bool: True if it's a good spot to bluff, False otherwise.
        """
        active_players = [p for p in game_state['players'] if not p.folded and p.name != self.name]
        if len(active_players) == 1:
            # Bluffing heads-up can be effective
            return True
        # Check if all opponents are tight players
        tight_opponents = all(
            self.observed_players.get(p.name, {}).get('aggressiveness', 0.5) < 0.3 for p in active_players
        )
        return tight_opponents

    def choose_bluff_action(self, call_amount: float) -> Tuple[str, float]:
        """
        Chooses an action when bluffing.

        Parameters:
            call_amount (float): The amount required to call the current bet.

        Returns:
            Tuple[str, float]: The action and bet amount.
        """
        # Bluff by raising a significant amount
        raise_amount = min(self.chips, call_amount + random.uniform(0.5, 1.0) * self.chips * self.aggression_factor)
        return 'raise', raise_amount

    def choose_action_based_on_hand_strength(self, hand_strength: float, pot_odds: float, call_amount: float) -> Tuple[str, float]:
        """
        Chooses an action based on hand strength and pot odds.

        Parameters:
            hand_strength (float): The evaluated strength of the AI's hand.
            pot_odds (float): The calculated pot odds.
            call_amount (float): The amount required to call the current bet.

        Returns:
            Tuple[str, float]: The action and bet amount.
        """
        # Compare hand strength to pot odds
        if hand_strength >= pot_odds:
            # Favorable situation
            if hand_strength > 0.8:
                # Strong hand, consider raising
                raise_amount = min(self.chips, call_amount + pot_odds * self.chips * self.aggression_factor)
                return 'raise', raise_amount
            elif hand_strength > 0.5:
                # Medium strength hand
                if call_amount == 0:
                    return 'check', 0.0
                else:
                    return 'call', call_amount
            else:
                # Marginal hand
                if call_amount == 0:
                    return 'check', 0.0
                else:
                    return 'call', call_amount
        else:
            # Unfavorable situation
            if call_amount == 0:
                # No cost to check
                return 'check', 0.0
            else:
                # Decide to fold or call based on aggression
                if self.aggression_factor > 1.0 and random.random() < 0.3:
                    return 'call', call_amount
                else:
                    return 'fold', 0.0

    def get_action(self, game_state: Dict[str, Any]) -> str:
        """
        Overrides the base class method to return the AI's action.

        Parameters:
            game_state (dict): Information about the current game state.

        Returns:
            str: The action chosen by the AI player.
        """
        action, amount = self.decide_action(game_state)
        if action == 'fold':
            self.fold()
            return 'fold'
        elif action == 'check':
            self.check()
            return 'check'
        elif action == 'call':
            self.call(game_state['current_bet'])
            return f'call {amount}'
        elif action == 'raise':
            self.raise_bet(amount)
            game_state['current_bet'] = self.current_bet
            return f'raise to {self.current_bet}'
        elif action == 'all-in':
            self.all_in_bet()
            return 'all-in'
        else:
            return 'fold'  # Default action if none matched