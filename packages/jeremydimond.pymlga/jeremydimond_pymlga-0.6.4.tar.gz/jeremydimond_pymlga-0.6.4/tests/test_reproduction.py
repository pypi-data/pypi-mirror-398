import sys
from typing import Callable, List, Tuple
from unittest.mock import create_autospec, call, Mock, patch

import pytest
from pytesthelpers.exceptionhandling import raises_assertion_error, does_not_raise

from pymlga.individual import Individual, IndividualFactory
import pymlga.reproduction as module_to_test
from pymlga.reproduction import ReproductionRules


@pytest.mark.parametrize(
    argnames=['population_size', 'expected_exception'],
    argvalues=[
        (-1, raises_assertion_error),
        (0, raises_assertion_error),
        (1, does_not_raise),
        (sys.maxsize, does_not_raise)
    ]
)
def test_reproduction_rules_validate_population_size(population_size: int, expected_exception: Callable):
    with expected_exception():
        assert module_to_test.ReproductionRules(population_size=population_size).population_size == population_size


SURVIVAL_RATE_FIELDS = [
    'keep_fittest_survival_rate',
    'clone_fittest_survival_rate',
    'crossover_fittest_survival_rate',
    'crossover_random_survival_rate',
]

@pytest.mark.parametrize(
    argnames=SURVIVAL_RATE_FIELDS + ['expected_exception'],
    argvalues=[
        (0.0, 0.0, 0.0, 0.0, does_not_raise),
        (0.1, 0.2, 0.3, 0.4, does_not_raise),
        (0.11, 0.2, 0.3, 0.4, raises_assertion_error),
        (0.1, 0.21, 0.3, 0.4, raises_assertion_error),
        (0.1, 0.2, 0.31, 0.4, raises_assertion_error),
        (0.1, 0.2, 0.3, 0.41, raises_assertion_error),
    ]
)
def test_reproduction_rules_validate_survival_rate_total(
        keep_fittest_survival_rate: float,
        clone_fittest_survival_rate: float,
        crossover_fittest_survival_rate: float,
        crossover_random_survival_rate: float,
        expected_exception: Callable
):
    with expected_exception():
        module_to_test.ReproductionRules(
            population_size=100,
            keep_fittest_survival_rate=keep_fittest_survival_rate,
            clone_fittest_survival_rate=clone_fittest_survival_rate,
            crossover_fittest_survival_rate=crossover_fittest_survival_rate,
            crossover_random_survival_rate=crossover_random_survival_rate
        )

@pytest.mark.parametrize(
    argnames=['field_value', 'expected_exception'],
    argvalues=[
        (-0.01, raises_assertion_error),
        (0.0, does_not_raise),
        (1, does_not_raise),
        (1.01, raises_assertion_error),
    ]
)
@pytest.mark.parametrize(
    argnames='field_name',
    argvalues=SURVIVAL_RATE_FIELDS
)
def test_reproduction_rules_validate_rates(field_name: str, field_value: float, expected_exception: Callable):
    with expected_exception():
        assert module_to_test.ReproductionRules(
            population_size=100,
            **{
                **{f: 0.0 for f in SURVIVAL_RATE_FIELDS},
                field_name: field_value
            }
        ).__getattribute__(field_name) == field_value


@patch.object(module_to_test, module_to_test._trim_to_size.__name__, autospec=True)
@patch.object(module_to_test, module_to_test._fill_to_size.__name__, autospec=True)
@patch.object(module_to_test, module_to_test._crossover_random.__name__, autospec=True)
@patch.object(module_to_test, module_to_test._crossover_fittest.__name__, autospec=True)
@patch.object(module_to_test, module_to_test._clone_fittest.__name__, autospec=True)
@patch.object(module_to_test, module_to_test._keep_fittest.__name__, autospec=True)
def test_reproduce(
        mock_keep_fittest: Mock,
        mock_clone_fittest: Mock,
        mock_crossover_fittest: Mock,
        mock_crossover_random: Mock,
        mock_fill_to_size: Mock,
        mock_trim_to_size: Mock
):
    mock_individual_factory = create_autospec(spec=IndividualFactory)
    ranked_individuals = [create_autospec(spec=Individual) for _ in range(12)]
    reproduction_rules = ReproductionRules(
        population_size=3,
        keep_fittest_survival_rate=0.1,
        clone_fittest_survival_rate=0.2,
        crossover_fittest_survival_rate=0.3,
        crossover_random_survival_rate=0.4
    )
    mock_keep_fittest.return_value = [create_autospec(spec=Individual) for _ in range(1)]
    mock_clone_fittest.return_value = [create_autospec(spec=Individual) for _ in range(2)]
    mock_crossover_fittest.return_value = [create_autospec(spec=Individual) for _ in range(3)]
    mock_crossover_random.return_value = [create_autospec(spec=Individual) for _ in range(4)]
    mock_trim_to_size.return_value = [create_autospec(spec=Individual) for _ in range(3)]
    assert module_to_test.reproduce(
        ranked_individuals=ranked_individuals,
        reproduction_rules=reproduction_rules,
        individual_factory=mock_individual_factory
    ) == mock_trim_to_size.return_value
    assert mock_keep_fittest.mock_calls == [
        call(
            ranked_individuals=ranked_individuals,
            survival_rate=0.1
        )
    ]
    assert mock_clone_fittest.mock_calls == [
        call(
            ranked_individuals=ranked_individuals,
            survival_rate=0.2,
            individual_factory=mock_individual_factory
        )
    ]
    assert mock_crossover_fittest.mock_calls == [
        call(
            ranked_individuals=ranked_individuals,
            survival_rate=0.3,
            individual_factory=mock_individual_factory
        )
    ]
    assert mock_crossover_random.mock_calls == [
        call(
            ranked_individuals=ranked_individuals,
            survival_rate=0.4,
            individual_factory=mock_individual_factory
        )
    ]
    assert mock_fill_to_size.mock_calls == [
        call(
            population=[
                *mock_keep_fittest.return_value,
                *mock_clone_fittest.return_value,
                *mock_crossover_fittest.return_value,
                *mock_crossover_random.return_value
            ],
            size=3,
            individual_factory=mock_individual_factory
        )
    ]
    assert mock_trim_to_size.mock_calls == [
        call(
            population=[
                *mock_keep_fittest.return_value,
                *mock_clone_fittest.return_value,
                *mock_crossover_fittest.return_value,
                *mock_crossover_random.return_value
            ],
            size=3
        )
    ]


@pytest.mark.parametrize(
    argnames=['population_size', 'survival_rate', 'expected_number_to_keep'],
    argvalues=[
        (1, 0.0, 0),
        (1, 1.0, 1),
        (1, 0.99, 0),
        (10, 0.0, 0),
        (10, 0.5, 5),
        (10, 1.0, 10),
        (9, 0.5, 4),
    ]
)
def test_keep_fittest_population(population_size: int, survival_rate: float, expected_number_to_keep: int):
    ranked_individuals = [create_autospec(spec=Individual) for _ in range(population_size)]
    assert(module_to_test._keep_fittest(
        ranked_individuals=ranked_individuals,
        survival_rate=survival_rate
    )) == ranked_individuals[:expected_number_to_keep]


@pytest.mark.parametrize(
    argnames=['population_size', 'survival_rate', 'expected_number_to_clone'],
    argvalues=[
        (1, 0.0, 0),
        (1, 1.0, 1),
        (1, 0.99, 0),
        (10, 0.0, 0),
        (10, 0.5, 5),
        (10, 1.0, 10),
        (9, 0.5, 4),
    ]
)
def test_clone_fittest(population_size: int, survival_rate: float, expected_number_to_clone: int):
    ranked_individuals = [create_autospec(spec=Individual) for _ in range(population_size)]
    clones = [create_autospec(spec=Individual) for _ in range(expected_number_to_clone)]
    mock_individual_factory = create_autospec(spec=IndividualFactory)
    mock_individual_factory.return_value.clone.side_effect = clones

    assert module_to_test._clone_fittest(
        ranked_individuals=ranked_individuals,
        survival_rate=survival_rate,
        individual_factory=mock_individual_factory.return_value
    ) == clones
    assert mock_individual_factory.return_value.clone.mock_calls == [
        call().clone(individual)
        for individual in ranked_individuals[:expected_number_to_clone]
    ]


@pytest.mark.parametrize(
    argnames=['population_size', 'survival_rate', 'expected_pairings'],
    argvalues=[
        (0, 0.0, []),
        (0, 1.0, []),
        (1, 0.0, []),
        (1, 1.0, []),
        (2, 0.0, []),
        (2, 0.49, []),
        (2, 0.5, [(0, 1)]),
        (2, 0.9, [(0, 1)]),
        (2, 1.0, [(0, 1), (0, 1)]),
        (10, 0.0, []),
        (10, 0.1, [(0, 1)]),
        (10, 0.2, [(0, 1), (0, 2)]),
        (10, 0.3, [(0, 1), (0, 2), (1, 2)]),
        (10, 0.4, [(0, 1), (0, 2), (0, 3), (1, 2)]),
        (10, 0.5, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3)]),
        (10, 0.6, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]),
        (10, 0.7, [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4)]),
        (10, 0.8, [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3)]),
        (10, 0.9, [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4)]),
        (10, 1.0, [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]),
    ]
)
def test_crossover_fittest(population_size: int, survival_rate: float, expected_pairings: List[Tuple[int, int]]):
    ranked_individuals = [create_autospec(spec=Individual) for _ in range(population_size)]
    offspring = [create_autospec(spec=Individual) for _ in range(len(expected_pairings))]
    mock_individual_factory = create_autospec(spec=IndividualFactory)
    mock_individual_factory.return_value.crossover.side_effect = offspring
    assert module_to_test._crossover_fittest(
        ranked_individuals=ranked_individuals,
        survival_rate=survival_rate,
        individual_factory=mock_individual_factory.return_value
    ) == offspring
    assert mock_individual_factory.mock_calls == [
        call().crossover(ranked_individuals[index1], ranked_individuals[index2])
        for index1, index2 in expected_pairings
    ]


@pytest.mark.parametrize(
    argnames=['population_size', 'survival_rate', 'expected_pairings'],
    argvalues=[
        (0, 0.0, []),
        (0, 1.0, []),
        (1, 0.0, []),
        (1, 1.0, []),
        (2, 0.0, []),
        (2, 0.49, []),
        (2, 0.5, [(1, 0)]),
        (2, 1.0, [(1, 0), (0, 1)]),
        (3, 0.66, [(1, 2)]),
        (3, 0.67, [(1, 2), (1, 0)]),
        (10, 0.5, [(1, 2), (1, 0), (3, 4), (9, 1), (5, 4)]),
        (10, 1.0, [(1, 2), (1, 0), (3, 4), (9, 1), (5, 4), (9, 1), (5, 4), (9, 1), (5, 4), (6, 7)]),
    ]
)
@patch('random.sample', autospec=True)
def test_crossover_random(
        mock_sample: Mock,
        population_size: int, survival_rate: float, expected_pairings: List[Tuple[int, int]]
):
    ranked_individuals = [create_autospec(spec=Individual) for _ in range(population_size)]
    offspring = [create_autospec(spec=Individual) for _ in range(len(expected_pairings))]
    mock_individual_factory = create_autospec(spec=IndividualFactory)
    mock_individual_factory.return_value.crossover.side_effect = offspring
    mock_sample.side_effect = [
        (ranked_individuals[index1], ranked_individuals[index2])
        for index1, index2 in expected_pairings
    ]
    assert module_to_test._crossover_random(
        ranked_individuals=ranked_individuals,
        survival_rate=survival_rate,
        individual_factory=mock_individual_factory.return_value
    ) == offspring
    assert mock_individual_factory.mock_calls == [
        call().crossover(ranked_individuals[index1], ranked_individuals[index2])
        for index1, index2 in expected_pairings
    ]



@pytest.mark.parametrize(
    argnames=['starting_size', 'target_size', 'expected_size'],
    argvalues=[
        (0, 10, 0),
        (5, 10, 5),
        (10, 10, 10),
        (11, 10, 10),
    ]
)
def test_trim_to_size(starting_size: int, target_size: int, expected_size: int):
    starting_population = [create_autospec(spec=Individual) for _ in range(starting_size)]
    assert module_to_test._trim_to_size(
        population=starting_population,
        size=target_size
    ) == starting_population[:expected_size]

@pytest.mark.parametrize(
    argnames=['starting_size', 'target_size', 'expected_spawned_individuals'],
    argvalues=[
        (0, 10, 10),
        (8, 10, 2),
        (10, 10, 0),
        (11, 10, 0),
    ]
)
def test_fill_to_size(starting_size: int, target_size: int, expected_spawned_individuals: int):
    starting_population = [create_autospec(spec=Individual) for _ in range(starting_size)]
    population = [individual for individual in starting_population]
    spawned_individuals = [create_autospec(spec=Individual) for _ in range(expected_spawned_individuals)]
    mock_individual_factory = create_autospec(spec=IndividualFactory)
    mock_individual_factory.return_value.spawn.side_effect = spawned_individuals
    module_to_test._fill_to_size(
        population=population,
        size=target_size,
        individual_factory=mock_individual_factory.return_value
    )
    assert len(population) == max(target_size, starting_size)
    assert population == starting_population + spawned_individuals
    assert mock_individual_factory.mock_calls == expected_spawned_individuals * [call().spawn()]
