import random
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Any

from pymlga.allele import AlleleFactory


@dataclass
class Gene:
    allele: Any


@dataclass
class GeneFactory(ABC):

    allele_factory: AlleleFactory

    def spawn(self) -> Gene:
        return Gene(allele=self.allele_factory.spawn())

    @abstractmethod
    def clone(self, gene: Gene) -> Gene:  # pragma: no cover
        pass


@dataclass
class SimpleGeneFactory(GeneFactory):

    def __init__(self, allele_factory: AlleleFactory):
        super().__init__(allele_factory=allele_factory)

    def clone(self, gene: Gene) -> Gene:
        return Gene(allele=gene.allele)


@dataclass
class RandomMutatingGeneFactory(GeneFactory):

    mutation_rate: float = 0.0

    def __post_init__(self):
        assert self.mutation_rate >= 0
        assert self.mutation_rate <= 1

    def clone(self, gene: Gene) -> Gene:
        if random.random() < self.mutation_rate:
            return self.spawn()
        return Gene(allele=gene.allele)
