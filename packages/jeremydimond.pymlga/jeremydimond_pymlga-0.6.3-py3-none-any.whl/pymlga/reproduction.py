import random
from dataclasses import dataclass
from typing import List

from pymlga.individual import Individual, IndividualFactory


@dataclass
class ReproductionRules:
    population_size: int
    keep_fittest_survival_rate: float = 0.1
    clone_fittest_survival_rate: float = 0.1
    crossover_fittest_survival_rate: float = 0.6
    crossover_random_survival_rate: float = 0.05

    def __post_init__(self):
        assert self.population_size > 0, "population_size must be > 0"
        survival_rate_total = 0.0
        # noinspection PyUnresolvedReferences
        for field in self.__dataclass_fields__:
            if field.endswith('_rate'):
                field_value = self.__getattribute__(field)
                assert field_value >= 0
                assert field_value <= 1
                survival_rate_total += field_value
        assert survival_rate_total <= 1.0, "survival rates must not exceed 1.0"


def reproduce(
        ranked_individuals: List[Individual],
        reproduction_rules: ReproductionRules,
        individual_factory: IndividualFactory
) -> List[Individual]:
    new_population = _keep_fittest(
        ranked_individuals=ranked_individuals,
        survival_rate=reproduction_rules.keep_fittest_survival_rate
    ) + _clone_fittest(
        ranked_individuals=ranked_individuals,
        survival_rate=reproduction_rules.clone_fittest_survival_rate,
        individual_factory=individual_factory
    ) + _crossover_fittest(
        ranked_individuals=ranked_individuals,
        survival_rate=reproduction_rules.crossover_fittest_survival_rate,
        individual_factory=individual_factory
    ) + _crossover_random(
        ranked_individuals=ranked_individuals,
        survival_rate=reproduction_rules.crossover_random_survival_rate,
        individual_factory=individual_factory
    )
    _fill_to_size(
        population=new_population,
        size=reproduction_rules.population_size,
        individual_factory=individual_factory
    )
    return _trim_to_size(
        population=new_population,
        size=reproduction_rules.population_size
    )


def _keep_fittest(ranked_individuals: List[Individual], survival_rate: float) -> List[Individual]:
    return ranked_individuals[:int(survival_rate * len(ranked_individuals))]


def _clone_fittest(
        ranked_individuals: List[Individual],
        survival_rate: float,
        individual_factory: IndividualFactory
) -> List[Individual]:
    individuals_to_clone = ranked_individuals[:int(survival_rate * len(ranked_individuals))]
    return [
        individual_factory.clone(individual)
        for individual in individuals_to_clone
    ]


def _crossover_fittest(
        ranked_individuals: List[Individual],
        survival_rate: float,
        individual_factory: IndividualFactory
) -> List[Individual]:
    if len(ranked_individuals) < 2:
        return []
    target_offspring_count = int(survival_rate * len(ranked_individuals))
    if target_offspring_count == 0:
        return []
    mating_individuals = [ranked_individuals[0]]
    index = 1
    while index < len(ranked_individuals) and ((len(mating_individuals) * (len(mating_individuals) - 1)) / 2) < target_offspring_count:
        mating_individuals.append(ranked_individuals[index])
        index += 1
    offspring = []
    while len(offspring) < target_offspring_count:
        for index, individual1 in enumerate(mating_individuals):
            if len(offspring) == target_offspring_count:
                break
            for individual2 in mating_individuals[index + 1:]:
                offspring.append(individual_factory.crossover(individual1, individual2))
                if len(offspring) == target_offspring_count:
                    break
    return offspring


def _crossover_random(
        ranked_individuals: List[Individual],
        survival_rate: float,
        individual_factory: IndividualFactory
) -> List[Individual]:
    if len(ranked_individuals) < 2:
        return []
    target_offspring_count = int(survival_rate * len(ranked_individuals))
    if target_offspring_count == 0:
        return []
    return [
        individual_factory.crossover(*random.sample(ranked_individuals, 2))
        for _ in range(target_offspring_count)
    ]

def _trim_to_size(population: List[Individual], size: int) -> List[Individual]:
    return population[:size]

def _fill_to_size(population: List[Individual], size: int, individual_factory: IndividualFactory):
    while len(population) < size:
        population.append(individual_factory.spawn())
