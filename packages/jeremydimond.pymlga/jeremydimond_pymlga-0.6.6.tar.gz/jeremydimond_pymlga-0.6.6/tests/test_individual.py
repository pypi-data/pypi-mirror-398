from typing import List, Callable
from unittest.mock import Mock, call

import pytest
from pytesthelpers.exceptionhandling import raises_assertion_error, does_not_raise

from pymlga.chromosome import Chromosome, ChromosomeFactory
from pymlga.gene import Gene
from pymlga.individual import Individual, IndividualFactory


def test_iterable():
    individual = Individual(chromosomes=[
        Chromosome(genes=[Gene('one')]),
        Chromosome(genes=[Gene('one'), Gene('two')]),
        Chromosome(genes=[Gene('two'), Gene('three')])
    ])
    assert [c for c in individual] == individual.chromosomes


@pytest.mark.parametrize(
    argnames=['chromosomes', 'expected_exception'],
    argvalues=[
        (None, raises_assertion_error),
        ([], raises_assertion_error),
        ([Chromosome([Gene("x")]), None, Chromosome([Gene("y")])], raises_assertion_error),
        ([Chromosome([Gene("x")])], does_not_raise)
    ]
)
def test_individual_validate(chromosomes: List[Chromosome], expected_exception: Callable):
    with expected_exception():
        assert Individual(chromosomes=chromosomes).chromosomes == chromosomes


@pytest.mark.parametrize(
    ids=lambda param: str(param),
    argnames=['chromosome_factories', 'expected_exception'],
    argvalues=[
        ([Mock()], does_not_raise),
        ([Mock(), Mock()], does_not_raise),
        ([], raises_assertion_error),
        ([Mock(), None], raises_assertion_error)
    ]
)
def test_factory_creation_validation(chromosome_factories: List[ChromosomeFactory], expected_exception: Callable):
    with expected_exception():
        IndividualFactory(chromosome_factories=chromosome_factories)


def test_spawn():
    mock_chromosome_factories = [Mock() for _ in range(3)]
    assert IndividualFactory(mock_chromosome_factories).spawn() == Individual([
        factory.spawn.return_value
        for factory in mock_chromosome_factories
    ])
    for factory in mock_chromosome_factories:
        assert factory.mock_calls == [call.spawn()]


def test_clone():
    mock_chromosome_factories = [Mock() for _ in range(3)]
    mock_chromosomes = [Mock() for _ in range(3)]
    individual = Individual(mock_chromosomes)

    assert IndividualFactory(mock_chromosome_factories).clone(individual) == Individual([
        factory.clone.return_value
        for factory in mock_chromosome_factories
    ])
    for factory, chromosome in zip(mock_chromosome_factories, mock_chromosomes):
        assert factory.mock_calls == [call.clone(chromosome)]


def test_crossover():
    mock_chromosome_factories = [Mock() for _ in range(3)]
    mock_chromosomes1 = [Mock() for _ in range(3)]
    mock_chromosomes2 = [Mock() for _ in range(3)]
    individual1 = Individual(mock_chromosomes1)
    individual2 = Individual(mock_chromosomes2)

    assert IndividualFactory(mock_chromosome_factories).crossover(individual1, individual2) == Individual([
        factory.crossover.return_value
        for factory in mock_chromosome_factories
    ])
    for factory, chromosome1, chromosome2 in zip(mock_chromosome_factories, mock_chromosomes1, mock_chromosomes2):
        assert factory.mock_calls == [call.crossover(chromosome1, chromosome2)]
