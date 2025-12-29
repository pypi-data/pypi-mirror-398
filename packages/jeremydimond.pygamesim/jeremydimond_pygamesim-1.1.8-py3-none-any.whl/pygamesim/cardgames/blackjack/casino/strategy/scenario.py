from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, eq=True)
class PlayStrategyScenario:
    dealer_up_card_rank_value: int
    player_hand_value: int
    player_hand_is_soft: Optional[bool] = None
