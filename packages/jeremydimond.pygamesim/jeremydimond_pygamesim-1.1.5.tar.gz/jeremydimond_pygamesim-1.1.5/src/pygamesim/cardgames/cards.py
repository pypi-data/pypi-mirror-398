from dataclasses import dataclass
from enum import Enum
from typing import List


class Rank(Enum):
    ACE = 'A'
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'
    SIX = '6'
    SEVEN = '7'
    EIGHT = '8'
    NINE = '9'
    TEN = 'X'
    JACK = 'J'
    QUEEN = 'Q'
    KING = 'K'


class Suit(Enum):
    SPADES = '♠'
    CLUBS = '♣'
    DIAMONDS = '♦'
    HEARTS = '♥'


@dataclass
class Card:
    rank: Rank
    suit: Suit


def create_deck(ranks: List[Rank] = None, suits: List[Suit] = None, number_of_decks: int = 1) -> List[Card]:
    ranks_to_include = list(Rank) if ranks is None else ranks
    suits_to_include = list(Suit) if suits is None else suits
    assert len(ranks_to_include) and len(ranks_to_include) == len(set(ranks_to_include))
    assert len(suits_to_include) and len(suits_to_include) == len(set(suits_to_include))
    assert number_of_decks > 0
    return [
        Card(rank=rank, suit=suit) for rank in ranks_to_include
        for suit in suits_to_include
        for _ in range(number_of_decks)
    ]
