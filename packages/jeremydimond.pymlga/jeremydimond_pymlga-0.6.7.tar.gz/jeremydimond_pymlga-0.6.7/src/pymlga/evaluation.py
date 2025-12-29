from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import List

from pymlga.individual import Individual


@dataclass
class EvaluatedIndividual:

    individual: Individual
    fitness: float

    def __lt__(self, other: 'EvaluatedIndividual'):
        return self.fitness < other.fitness

class FitnessEvaluator(ABC):
    @abstractmethod
    def evaluate(self, population: List[Individual]) -> List[EvaluatedIndividual]:  # pragma: no cover
        pass
