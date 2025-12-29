from abc import ABC, abstractmethod

from pygamesim.cardgames.cards import Card


class DeckWatcher(ABC):
    @abstractmethod
    def notify_deck_shuffled(self):  # pragma: no cover
        pass


class CardWatcher(ABC):
    @abstractmethod
    def notify_card_revealed(self, card: Card):  # pragma: no cover
        pass
