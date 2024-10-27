from collections import Counter
from itertools import combinations
from typing import List, Tuple, Dict, Optional

from .card import Card

class HandEvaluator:
    """
    A class to evaluate poker hands according to standard poker hand rankings.
    """
    
    HAND_RANKS: Dict[str, int] = {
        'High Card': 1,
        'One Pair': 2,
        'Two Pair': 3,
        'Three of a Kind': 4,
        'Straight': 5,
        'Flush': 6,
        'Full House': 7,
        'Four of a Kind': 8,
        'Straight Flush': 9,
        'Royal Flush': 10,
    }
    
    RANK_TO_HAND: Dict[int, str] = {v: k for k, v in HAND_RANKS.items()}

    @staticmethod
    def evaluate_hand(hand: List[Card], community_cards: List[Card]) -> Tuple[int, List[int]]:
        """
        Evaluates the best poker hand from the player's hand and community cards.

        Parameters:
            hand (List[Card]): List of Card objects representing the player's hand.
            community_cards (List[Card]): List of Card objects on the table.

        Returns:
            Tuple[int, List[int]]: A tuple containing the hand rank value and a list of highest card ranks for tie-breaking.
        """
        # Combine player hand and community cards
        all_cards: List[Card] = hand + community_cards

        # Generate all possible 5-card combinations
        possible_hands = combinations(all_cards, 5)

        best_rank: int = 0
        best_hand: Optional[List[int]] = None

        # Iterate through all possible 5-card hands to find the best one
        for possible_hand in possible_hands:
            rank, highest_cards = HandEvaluator.evaluate_five_card_hand(possible_hand)
            # Compare hands based on rank and then highest cards
            if rank > best_rank or (rank == best_rank and highest_cards > best_hand):
                best_rank = rank
                best_hand = highest_cards

        return best_rank, best_hand

    @staticmethod
    def evaluate_five_card_hand(cards: Tuple[Card, ...]) -> Tuple[int, List[int]]:
        """
        Evaluates a single 5-card poker hand.

        Parameters:
            cards (Tuple[Card, ...]): Tuple of 5 Card objects.

        Returns:
            Tuple[int, List[int]]: A tuple containing the hand rank value and a list of highest card ranks for tie-breaking.
        """
        # Extract ranks and suits
        ranks: List[int] = [Card.RANKS[card.rank] for card in cards]
        suits: List[str] = [card.suit for card in cards]
        rank_counts: Counter = Counter(ranks)
        suit_counts: Counter = Counter(suits)

        is_flush: bool = HandEvaluator.is_flush(suit_counts)
        is_straight, straight_high = HandEvaluator.is_straight(ranks)

        # Check for Straight Flush and Royal Flush
        if is_flush and is_straight:
            if straight_high == 14:
                return (HandEvaluator.HAND_RANKS['Royal Flush'], [14])
            else:
                return (HandEvaluator.HAND_RANKS['Straight Flush'], [straight_high])

        # Check for Four of a Kind
        if 4 in rank_counts.values():
            four_rank = HandEvaluator.get_rank_by_count(rank_counts, 4)
            kicker = HandEvaluator.get_high_cards(ranks, exclude=[four_rank])
            return (HandEvaluator.HAND_RANKS['Four of a Kind'], [four_rank] + kicker)

        # Check for Full House
        if 3 in rank_counts.values():
            three_ranks = HandEvaluator.get_ranks_by_count(rank_counts, 3)
            remaining_ranks = [rank for rank in rank_counts if rank_counts[rank] >= 2 and rank not in three_ranks]
            if remaining_ranks:
                # Use the highest three of a kind and the highest pair
                three_rank = max(three_ranks)
                pair_rank = max(remaining_ranks)
                return (HandEvaluator.HAND_RANKS['Full House'], [three_rank, pair_rank])

        # Check for Flush
        if is_flush:
            high_cards = sorted(ranks, reverse=True)
            return (HandEvaluator.HAND_RANKS['Flush'], high_cards)

        # Check for Straight
        if is_straight:
            return (HandEvaluator.HAND_RANKS['Straight'], [straight_high])

        # Check for Three of a Kind
        if 3 in rank_counts.values():
            three_rank = HandEvaluator.get_rank_by_count(rank_counts, 3)
            kickers = HandEvaluator.get_high_cards(ranks, exclude=[three_rank], count=2)
            return (HandEvaluator.HAND_RANKS['Three of a Kind'], [three_rank] + kickers)

        # Check for Two Pair
        pairs = HandEvaluator.get_ranks_by_count(rank_counts, 2)
        if len(pairs) >= 2:
            top_two_pairs = pairs[:2]
            kicker = HandEvaluator.get_high_cards(ranks, exclude=top_two_pairs, count=1)
            return (HandEvaluator.HAND_RANKS['Two Pair'], top_two_pairs + kicker)

        # Check for One Pair
        if 2 in rank_counts.values():
            pair_rank = HandEvaluator.get_rank_by_count(rank_counts, 2)
            kickers = HandEvaluator.get_high_cards(ranks, exclude=[pair_rank], count=3)
            return (HandEvaluator.HAND_RANKS['One Pair'], [pair_rank] + kickers)

        # High Card
        high_cards = sorted(ranks, reverse=True)[:5]
        return (HandEvaluator.HAND_RANKS['High Card'], high_cards)

    @staticmethod
    def is_flush(suit_counts: Counter) -> bool:
        """
        Determines if the hand is a flush.

        Parameters:
            suit_counts (Counter): Counter object of suits.

        Returns:
            bool: True if flush, else False.
        """
        return any(count >= 5 for count in suit_counts.values())

    @staticmethod
    def is_straight(ranks: List[int]) -> Tuple[bool, Optional[int]]:
        """
        Determines if the hand is a straight.

        Parameters:
            ranks (List[int]): List of integer ranks.

        Returns:
            Tuple[bool, Optional[int]]: (True, high_card) if straight; else (False, None).
        """
        unique_ranks = set(ranks)
        sorted_ranks = sorted(unique_ranks)
        # Handle the special case of Ace acting as 1 in a low straight
        if 14 in unique_ranks:
            sorted_ranks_with_low_ace = [1] + sorted_ranks[:-1]
        else:
            sorted_ranks_with_low_ace = sorted_ranks

        # Check for straight in both scenarios
        for ranks_list in [sorted_ranks, sorted_ranks_with_low_ace]:
            for i in range(len(ranks_list) - 4):
                window = ranks_list[i:i+5]
                if window[4] - window[0] == 4 and len(window) == 5:
                    return True, window[4]
        return False, None

    @staticmethod
    def get_rank_by_count(rank_counts: Counter, count: int) -> int:
        """
        Returns the highest rank that appears a specific number of times.

        Parameters:
            rank_counts (Counter): Counter object of ranks.
            count (int): The count to look for.

        Returns:
            int: Highest rank that appears 'count' times.
        """
        ranks = [rank for rank, cnt in rank_counts.items() if cnt == count]
        return max(ranks) if ranks else None

    @staticmethod
    def get_ranks_by_count(rank_counts: Counter, count: int) -> List[int]:
        """
        Returns all ranks that appear a specific number of times, sorted in descending order.

        Parameters:
            rank_counts (Counter): Counter object of ranks.
            count (int): The count to look for.

        Returns:
            List[int]: Ranks that appear 'count' times, sorted high to low.
        """
        ranks = [rank for rank, cnt in rank_counts.items() if cnt == count]
        return sorted(ranks, reverse=True)

    @staticmethod
    def get_high_cards(ranks: List[int], exclude: List[int] = [], count: int = 1) -> List[int]:
        """
        Returns the highest cards excluding certain ranks.

        Parameters:
            ranks (List[int]): List of integer ranks.
            exclude (List[int], optional): Ranks to exclude. Defaults to [].
            count (int, optional): Number of high cards to return. Defaults to 1.

        Returns:
            List[int]: List of high card ranks.
        """
        high_cards = [rank for rank in ranks if rank not in exclude]
        high_cards = sorted(high_cards, reverse=True)
        return high_cards[:count]
