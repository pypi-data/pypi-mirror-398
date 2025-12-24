import random
from dataclasses import dataclass
from typing import List

from pygamesim.cardgames.blackjack.casino.strategy.scenario import PlayStrategyScenario
from pymlga.allele import RepeatingQueueAlleleFactory, AlleleFactory
from pymlga.chromosome import FixedLengthChromosomeFactory, RandomLengthChromosomeFactory
from pymlga.gene import RandomMutatingGeneFactory
from pymlga.individual import IndividualFactory


@dataclass
class BasicStrategyIndividualFactory(IndividualFactory):

    def __init__(
            self,
            mutation_rate: float,
            chromosome_shortening_rate: float = 0.2,
            chromosome_lengthening_rate: float = 0.3,
            player_hand_is_soft_inclusion_rate: float = 0.05,
            max_split_decision_table_size: int = 30,
            max_double_decision_table_size: int = 100,
            max_hit_decision_table_size: int = 100
    ):
        super().__init__(chromosome_factories=[
            DefaultDecisionChromosomeFactory(mutation_rate=mutation_rate),
            PlayDecisionTableChromosomeFactory(
                mutation_rate=mutation_rate,
                min_length=0,
                max_length=max_split_decision_table_size,
                shortening_rate=chromosome_shortening_rate,
                lengthening_rate=chromosome_lengthening_rate,
                dealer_up_card_rank_values=list(range(1, 10 + 1)),
                player_hand_values=[2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                player_hand_is_soft_inclusion_rate=player_hand_is_soft_inclusion_rate
            ),
            DefaultDecisionChromosomeFactory(mutation_rate=mutation_rate),
            PlayDecisionTableChromosomeFactory(
                mutation_rate=mutation_rate,
                min_length=0,
                max_length=max_double_decision_table_size,
                shortening_rate=chromosome_shortening_rate,
                lengthening_rate=chromosome_lengthening_rate,
                dealer_up_card_rank_values=list(range(1, 11)),
                player_hand_values=list(range(2, 20 + 1)),
                player_hand_is_soft_inclusion_rate=player_hand_is_soft_inclusion_rate
            ),
            DefaultDecisionChromosomeFactory(mutation_rate=mutation_rate),
            PlayDecisionTableChromosomeFactory(
                mutation_rate=mutation_rate,
                min_length=0,
                max_length=max_hit_decision_table_size,
                shortening_rate=chromosome_shortening_rate,
                lengthening_rate=chromosome_lengthening_rate,
                dealer_up_card_rank_values=list(range(1, 11)),
                player_hand_values=list(range(2, 20 + 1)),
                player_hand_is_soft_inclusion_rate=player_hand_is_soft_inclusion_rate
            )
        ])


@dataclass
class DefaultDecisionChromosomeFactory(FixedLengthChromosomeFactory):
    def __init__(self, mutation_rate: float):
        super().__init__(gene_factory=RandomMutatingGeneFactory(
            allele_factory=RepeatingQueueAlleleFactory(alleles=[True, False]),
            mutation_rate=mutation_rate
        ))


@dataclass
class PlayDecisionTableChromosomeFactory(RandomLengthChromosomeFactory):

    def __init__(
            self,
            mutation_rate: float,
            min_length: int,
            max_length: int,
            shortening_rate: float,
            lengthening_rate: float,
            dealer_up_card_rank_values: List[int],
            player_hand_values: List[int],
            player_hand_is_soft_inclusion_rate: float
    ):
        super().__init__(
            gene_factory=PlayDecisionTableGeneFactory(
                mutation_rate=mutation_rate,
                dealer_up_card_rank_values=dealer_up_card_rank_values,
                player_hand_values=player_hand_values,
                player_hand_is_soft_inclusion_rate=player_hand_is_soft_inclusion_rate
            ),
            min_length=min_length,
            max_length=max_length,
            shortening_rate=shortening_rate,
            lengthening_rate=lengthening_rate
        )


@dataclass
class PlayDecisionTableGeneFactory(RandomMutatingGeneFactory):
    def __init__(
            self,
            mutation_rate: float,
            dealer_up_card_rank_values: List[int],
            player_hand_values: List[int],
            player_hand_is_soft_inclusion_rate: float
    ):
        super().__init__(
            allele_factory=PlayDecisionTableAlleleFactory(
                dealer_up_card_rank_values=dealer_up_card_rank_values,
                player_hand_values=player_hand_values,
                player_hand_is_soft_inclusion_rate=player_hand_is_soft_inclusion_rate
            ),
            mutation_rate=mutation_rate
        )

@dataclass
class PlayDecisionTableAlleleFactory(AlleleFactory):
    dealer_up_card_rank_values: List[int]
    player_hand_values: List[int]
    player_hand_is_soft_inclusion_rate: float = 0.0

    def spawn(self):
        return (
            PlayStrategyScenario(
                dealer_up_card_rank_value=random.choice(self.dealer_up_card_rank_values),
                player_hand_value=random.choice(self.player_hand_values),
                player_hand_is_soft=None if (
                        self.player_hand_is_soft_inclusion_rate == 0 or
                        random.random() >= self.player_hand_is_soft_inclusion_rate
                ) else random.choice([True, False])
            ),
            random.choice([True, False])
        )
