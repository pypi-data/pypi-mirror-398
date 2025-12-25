from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pygamesim.cardgames.blackjack.casino.player import WagerStrategy, PlayStrategy
from pygamesim.cardgames.blackjack.casino.strategy.scenario import PlayStrategyScenario
from pygamesim.cardgames.blackjack.casino.watchers import DeckWatcher, CardWatcher
from pygamesim.cardgames.blackjack.hand import get_hand_value
from pygamesim.cardgames.cards import Card, Rank


class CardCounter(DeckWatcher, CardWatcher):

    def __init__(
            self,
            card_rank_count_values: Dict[Rank, int],
            number_of_decks: int = 1,
            use_deck_adjusted_count: bool = True
    ):
        self._card_rank_count_values = card_rank_count_values
        self._number_of_decks = number_of_decks
        self._use_deck_adjusted_count = use_deck_adjusted_count
        self._reset_count()

    def notify_deck_shuffled(self):
        self._reset_count()

    def notify_card_revealed(self, card: Card):
        self._number_of_cards_dealt += 1
        self._raw_count += self._card_rank_count_values.get(card.rank, 0)

    def _reset_count(self):
        self._number_of_cards_dealt = 0
        self._raw_count = 0

    def get_current_count(self):
        if not self._use_deck_adjusted_count:
            return self._raw_count
        decks_remaining = self._number_of_decks - int(self._number_of_cards_dealt / 52)
        return int(self._raw_count / decks_remaining)


@dataclass
class CountingWagerStrategy(WagerStrategy):
    card_counter: CardCounter
    default_wager_amount: float
    min_count_wager_amounts: Dict[int, float]

    def get_next_wager(self, min_wager: float, max_wager: float) -> float:
        desired_wager_amount = _get_desired_wager_amount(
            card_counter=self.card_counter,
            default_wager_amount=self.default_wager_amount,
            min_count_wager_amounts=self.min_count_wager_amounts
        )
        return max(min(desired_wager_amount, max_wager), min_wager)


def _get_desired_wager_amount(
        card_counter: CardCounter,
        default_wager_amount: float,
        min_count_wager_amounts: Dict[int, float]
) -> float:
    current_count = card_counter.get_current_count()
    lesser_or_equal_counts = [count for count in min_count_wager_amounts if count <= current_count]
    if not lesser_or_equal_counts:
        return default_wager_amount
    return min_count_wager_amounts[max(lesser_or_equal_counts)]


@dataclass(frozen=True, eq=True)
class CountBasedDecision:
    default_decision: bool = False
    decision_table: Dict[int, bool] = field(default_factory=dict)


@dataclass
class CountingPlayStrategy(PlayStrategy):
    card_counter: CardCounter
    default_decision: bool = False
    decision_table: Dict[PlayStrategyScenario, CountBasedDecision] = field(default_factory=dict)
    use_deck_adjusted_count: bool = True

    def get_decision(self, dealer_up_card: Card, player_cards: List[Card]) -> bool:
        scenario_match = self._lookup_scenario(dealer_up_card=dealer_up_card, player_cards=player_cards)
        return self._get_decision_for(scenario_match) if scenario_match else self.default_decision

    def _lookup_scenario(self, dealer_up_card: Card, player_cards: List[Card]) -> Optional[CountBasedDecision]:
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
                )
            )
        )

    def _get_decision_for(self, scenario_match: CountBasedDecision) -> bool:
        current_count = self.card_counter.get_current_count()
        lower_counts = [count for count in scenario_match.decision_table if count <= current_count]
        return scenario_match.decision_table[max(lower_counts)] if lower_counts else scenario_match.default_decision
