from abc import ABC, abstractmethod
from typing import List

from pygamesim.cardgames.cards import Card


class WagerStrategy(ABC):
    @abstractmethod
    def get_next_wager(self, min_wager: float, max_wager: float) -> float:  # pragma: no cover
        pass


class PlayStrategy(ABC):
    @abstractmethod
    def get_decision(self, dealer_up_card: Card, player_cards: List[Card]) -> bool:  # pragma: no cover
        pass


class Player:
    def __init__(
            self,
            wager_strategy: WagerStrategy,
            split_strategy: PlayStrategy,
            double_strategy: PlayStrategy,
            hit_strategy: PlayStrategy
    ):
        self.winnings = 0.0
        self.amount_wagered = 0.0
        self.amount_paid = 0.0
        self.wager_strategy = wager_strategy
        self.split_strategy = split_strategy
        self.double_strategy = double_strategy
        self.hit_strategy = hit_strategy

    def pay(self, amount: float):
        assert amount > 0
        self.winnings = round(self.winnings + amount, 2)
        self.amount_paid = round(self.amount_paid + amount, 2)

    def get_next_wager(self, min_wager: float, max_wager: float) -> float:
        wager = round(self.wager_strategy.get_next_wager(min_wager=min_wager, max_wager=max_wager), 2)
        assert wager >= min_wager
        assert wager <= max_wager
        self.winnings = round(self.winnings - wager, 2)
        self.amount_wagered = round(self.amount_wagered + wager, 2)
        return wager

    def offer_split(self, dealer_up_card: Card, player_cards: List[Card],  wagered_amount: float) -> bool:
        if self.split_strategy.get_decision(dealer_up_card=dealer_up_card, player_cards=player_cards):
            self.winnings -= wagered_amount
            return True
        return False

    def offer_double(self, dealer_up_card: Card, player_cards: List[Card],  wagered_amount: float) -> bool:
        if self.double_strategy.get_decision(dealer_up_card=dealer_up_card, player_cards=player_cards):
            self.winnings -= wagered_amount
            return True
        return False

    def offer_hit(self, dealer_up_card: Card, player_cards: List[Card]) -> bool:
        return self.hit_strategy.get_decision(dealer_up_card=dealer_up_card, player_cards=player_cards)
