import random
from .card import Card

class Deck:
    def __init__(self):
        self.cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS.keys()]

    def shuffle(self, count: int = 1):
        for _ in range(count):
            random.shuffle(self.cards)
            
    def cut(self):
        cut_index = random.randint(0, len(self.cards))
        self.cards[:cut_index], self.cards[cut_index:] = self.cards[cut_index:], self.cards[:cut_index]

    def deal(self):
        return self.cards.pop()
