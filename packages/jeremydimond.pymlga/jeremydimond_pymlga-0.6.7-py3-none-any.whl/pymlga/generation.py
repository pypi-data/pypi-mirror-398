from dataclasses import dataclass
from typing import List

from pymlga.evaluation import EvaluatedIndividual


@dataclass
class Generation:
    generation_number: int
    ranked_individuals: List[EvaluatedIndividual]
    size: int
    top_fitness: float
    average_fitness: float
    bottom_fitness: float
    sum_fitness: float
    fittest: EvaluatedIndividual

    def __str__(self):
        header_text = f'Generation # {self.generation_number:,}'
        header_separator = ''.join(['=' for _ in range(len(header_text))])
        return f'''
{header_separator}
{header_text}
{header_separator}
size: {self.size}
top_fitness: {self.top_fitness:,}
average_fitness: {self.average_fitness:,}
bottom_fitness: {self.bottom_fitness:,}
sum_fitness: {self.sum_fitness:,}
fittest: {self.fittest}
'''


