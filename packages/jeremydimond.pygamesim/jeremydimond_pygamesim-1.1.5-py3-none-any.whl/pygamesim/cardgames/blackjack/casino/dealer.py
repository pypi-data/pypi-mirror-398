import random
from typing import List, Optional

from pygamesim.cardgames.blackjack.casino.watchers import DeckWatcher, CardWatcher
from pygamesim.cardgames.cards import create_deck, Card


class Dealer:
    def __init__(
            self,
            number_of_decks: int = 1,
            shoe_cut_penetration: float = 1.0,
            deck_watchers: Optional[List[DeckWatcher]] = None,
            card_watchers: Optional[List[CardWatcher]] = None
    ):
        assert number_of_decks > 0
        self._shoe_cut_penetration = shoe_cut_penetration
        self._shoe = create_deck(number_of_decks=number_of_decks)
        self._deck_watchers = deck_watchers if deck_watchers else []
        self._card_watchers = card_watchers if card_watchers else []
        self._shuffle()

    def _shuffle(self):
        random.shuffle(self._shoe)
        self._next_card_index = 0
        self._shuffle_trigger_index = self._shoe_cut_penetration * float(len(self._shoe))
        for deck_watcher in self._deck_watchers:
            deck_watcher.notify_deck_shuffled()

    def prepare_next_hand(self):
        if self._next_card_index > self._shuffle_trigger_index:
            self._shuffle()

    def deal_next_card(self, face_up: bool = True):
        if int(self._next_card_index) >= int(len(self._shoe)):
            self._shuffle()
        next_card = self._shoe[self._next_card_index]
        self._next_card_index += 1
        if face_up:
            for card_watcher in self._card_watchers:
                card_watcher.notify_card_revealed(card=next_card)
        return next_card

    def reveal_card(self, card: Card):
        for card_watcher in self._card_watchers:
            card_watcher.notify_card_revealed(card=card)
