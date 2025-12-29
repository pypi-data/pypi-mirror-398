from dataclasses import dataclass
from typing import List, Optional

from pygamesim.cardgames.blackjack.casino.dealer import Dealer
from pygamesim.cardgames.blackjack.casino.player import Player
from pygamesim.cardgames.blackjack.casino.watchers import DeckWatcher, CardWatcher
from pygamesim.cardgames.blackjack.hand import get_hand_value, HandValue
from pygamesim.cardgames.cards import Card, Rank
from pygamesim.simulator import Game


@dataclass
class GameRules:
    min_wager: float = 1.0
    max_wager: float = 1.0
    number_of_decks: int = 1
    blackjack_pays: float = 1.5
    is_double_allowed: bool = True
    max_splits_allowed: int = 3
    dealer_hits_soft_17: bool = False
    shoe_cut_penetration: float = 0.8

    def __post_init__(self):
        assert self.min_wager > 0
        assert self.max_wager >= self.min_wager
        assert self.number_of_decks > 0
        assert self.blackjack_pays >= 1
        assert self.max_splits_allowed >= 0
        assert self.shoe_cut_penetration >= 0
        assert self.shoe_cut_penetration <= 1


@dataclass
class PlayerHand:
    cards: List[Card]
    hand_value: HandValue
    wagered_amount: float
    is_doubled: bool = False


@dataclass
class DealerDealResult:
    dealer_cards: List[Card]
    hand_value: HandValue


@dataclass
class PlayerOutcome:
    player: Player
    hands: List[PlayerHand]
    winnings: float


@dataclass
class PlayNextRoundResult:
    dealer_deal_result: DealerDealResult
    player_outcomes: List[PlayerOutcome]


class BlackjackGame(Game):
    rules: GameRules
    players: List[Player]

    def __init__(
            self,
            rules: GameRules,
            players: List[Player],
            deck_watchers: Optional[List[DeckWatcher]] = None,
            card_watchers: Optional[List[CardWatcher]] = None
    ):
        self.rules = rules
        self.players = players
        self.dealer = Dealer(
            number_of_decks=rules.number_of_decks,
            shoe_cut_penetration=rules.shoe_cut_penetration,
            deck_watchers=deck_watchers,
            card_watchers=card_watchers
        )

    def play_next_round(self) -> PlayNextRoundResult:

        self.dealer.prepare_next_hand()

        player_wagers = _collect_wagers(
            players=self.players,
            min_wager=self.rules.min_wager,
            max_wager=self.rules.max_wager
        )

        initial_deal_result = _perform_initial_deal(
            dealer=self.dealer, player_wagers=player_wagers
        )

        final_deal_result = _check_for_dealer_blackjack(
            dealer_up_card=initial_deal_result.dealer_up_card,
            dealer_hole_card=initial_deal_result.dealer_hole_card,
            player_positions=initial_deal_result.player_positions
        ) or _deal_out_the_round(
            dealer=self.dealer,
            dealer_up_card=initial_deal_result.dealer_up_card,
            dealer_hole_card=initial_deal_result.dealer_hole_card,
            player_positions=initial_deal_result.player_positions,
            is_double_allowed=self.rules.is_double_allowed,
            max_splits_allowed=self.rules.max_splits_allowed,
            dealer_hits_soft_17=self.rules.dealer_hits_soft_17
        )

        self.dealer.reveal_card(card=initial_deal_result.dealer_hole_card)

        player_outcomes = [
            _determine_player_outcomes(
                dealer_hand_value=final_deal_result.dealer_deal_result.hand_value,
                player=player_deal_result.player,
                player_hands=player_deal_result.hands,
                blackjack_pays=self.rules.blackjack_pays
            )
            for player_deal_result in final_deal_result.player_deal_results
        ]

        _pay_the_winners(player_outcomes=player_outcomes)

        return PlayNextRoundResult(
            dealer_deal_result=final_deal_result.dealer_deal_result,
            player_outcomes=player_outcomes
        )


@dataclass
class _PlayerWager:
    player: Player
    wagered_amount: float


@dataclass
class _PlayerPosition:
    player: Player
    wagered_amount: float
    cards: List[Card]


@dataclass
class _InitialDealResult:
    dealer_up_card: Card
    dealer_hole_card: Card
    player_positions: List[_PlayerPosition]


@dataclass
class _PlayerDealResult:
    player: Player
    hands: List[PlayerHand]


@dataclass
class _FinalDealResult:
    dealer_deal_result: DealerDealResult
    player_deal_results: List[_PlayerDealResult]


def _collect_wagers(players: List[Player], min_wager: float, max_wager: float) -> List[_PlayerWager]:
    player_wagers = [
        _PlayerWager(
            player=player,
            wagered_amount=player.get_next_wager(min_wager=min_wager, max_wager=max_wager)
        )
        for player in players
    ]
    invalid_wagers = [
        player_wager for player_wager in player_wagers
        if player_wager.wagered_amount < min_wager or player_wager.wagered_amount > max_wager
    ]
    assert len(invalid_wagers) == 0, f'{len(invalid_wagers)} invalid wager amount(s) {invalid_wagers}'
    return player_wagers


def _perform_initial_deal(
        dealer: Dealer, player_wagers: List[_PlayerWager]
) -> _InitialDealResult:
    player_positions = [
        _PlayerPosition(
            player=player_wager.player,
            wagered_amount=player_wager.wagered_amount,
            cards=[dealer.deal_next_card()]
        )
        for player_wager in player_wagers
    ]
    dealer_hole_card = dealer.deal_next_card(face_up=False)
    for player_position in player_positions:
        player_position.cards.append(dealer.deal_next_card())
    dealer_up_card = dealer.deal_next_card()

    return _InitialDealResult(
        dealer_up_card=dealer_up_card,
        dealer_hole_card=dealer_hole_card,
        player_positions=player_positions
    )


def _check_for_dealer_blackjack(
        dealer_up_card: Card,
        dealer_hole_card: Card,
        player_positions: List[_PlayerPosition]
) -> Optional[_FinalDealResult]:
    dealer_hand_value = get_hand_value(cards=[dealer_up_card, dealer_hole_card])
    if not dealer_hand_value.is_blackjack:
        return None
    player_deal_results = []
    for player_position in player_positions:
        player = player_position.player
        wagered_amount = player_position.wagered_amount
        player_cards = player_position.cards
        player_hand_value = get_hand_value(cards=player_cards)
        player_deal_result = _PlayerDealResult(
            player=player,
            hands=[PlayerHand(cards=player_cards, hand_value=player_hand_value, wagered_amount=wagered_amount)]
        )
        player_deal_results.append(player_deal_result)
    return _FinalDealResult(
        dealer_deal_result=DealerDealResult(
            dealer_cards=_reveal_dealer_cards(
                dealer_up_card=dealer_up_card,
                dealer_hole_card=dealer_hole_card
            ),
            hand_value=dealer_hand_value
        ),
        player_deal_results=player_deal_results
    )


def _deal_out_the_round(
        dealer: Dealer, dealer_up_card: Card, dealer_hole_card: Card,
        player_positions: List[_PlayerPosition],
        is_double_allowed: bool, max_splits_allowed: int, dealer_hits_soft_17: bool
) -> _FinalDealResult:
    player_deal_results = [
        _deal_to_player(
            dealer=dealer, player=position.player,
            dealer_up_card=dealer_up_card, initial_player_cards=position.cards,
            wagered_amount=position.wagered_amount,
            is_double_allowed=is_double_allowed,
            max_splits_allowed=max_splits_allowed
        )
        for position in player_positions
    ]
    still_active = [
        result
        for result in player_deal_results
        if any(hand for hand in result.hands if not hand.hand_value.is_busted)
    ]
    dealer_cards = _reveal_dealer_cards(dealer_up_card=dealer_up_card, dealer_hole_card=dealer_hole_card)
    dealer_deal_result = _deal_to_dealer(
        dealer=dealer, initial_dealer_cards=dealer_cards,
        dealer_hits_soft_17=dealer_hits_soft_17
    ) if any(still_active) else DealerDealResult(
        dealer_cards=dealer_cards,
        hand_value=get_hand_value(cards=dealer_cards)
    )
    return _FinalDealResult(
        dealer_deal_result=dealer_deal_result,
        player_deal_results=player_deal_results
    )


def _deal_to_player(
        dealer: Dealer, player: Player,
        dealer_up_card: Card, initial_player_cards: List[Card], wagered_amount: float,
        is_double_allowed: bool, max_splits_allowed: int
) -> _PlayerDealResult:
    hands: List[PlayerHand] = []
    player_hand_cards = [initial_player_cards.copy()]
    split_aces = False
    while len(hands) < len(player_hand_cards):
        player_cards = player_hand_cards[len(hands)]
        hand_is_doubled = False
        while True:
            while len(player_cards) < 2:
                player_cards.append(dealer.deal_next_card())
            hand_value = get_hand_value(cards=player_cards)
            if hand_value.value >= 21:
                break
            if len(player_hand_cards) <= max_splits_allowed and \
                    len(player_cards) == 2 and player_cards[0].rank == player_cards[1].rank:
                if player.offer_split(
                    dealer_up_card=dealer_up_card, player_cards=player_cards, wagered_amount=wagered_amount
                ):
                    player_hand_cards.append([player_cards.pop()])
                    split_aces = player_cards[0].rank == Rank.ACE
                    continue
            if is_double_allowed and len(player_cards) == 2 and not split_aces:
                if player.offer_double(
                    dealer_up_card=dealer_up_card, player_cards=player_cards, wagered_amount=wagered_amount
                ):
                    hand_is_doubled = True
                    player_cards.append(dealer.deal_next_card())
                    break
            if not split_aces:
                if player.offer_hit(dealer_up_card=dealer_up_card, player_cards=player_cards):
                    player_cards.append(dealer.deal_next_card())
                    continue
            break
        hands.append(PlayerHand(
            cards=player_cards,
            hand_value=get_hand_value(player_cards),
            is_doubled=hand_is_doubled,
            wagered_amount=wagered_amount
        ))
    return _PlayerDealResult(player=player, hands=hands)


def _deal_to_dealer(
        dealer: Dealer, initial_dealer_cards: List[Card], dealer_hits_soft_17: bool
) -> DealerDealResult:
    dealer_cards = initial_dealer_cards.copy()
    while True:
        hand_value = get_hand_value(cards=dealer_cards)
        if hand_value.is_soft:
            if hand_value.value == 17 and not dealer_hits_soft_17:
                break
            elif hand_value.value > 17:
                break
        elif hand_value.value >= 17:
            break
        dealer_cards.append(dealer.deal_next_card())
    return DealerDealResult(dealer_cards=dealer_cards, hand_value=hand_value)


def _determine_player_outcomes(
        dealer_hand_value: HandValue,
        player: Player,
        player_hands: List[PlayerHand],
        blackjack_pays: float
) -> PlayerOutcome:
    total_winnings = 0.0
    dealer_has_blackjack = dealer_hand_value.is_blackjack
    player_has_blackjack = len(player_hands) == 1 and player_hands[0].hand_value.is_blackjack
    if dealer_has_blackjack:
        if player_has_blackjack:
            total_winnings += float(player_hands[0].wagered_amount)
    elif player_has_blackjack:
        total_winnings += (1.0 + float(blackjack_pays)) * float(player_hands[0].wagered_amount)
    else:
        for player_hand in player_hands:
            player_hand_value = player_hand.hand_value
            if player_hand_value.is_busted:
                continue
            if not dealer_hand_value.is_busted and dealer_hand_value.value > player_hand_value.value:
                continue
            hand_winnings = float(player_hand.wagered_amount)
            if player_hand.is_doubled:
                hand_winnings = 2.0 * hand_winnings
            if dealer_hand_value.is_busted or player_hand_value.value > dealer_hand_value.value:
                hand_winnings = 2.0 * hand_winnings
            total_winnings += hand_winnings
    return PlayerOutcome(player=player, hands=player_hands, winnings=total_winnings)


def _reveal_dealer_cards(dealer_up_card: Card, dealer_hole_card: Card) -> List[Card]:
    return [dealer_up_card, dealer_hole_card]


def _pay_the_winners(player_outcomes: List[PlayerOutcome]):
    for player_outcome in player_outcomes:
        winnings = player_outcome.winnings
        if winnings > 0:
            player_outcome.player.pay(amount=winnings)
