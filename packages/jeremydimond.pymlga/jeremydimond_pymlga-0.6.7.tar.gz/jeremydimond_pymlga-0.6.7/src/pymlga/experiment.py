from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Optional, List

from pymlga.evaluation import FitnessEvaluator
from pymlga.generation import Generation
from pymlga.individual import IndividualFactory, Individual
from pymlga.reproduction import ReproductionRules, reproduce


@dataclass
class Experiment:
    reproduction_rules: ReproductionRules
    individual_factory: IndividualFactory
    fitness_evaluator: FitnessEvaluator
    target_fitness: Optional[float]
    initial_individuals: Optional[List[Individual]] = None
    max_generations: Optional[int] = None
    time_limit: Optional[timedelta] = None
    target_fitness: Optional[float] = None

    def __post_init__(self):
        assert not (self.max_generations is None and self.target_fitness is None and self.time_limit is None)
        assert not (self.max_generations is not None and self.max_generations <= 0)

    def run(self) -> Generation:
        start_time = datetime.now()
        population = _initial_population(
            size=self.reproduction_rules.population_size,
            initial_individuals=self.initial_individuals,
            individual_factory=self.individual_factory
        )
        generation_number = 0
        while True:
            generation_number += 1
            generation = _next_generation(
                generation_number=generation_number,
                population=population,
                fitness_evaluator=self.fitness_evaluator
            )
            if _is_final_generation(
                generation=generation,
                elapsed_time=datetime.now() - start_time,
                max_generations=self.max_generations,
                time_limit=self.time_limit,
                target_fitness=self.target_fitness
            ):
                return generation
            population = _next_population(
                generation=generation,
                reproduction_rules=self.reproduction_rules,
                individual_factory=self.individual_factory
            )


def _initial_population(
        size: int,
        initial_individuals: Optional[List[Individual]],
        individual_factory: IndividualFactory
) -> List[Individual]:
    print('Spawning initial population...')
    result = [*(initial_individuals or [])]
    while len(result) < size:
        result.append(individual_factory.spawn())
    return result


def _next_generation(
        generation_number: int,
        population: List[Individual],
        fitness_evaluator: FitnessEvaluator
) -> Generation:
    print(f'Creating next generation...')
    ranked_individuals = sorted(fitness_evaluator.evaluate(population), reverse=True)
    sum_fitness = sum([i.fitness for i in ranked_individuals])
    return Generation(
        generation_number=generation_number,
        ranked_individuals=ranked_individuals,
        size=len(ranked_individuals),
        top_fitness=ranked_individuals[0].fitness,
        average_fitness=(sum_fitness/float(len(ranked_individuals))),
        bottom_fitness=ranked_individuals[-1].fitness,
        sum_fitness=sum_fitness,
        fittest=ranked_individuals[0]
    )


def _is_final_generation(
        generation: Generation,
        elapsed_time: timedelta,
        max_generations: Optional[int],
        time_limit: Optional[timedelta],
        target_fitness: Optional[float]
) -> bool:
    print(f'Generation #{generation.generation_number} '
          f'top fitness={"{:0,.2f}".format(generation.top_fitness)}, '
          f'elapsed time {elapsed_time}.')
    if max_generations is not None and generation.generation_number == max_generations:
        print('Max generations reached!!!')
        return True
    if time_limit is not None and elapsed_time >= time_limit:
        print('Time limit reached!!!')
        return True
    if target_fitness is not None and generation.top_fitness >= target_fitness:
        print('Target fitness reached!!!')
        return True
    print('Generation is not final, experiment continues...')
    return False


def _next_population(
        generation: Generation,
        reproduction_rules: ReproductionRules,
        individual_factory: IndividualFactory
) -> List[Individual]:
    print('Reproducing...')
    return reproduce(
        ranked_individuals=[ei.individual for ei in generation.ranked_individuals],
        reproduction_rules=reproduction_rules,
        individual_factory=individual_factory
    )