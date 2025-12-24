from dataclasses import dataclass
from typing import Dict

from pygamesim.cardgames.blackjack.casino.player import Player
from pygamesim.cardgames.blackjack.casino.strategy.basic import BasicWagerStrategy, BasicPlayStrategy
from pygamesim.cardgames.blackjack.casino.strategy.scenario import PlayStrategyScenario
from pymlga.chromosome import Chromosome
from pymlga.gene import Gene
from pymlga.individual import Individual


@dataclass
class BasicStrategy(Player):
    split_default_decision: bool
    split_decision_table: Dict[PlayStrategyScenario, bool]
    double_default_decision: bool
    double_decision_table: Dict[PlayStrategyScenario, bool]
    hit_default_decision: bool
    hit_decision_table: Dict[PlayStrategyScenario, bool]

    def __init__(
            self,
            split_default_decision: bool,
            split_decision_table: Dict[PlayStrategyScenario, bool],
            double_default_decision: bool,
            double_decision_table: Dict[PlayStrategyScenario, bool],
            hit_default_decision: bool,
            hit_decision_table: Dict[PlayStrategyScenario, bool]
    ):
        self.split_default_decision = split_default_decision
        self.split_decision_table = split_decision_table
        self.double_default_decision = double_default_decision
        self.double_decision_table = double_decision_table
        self.hit_default_decision = hit_default_decision
        self.hit_decision_table = hit_decision_table
        super().__init__(
            wager_strategy=BasicWagerStrategy(),
            split_strategy=BasicPlayStrategy(
                default_decision=split_default_decision,
                decision_table=split_decision_table
            ),
            double_strategy=BasicPlayStrategy(
                default_decision=double_default_decision,
                decision_table=double_decision_table
            ),
            hit_strategy=BasicPlayStrategy(
                default_decision=hit_default_decision,
                decision_table=hit_decision_table
            )
        )

    def to_individual(self) -> Individual:

        return Individual(
            chromosomes=[
                Chromosome(genes=[Gene(self.split_default_decision)]),
                Chromosome(genes=[Gene(item) for item in self.split_decision_table.items()]),
                Chromosome(genes=[Gene(self.double_default_decision)]),
                Chromosome(genes=[Gene(item) for item in self.double_decision_table.items()]),
                Chromosome(genes=[Gene(self.hit_default_decision)]),
                Chromosome(genes=[Gene(item) for item in self.hit_decision_table.items()]),
            ]
        )

    def __str__(self):
        return "todo print strategy table"


def basic_strategy_from(individual: Individual) -> BasicStrategy:
    chromosomes = iter(individual.chromosomes)

    def _boolean_from(chromosome: Chromosome) -> bool:
        return next(iter(chromosome)).allele

    def _decision_table_from(chromosome: Chromosome) -> Dict[PlayStrategyScenario, bool]:

        return {
            gene.allele[0]: gene.allele[1]
            for gene in chromosome
        }

    return BasicStrategy(
        split_default_decision=_boolean_from(next(iter(chromosomes))),
        split_decision_table=_decision_table_from(next(iter(chromosomes))),
        double_default_decision=_boolean_from(next(iter(chromosomes))),
        double_decision_table=_decision_table_from(next(iter(chromosomes))),
        hit_default_decision=_boolean_from(next(iter(chromosomes))),
        hit_decision_table=_decision_table_from(next(iter(chromosomes)))
    )
