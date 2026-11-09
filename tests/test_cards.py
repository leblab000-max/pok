import unittest
from poker_ai.cards import deck, evaluate_five, evaluate_seven

class HandTests(unittest.TestCase):
    def test_deck(self):
        self.assertEqual(len(set(deck())), 52)

    def test_royal_flush(self):
        self.assertEqual(evaluate_five(['As','Ks','Qs','Js','Ts']), (8, 14))

    def test_wheel(self):
        self.assertEqual(evaluate_five(['As','2d','3c','4h','5s']), (4, 5))

    def test_wheel_straight_flush(self):
        self.assertEqual(evaluate_five(['As','2s','3s','4s','5s']), (8, 5))

    def test_full_house_beats_flush(self):
        self.assertGreater(evaluate_five(['Ac','Ad','Ah','Kc','Kd']), evaluate_five(['2s','5s','8s','Js','Ks']))

    def test_seven_cards_best_hand(self):
        self.assertEqual(evaluate_seven(['As','Ks','Qs','Js','Ts','2c','3d']), (8, 14))

    def test_invalid_cards(self):
        for cards in (['As']*5, ['As','Ks','Qs','Js','1s']):
            with self.assertRaises(ValueError):
                evaluate_five(cards)

if __name__ == '__main__':
    unittest.main()
