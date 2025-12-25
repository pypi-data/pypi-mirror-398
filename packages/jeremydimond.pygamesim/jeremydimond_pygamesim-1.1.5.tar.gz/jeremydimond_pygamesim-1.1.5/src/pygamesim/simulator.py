from abc import ABC, abstractmethod
from concurrent.futures.process import ProcessPoolExecutor as PoolExecutor
from dataclasses import dataclass
from typing import List, Optional


class Game(ABC):
    def play_next_round(self):  # pragma: no cover
        pass


class GameSimulator(ABC):
    @abstractmethod
    def simulate(self, games: List[Game], number_of_rounds_per_game: int) -> List[Game]:  # pragma: no cover
        pass


class LocalGameSimulator(GameSimulator):
    max_concurrent_games: Optional[int]

    def __init__(self, max_concurrent_games: Optional[int] = None):
        self.max_concurrent_games = max_concurrent_games
        super().__init__()

    def simulate(self, games: List[Game], number_of_rounds_per_game: int) -> List[Game]:
        print()
        print(f'Starting local game simulator for {len(games)} games...')
        print()

        game_run_args = [
            GameRunArgs(
                game=game,
                game_number=index + 1,
                number_of_rounds=number_of_rounds_per_game
            )
            for index, game in enumerate(games)
        ]
        if self.max_concurrent_games is None:
            results = [_run_game(args) for args in game_run_args]
        else:
            with PoolExecutor(max_workers=self.max_concurrent_games) as executor:
                results = list(executor.map(_run_game, game_run_args))
        print()
        print('Finished local game simulator')
        print()
        # noinspection PyUnboundLocalVariable
        return results


@dataclass
class GameRunArgs:
    game: Game
    game_number: int
    number_of_rounds: int


def _run_game(args: GameRunArgs) -> Game:
    for _ in range(args.number_of_rounds):
        args.game.play_next_round()
    print('.', end='')
    return args.game
