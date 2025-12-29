from dataclasses import dataclass
from typing import List

from pygamesim.cardgames.cards import Card, Rank


@dataclass
class HandValue:
    value: int
    is_soft: bool = False
    is_busted: bool = False
    is_blackjack: bool = False


RANK_VALUES = {
    Rank.ACE: 1,
    Rank.TWO: 2,
    Rank.THREE: 3,
    Rank.FOUR: 4,
    Rank.FIVE: 5,
    Rank.SIX: 6,
    Rank.SEVEN: 7,
    Rank.EIGHT: 8,
    Rank.NINE: 9,
    Rank.TEN: 10,
    Rank.JACK: 10,
    Rank.QUEEN: 10,
    Rank.KING: 10,
}


def get_hand_value(cards: List[Card]) -> HandValue:
    value = 0
    ace_count = 0
    for card in cards:
        value += RANK_VALUES[card.rank]
        if card.rank == Rank.ACE:
            ace_count += 1
    is_soft = ace_count > 0 and value <= 11
    if is_soft:
        value = value + 10
    return HandValue(
        value=value,
        is_soft=is_soft,
        is_busted=value > 21,
        is_blackjack=value == 21 and len(cards) == 2
    )
