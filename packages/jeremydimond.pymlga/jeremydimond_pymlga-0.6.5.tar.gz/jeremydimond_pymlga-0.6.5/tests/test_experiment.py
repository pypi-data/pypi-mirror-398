from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Callable, Optional, List
from unittest.mock import Mock, patch, call

import pytest
from pytesthelpers.exceptionhandling import does_not_raise, raises_assertion_error

from pymlga.evaluation import EvaluatedIndividual
from pymlga.experiment import Experiment
import pymlga.experiment as module_to_test
from pymlga.generation import Generation
from pymlga.individual import Individual
from pymlga.reproduction import reproduce


@pytest.mark.parametrize(
    argnames=['args', 'expected_exception'],
    argvalues=[
        ({}, raises_assertion_error),
        ({'max_generations': -1}, raises_assertion_error),
        ({'max_generations': 0}, raises_assertion_error),
        ({'max_generations': 1}, does_not_raise),
        ({'time_limit': timedelta(seconds=1.0)}, does_not_raise),
        ({'target_fitness': -0.1}, does_not_raise),
        ({'target_fitness': -12.345, 'time_limit': timedelta(days=100), 'max_generations': 1000}, does_not_raise),
    ]
)
def test_create_experiment(args: dict, expected_exception: Callable):
    with expected_exception():
        Experiment(
            reproduction_rules=Mock(),
            individual_factory=Mock(),
            fitness_evaluator=Mock(),
            **args
        )


@patch.object(module_to_test, 'datetime', autospec=True)
@patch.object(module_to_test, module_to_test._next_population.__name__, autospec=True)
@patch.object(module_to_test, module_to_test._is_final_generation.__name__, autospec=True)
@patch.object(module_to_test, module_to_test._next_generation.__name__, autospec=True)
@patch.object(module_to_test, module_to_test._initial_population.__name__, autospec=True)
def test_run_experiment(
        mock_initial_population: Mock,
        mock_next_generation: Mock,
        mock_is_final_generation: Mock,
        mock_next_population: Mock,
        mock_datetime: Mock
):
    mock_reproduction_rules = Mock(
        population_size=12345
    )
    mock_individual_factory = Mock()
    mock_fitness_evaluator = Mock()
    mock_generations = 10 * [Mock()]
    mock_populations = 11 * [Mock()]
    mock_initial_individuals = [Mock()]
    mock_initial_population.return_value = mock_populations[0]
    mock_next_generation.side_effect = mock_generations
    mock_is_final_generation.side_effect = (9 * [False]) + [True]
    mock_next_population.side_effect = mock_populations[1:]
    mock_datetime.now.side_effect = [
        datetime(year=2025, month=1, day=31, hour=13, minute=59, second=3*index)
        for index in range(11)
    ]
    assert Experiment(
        reproduction_rules=mock_reproduction_rules,
        individual_factory=mock_individual_factory,
        fitness_evaluator=mock_fitness_evaluator,
        initial_individuals=mock_initial_individuals,
        max_generations=10,
        time_limit=timedelta(seconds=11),
        target_fitness=12.3
    ).run() == mock_generations[-1]
    assert mock_initial_population.mock_calls == [
        call(
            size=12345,
            initial_individuals=mock_initial_individuals,
            individual_factory=mock_individual_factory
        )
    ]
    assert mock_next_generation.mock_calls == [
        call(
            generation_number=generation_index + 1,
            population=mock_populations[generation_index],
            fitness_evaluator=mock_fitness_evaluator
        )
        for generation_index in range(10)
    ]
    assert mock_is_final_generation.mock_calls == [
        call(
            generation=mock_generations[generation_index],
            elapsed_time=timedelta(seconds=3*(generation_index+1)),
            max_generations=10,
            time_limit=timedelta(seconds=11),
            target_fitness=12.3
        )
        for generation_index in range(10)
    ]
    assert mock_next_population.mock_calls == [
        call(
            generation=mock_generations[generation_index],
            reproduction_rules=mock_reproduction_rules,
            individual_factory=mock_individual_factory
        )
        for generation_index in range(9)
    ]



@pytest.mark.parametrize(
    ids=['all spawned', 'some_spawned'],
    argnames=['initial_individuals', 'expected_spawn_calls'],
    argvalues=[
        (None, 3),
        ([Mock(), Mock()], 1),
    ]
)
def test_initial_population(
        initial_individuals: Optional[List[Individual]],
        expected_spawn_calls: int
):
    mock_individual_factory = Mock()
    mock_individuals = [Mock() for _ in range(3)]
    mock_individual_factory.spawn.side_effect = mock_individuals
    assert module_to_test._initial_population(
        size=3,
        initial_individuals=initial_individuals,
        individual_factory=mock_individual_factory
    ) == (initial_individuals or []) + mock_individuals[:expected_spawn_calls]
    assert mock_individual_factory.mock_calls == expected_spawn_calls * [call.spawn()]


def test_next_generation():
    mock_population = [Mock() for _ in range(3)]
    mock_evaluated_individuals = [
        EvaluatedIndividual(individual=Mock(), fitness=10.0),
        EvaluatedIndividual(individual=Mock(), fitness=-123.45),
        EvaluatedIndividual(individual=Mock(), fitness=12.3),
        EvaluatedIndividual(individual=Mock(), fitness=1.23)
    ]
    mock_fitness_evaluator = Mock()
    mock_fitness_evaluator.evaluate.return_value = mock_evaluated_individuals
    assert module_to_test._next_generation(
        generation_number=123,
        population=mock_population,
        fitness_evaluator=mock_fitness_evaluator
    ) == Generation(
        generation_number=123,
        ranked_individuals=[
            mock_evaluated_individuals[2],
            mock_evaluated_individuals[0],
            mock_evaluated_individuals[3],
            mock_evaluated_individuals[1]
        ],
        size=4,
        top_fitness=12.3,
        average_fitness=-24.98,
        bottom_fitness=-123.45,
        sum_fitness=-99.92,
        fittest=mock_evaluated_individuals[2]
    )
    assert mock_fitness_evaluator.mock_calls == [call.evaluate(mock_population)]


@dataclass
class IsFinalGenerationParam:
    description: str
    expected_result: bool
    max_generations: Optional[int] = None
    time_limit: Optional[timedelta] = None
    target_fitness: Optional[float] = None
    generation_number: int = 1
    elapsed_time: timedelta = timedelta(seconds=1)
    top_fitness: float = 0.0


@pytest.mark.parametrize(
    ids=lambda param: param.description,
    argnames='param',
    argvalues=[
        IsFinalGenerationParam(
            description='max generation not reached',
            max_generations=10,
            generation_number=9,
            expected_result=False
        ),
        IsFinalGenerationParam(
            description='max generation reached',
            max_generations=10,
            generation_number=10,
            expected_result=True
        ),
        IsFinalGenerationParam(
            description='time limit not reached',
            time_limit=timedelta(seconds=10),
            elapsed_time=timedelta(seconds=9),
            expected_result=False
        ),
        IsFinalGenerationParam(
            description='time limit reached',
            time_limit=timedelta(seconds=10),
            elapsed_time=timedelta(seconds=10),
            expected_result=True
        ),
        IsFinalGenerationParam(
            description='time limit exceeded',
            time_limit=timedelta(seconds=10),
            elapsed_time=timedelta(seconds=11),
            expected_result=True
        ),
        IsFinalGenerationParam(
            description='target fitness not reached',
            target_fitness=12.3,
            top_fitness=12.2,
            expected_result=False
        ),
        IsFinalGenerationParam(
            description='target fitness reached',
            target_fitness=12.3,
            top_fitness=12.3,
            expected_result=True
        ),
        IsFinalGenerationParam(
            description='target fitness exceeded',
            target_fitness=12.3,
            top_fitness=12.4,
            expected_result=True
        ),
    ]
)
def test_is_final_generation(param: IsFinalGenerationParam):
    assert module_to_test._is_final_generation(
        generation=Mock(
            generation_number=param.generation_number,
            top_fitness=param.top_fitness,
        ),
        elapsed_time=param.elapsed_time,
        max_generations=param.max_generations,
        time_limit=param.time_limit,
        target_fitness=param.target_fitness
    ) == param.expected_result


@patch.object(module_to_test, reproduce.__name__, autospec=True)
def test_next_population(mock_reproduce: Mock):
    expected_result = [Mock() for _ in range(5)]
    mock_reproduce.return_value = expected_result
    mock_individuals = [Mock() for _ in range(3)]
    mock_evaluated_individuals = [
        EvaluatedIndividual(individual=individual, fitness=10-index)
        for index, individual in enumerate(mock_individuals)
    ]
    mock_reproduction_rules = Mock()
    mock_individual_factory = Mock()
    assert module_to_test._next_population(
        generation=Mock(ranked_individuals=mock_evaluated_individuals),
        reproduction_rules=mock_reproduction_rules,
        individual_factory=mock_individual_factory
    ) == expected_result
    assert mock_reproduce.mock_calls == [
        call(
            ranked_individuals=mock_individuals,
            reproduction_rules=mock_reproduction_rules,
            individual_factory=mock_individual_factory
        )
    ]
