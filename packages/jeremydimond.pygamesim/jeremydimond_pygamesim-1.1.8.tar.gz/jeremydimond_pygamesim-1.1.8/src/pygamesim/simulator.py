from abc import ABC, abstractmethod
from concurrent.futures import Future
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

        game_run_args = [
            GameRunArgs(
                game=game,
                game_number=index + 1,
                number_of_rounds=number_of_rounds_per_game
            )
            for index, game in enumerate(games)
        ]
        if self.max_concurrent_games is None:
            completed = 0
            results = []
            for args in game_run_args:
                results.append(_run_game(args))
                completed = completed + 1
                _show_single_thread_status(completed)
        else:

            with PoolExecutor(max_workers=self.max_concurrent_games) as executor:
                # results = list(executor.map(_run_game, game_run_args))
                futures = [executor.submit(_run_game, args) for args in game_run_args]
                _add_callbacks(futures)
                results = [future.result() for future in futures]
        print()
        print('Finished local game simulator')
        print()
        # noinspection PyUnboundLocalVariable
        return results


def _show_single_thread_status(completed: int):
    print('.', end='', flush=True)
    if completed % 100 == 0:
        print(flush=True)


def _add_callbacks(futures: List[Future], approximate_dots_per_line: int = 100):
    def _show_progress(_):
        print('.', end='', flush=True)

    def _show_progress_newline(_):
        print(flush=True)

    for future in futures:
        future.add_done_callback(_show_progress)
    for future in futures[::approximate_dots_per_line]:
        future.add_done_callback(_show_progress_newline)


@dataclass
class GameRunArgs:
    game: Game
    game_number: int
    number_of_rounds: int


def _run_game(args: GameRunArgs) -> Game:
    for _ in range(args.number_of_rounds):
        args.game.play_next_round()
    return args.game
