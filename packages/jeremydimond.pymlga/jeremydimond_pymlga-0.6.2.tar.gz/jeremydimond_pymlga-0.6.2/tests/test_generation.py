from pymlga.generation import Generation


def test_str():
    ranked_individuals = [f'individual {i}' for i in range(3)]
    # noinspection PyTypeChecker
    assert str(Generation(
        generation_number=1234567890,
        ranked_individuals=ranked_individuals,
        size=3,
        top_fitness=1234.234,
        average_fitness=1.1,
        bottom_fitness=0.3456789,
        sum_fitness=1235.67967889,
        fittest=ranked_individuals[0]
    )) == '''
==========================
Generation # 1,234,567,890
==========================
size: 3
top_fitness: 1,234.234
average_fitness: 1.1
bottom_fitness: 0.3456789
sum_fitness: 1,235.67967889
fittest: individual 0
'''
