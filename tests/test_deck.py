import unittest
from app.deck import Deck

class TestDeck(unittest.TestCase):
    def test_deck_has_52_cards(self):
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)

if __name__ == '__main__':
    unittest.main()
