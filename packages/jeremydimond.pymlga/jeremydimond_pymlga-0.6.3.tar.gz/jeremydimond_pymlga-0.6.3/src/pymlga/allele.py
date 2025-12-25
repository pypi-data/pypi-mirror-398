import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class AlleleFactory(ABC):
    @abstractmethod
    def spawn(self):  # pragma: no cover
        pass


@dataclass
class RepeatingQueueAlleleFactory(AlleleFactory):
    alleles: list
    _index: int = field(default=-1, init=False)

    def __post_init__(self):
        assert self.alleles

    def spawn(self):
        self._index = (self._index + 1) % len(self.alleles)
        return self.alleles[self._index]


@dataclass
class RandomChoiceAlleleFactory(AlleleFactory):
    alleles: list

    def __post_init__(self):
        assert self.alleles

    def spawn(self):
        return random.choice(self.alleles)
