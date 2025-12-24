from dataclasses import dataclass
from typing import List

from pygamesim.cardgames.blackjack.casino.game import GameRules, BlackjackGame
from pygamesim.simulator import GameSimulator
from pymlga.evaluation import FitnessEvaluator, EvaluatedIndividual
from pymlga.individual import Individual

from pymlgabj.strategy import basic_strategy_from, BasicStrategy


@dataclass
class BasicStrategyFitnessEvaluator(FitnessEvaluator):
    simulator: GameSimulator
    rules: GameRules
    number_of_rounds: int
    players_per_game: int = 1
    table_size_penalty_factor: float = 0.0

    def evaluate(self, population: List[Individual]) -> List[EvaluatedIndividual]:
        players = [basic_strategy_from(individual) for individual in population]
        results = _run_simulation(
            simulator=self.simulator,
            rules=self.rules,
            players=players,
            players_per_game=self.players_per_game,
            number_of_rounds=self.number_of_rounds
        )
        return [
            EvaluatedIndividual(
                individual=player.to_individual(),
                fitness=_calculate_basic_strategy_fitness(
                    player=player,
                    table_size_penalty_factor=self.table_size_penalty_factor
                )
            )
            for player in results
        ]


def _run_simulation(
        simulator: GameSimulator,
        rules: GameRules,
        players: List[BasicStrategy],
        players_per_game: int,
        number_of_rounds: int
) -> List[BasicStrategy]:
    # noinspection PyTypeChecker
    games: List[BlackjackGame] = simulator.simulate(
        games=[
            BlackjackGame(rules=rules, players=player_group)
            for player_group in [
                players[i:i + players_per_game]
                for i in range(0, len(players), players_per_game)
            ]
        ],
        number_of_rounds_per_game=number_of_rounds
    )
    return [
        player
        for game in games for player in game.players
    ]


def _calculate_basic_strategy_fitness(player: BasicStrategy, table_size_penalty_factor: float) -> float:
    total_table_size = sum([
        len(table) for table in [
            player.split_decision_table,
            player.double_decision_table,
            player.hit_decision_table
        ]
    ])
    table_size_penalty = table_size_penalty_factor * total_table_size
    return player.winnings - table_size_penalty
