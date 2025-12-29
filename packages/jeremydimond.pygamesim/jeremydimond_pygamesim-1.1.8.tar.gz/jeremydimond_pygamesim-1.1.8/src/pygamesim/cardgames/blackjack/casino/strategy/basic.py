from dataclasses import dataclass, field
from typing import Optional, List, Dict

from pygamesim.cardgames.blackjack.casino.player import WagerStrategy, PlayStrategy
from pygamesim.cardgames.blackjack.casino.strategy.scenario import PlayStrategyScenario
from pygamesim.cardgames.blackjack.hand import get_hand_value
from pygamesim.cardgames.cards import Card


@dataclass
class BasicWagerStrategy(WagerStrategy):
    wager_amount: Optional[float] = None

    def get_next_wager(self, min_wager: float, max_wager: float) -> float:
        if not self.wager_amount:
            return min_wager
        return max(min(self.wager_amount, max_wager), min_wager)


@dataclass
class BasicPlayStrategy(PlayStrategy):
    default_decision: bool = False
    decision_table: Dict[PlayStrategyScenario, bool] = field(default_factory=dict)

    def get_decision(self, dealer_up_card: Card, player_cards: List[Card]) -> bool:
        dealer_hand_value = get_hand_value(cards=[dealer_up_card])
        player_hand_value = get_hand_value(cards=player_cards)
        return self.decision_table.get(
            PlayStrategyScenario(
                dealer_up_card_rank_value=dealer_hand_value.value,
                player_hand_value=player_hand_value.value,
                player_hand_is_soft=player_hand_value.is_soft
            ),
            self.decision_table.get(
                PlayStrategyScenario(
                    dealer_up_card_rank_value=dealer_hand_value.value,
                    player_hand_value=player_hand_value.value
                ),
                self.default_decision
            )
        )
