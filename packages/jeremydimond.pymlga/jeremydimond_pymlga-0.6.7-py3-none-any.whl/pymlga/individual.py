from dataclasses import dataclass
from typing import List

from pymlga.chromosome import Chromosome, ChromosomeFactory


@dataclass
class Individual:
    chromosomes: List[Chromosome]

    def __post_init__(self):
        assert self.chromosomes
        assert None not in self.chromosomes

    def __iter__(self):
        return iter(self.chromosomes)


@dataclass
class IndividualFactory:

    chromosome_factories: List[ChromosomeFactory]

    def __post_init__(self):
        assert self.chromosome_factories
        assert None not in self.chromosome_factories

    def spawn(self) -> Individual:
        return Individual(chromosomes=[
            factory.spawn()
            for factory in self.chromosome_factories
        ])

    def clone(self, individual: Individual) -> Individual:
        return Individual(chromosomes=[
            factory.clone(chromosome)
            for chromosome, factory in zip(individual.chromosomes, self.chromosome_factories)
        ])

    def crossover(self, individual1: Individual, individual2: Individual) -> Individual:
        return Individual(chromosomes=[
            factory.crossover(chromosome1, chromosome2)
            for chromosome1, chromosome2, factory in zip(individual1.chromosomes, individual2.chromosomes, self.chromosome_factories)
        ])
