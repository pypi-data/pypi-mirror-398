from unittest.mock import create_autospec

from pymlga.evaluation import EvaluatedIndividual
from pymlga.individual import Individual


def test_evaluated_individual_sort():
    sorted_individuals = sorted([
        EvaluatedIndividual(fitness=fitness, individual=create_autospec(spec=Individual))
        for fitness in [0.1, -1.0, 1.0, -0.5, 10.0, 0.0, -11.0, 2.5]
    ], reverse=True)
    assert [i.fitness for i in sorted_individuals] == [
        10.0, 2.5, 1.0, 0.1, 0.0, -0.5, -1.0, -11.0
    ]
