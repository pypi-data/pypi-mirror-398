from dataclasses import dataclass
from typing import List, Callable
from unittest.mock import Mock, call, patch

import pytest
from pytesthelpers.exceptionhandling import does_not_raise, raises_assertion_error

from pymlga.allele import RepeatingQueueAlleleFactory
# noinspection PyProtectedMember
from pymlga.chromosome import Chromosome, FixedLengthChromosomeFactory, RandomLengthChromosomeFactory, \
    _get_target_length
from pymlga.gene import Gene, SimpleGeneFactory


def gene_factory():
    return SimpleGeneFactory(
        allele_factory=RepeatingQueueAlleleFactory(alleles=[
            f'spawned{index + 1}'
            for index in range(5)
        ])
    )


@pytest.mark.parametrize(
    argnames=['genes', 'expected_exception'],
    argvalues=[
        (None, raises_assertion_error),
        ([], does_not_raise),
        ([Gene("x"), None, Gene("y")], raises_assertion_error),
        ([Gene("x")], does_not_raise)
    ]
)
def test_chromosome_validate(genes: List[Gene], expected_exception: Callable):
    with expected_exception():
        assert Chromosome(genes=genes).genes == genes


def test_chromosome_iterable():
    genes = [
        Gene(allele='one'),
        Gene(allele='two'),
        Gene(allele='three')
    ]
    result = [gene for gene in Chromosome(genes=genes)]
    assert result == genes


@pytest.mark.parametrize(
    argnames=['length', 'expected_exception'],
    argvalues=[
        (0, raises_assertion_error),
        (1, does_not_raise)
    ]
)
def test_fixed_length_chromosome_factory_constructor(length: int, expected_exception: Callable):
    with expected_exception():
        FixedLengthChromosomeFactory(gene_factory=gene_factory(), length=length)


def test_fixed_length_chromosome_factory_spawn():
    assert FixedLengthChromosomeFactory(gene_factory=gene_factory(), length=5).spawn() == Chromosome(genes=[Gene(allele='spawned1'),
                  Gene(allele='spawned2'),
                  Gene(allele='spawned3'),
                  Gene(allele='spawned4'),
                  Gene(allele='spawned5')
    ])


def test_fixed_length_chromosome_factory_clone():
    mock_genes = [Mock() for _ in range(5)]
    mock_gene_factory = Mock()
    mock_cloned_genes = [Mock() for _ in range(5)]
    mock_gene_factory.clone.side_effect = mock_cloned_genes
    assert FixedLengthChromosomeFactory(gene_factory=mock_gene_factory, length=5).clone(
        Chromosome(genes=mock_genes)
    ) == Chromosome(genes=mock_cloned_genes)
    assert mock_gene_factory.mock_calls == [
        call.clone(mock_gene)
        for mock_gene in mock_genes
    ]


@patch('random.choice', autospec=True)
def test_fixed_length_chromosome_factory_crossover(mock_choice: Mock):
    chromosome1 = Chromosome(genes=[Mock() for _ in range(5)])
    chromosome2 = Chromosome(genes=[Mock() for _ in range(5)])
    chosen = [
        chromosome2.genes[0],
        chromosome1.genes[1],
        chromosome1.genes[2],
        chromosome2.genes[3],
        chromosome1.genes[4]
    ]
    mock_choice.side_effect = chosen
    mock_gene_factory = Mock()
    mock_cloned_genes = [Mock() for _ in range(5)]
    mock_gene_factory.clone.side_effect = mock_cloned_genes
    assert FixedLengthChromosomeFactory(gene_factory=mock_gene_factory, length=5).crossover(
        chromosome1, chromosome2
    ) == Chromosome(genes=mock_cloned_genes)
    assert mock_gene_factory.mock_calls == [
        call.clone(gene)
        for gene in chosen
    ]


@pytest.mark.parametrize(
    argnames=['args', 'expected_exception'],
    argvalues=[
        ({}, does_not_raise),
        ({'shortening_rate': -0.01}, raises_assertion_error),
        ({'shortening_rate': 0}, does_not_raise),
        ({'shortening_rate': 0.5}, does_not_raise),
        ({'shortening_rate': 1}, does_not_raise),
        ({'shortening_rate': 1.01}, raises_assertion_error),
        ({'lengthening_rate': -0.01}, raises_assertion_error),
        ({'lengthening_rate': 0}, does_not_raise),
        ({'lengthening_rate': 0.5}, does_not_raise),
        ({'lengthening_rate': 1}, does_not_raise),
        ({'lengthening_rate': 1.01}, raises_assertion_error),
        ({'throttling_factor': -1}, raises_assertion_error),
        ({'throttling_factor': 0}, raises_assertion_error),
        ({'throttling_factor': 1}, does_not_raise),
        ({'min_length': -1}, raises_assertion_error),
        ({'min_length': 0}, does_not_raise),
        ({'min_length': 1, 'max_length': 1}, raises_assertion_error),
        ({'min_length': 1, 'max_length': 2}, does_not_raise),
        ({'min_length': 1, 'max_length': 10}, does_not_raise),
        ({'min_length': 10, 'max_length': 10}, raises_assertion_error),
        ({'min_length': 11, 'max_length': 10}, raises_assertion_error),
    ]
)
def test_random_length_chromosome_factory_constructor(args: dict, expected_exception: Callable):
    with expected_exception():
        RandomLengthChromosomeFactory(**{
            **{'gene_factory': gene_factory(), 'min_length': 1, 'max_length': 2},
            **args
        })


@patch('random.randint', autospec=True)
def test_random_length_chromosome_factory_spawn(mock_randint: Mock):
    mock_randint.return_value = 7
    mock_gene_factory = Mock()
    mock_spawned_genes = [Mock() for _ in range(7)]
    mock_gene_factory.spawn.side_effect = mock_spawned_genes
    assert RandomLengthChromosomeFactory(
        gene_factory=mock_gene_factory,
        min_length=5,
        max_length=10,
        shortening_rate=0.5,
        lengthening_rate=0.5
    ).spawn() == Chromosome(genes=mock_spawned_genes)
    assert mock_gene_factory.mock_calls == 7 * [call.spawn()]


@dataclass
class RandomLengthCloneParam:
    initial_length: int
    min_length: int
    max_length: int
    target_length: int
    randint_return_values: List[int]
    randint_max_arg_values: List[int]


@pytest.mark.parametrize(
    ids=lambda param: f'{param.initial_length}, {param.min_length}, {param.max_length} => {param.target_length}',
    argnames='param',
    argvalues=[
        RandomLengthCloneParam(
            initial_length=0, min_length=0, max_length=1,
            target_length=0,
            randint_return_values=[],
            randint_max_arg_values=[]
        ),
        RandomLengthCloneParam(
            initial_length=0, min_length=0, max_length=10,
            target_length=2,
            randint_return_values=[1],
            randint_max_arg_values=[1]
        ),
        RandomLengthCloneParam(
            initial_length=2, min_length=0, max_length=10,
            target_length=1,
            randint_return_values=[0],
            randint_max_arg_values=[1]
        ),
        RandomLengthCloneParam(
            initial_length=2, min_length=0, max_length=10,
            target_length=0,
            randint_return_values=[1],
            randint_max_arg_values=[1]
        ),
        RandomLengthCloneParam(
            initial_length=5, min_length=0, max_length=10,
            target_length=10,
            randint_return_values=[1, 1, 2, 2, 3],
            randint_max_arg_values=[5, 6, 7, 8, 9]
        ),
        RandomLengthCloneParam(
            initial_length=5, min_length=0, max_length=10,
            target_length=0,
            randint_return_values=[4, 3, 0, 1],
            randint_max_arg_values=[4, 3, 2, 1]
        ),
    ]
)
@patch('random.randint', autospec=True)
@patch('pymlga.chromosome._get_target_length', autospec=True)
def test_random_length_chromosome_factory_clone(
        mock_get_target_length: Mock,
        mock_randint: Mock,
        param: RandomLengthCloneParam
):
    mock_get_target_length.return_value = param.target_length
    mock_initial_genes = [Mock() for _ in range(param.initial_length)]
    mock_gene_factory = Mock()
    mock_cloned_initial_genes = [Mock() for _ in range(param.initial_length)]
    mock_gene_factory.clone.side_effect = mock_cloned_initial_genes
    mock_randint.side_effect = param.randint_return_values
    mock_expected_genes = [*mock_cloned_initial_genes]
    mock_spawned_genes = []
    assert len(param.randint_max_arg_values) == len(param.randint_return_values)
    if param.target_length > param.initial_length:
        mock_spawned_genes = [Mock() for _ in range(param.target_length - param.initial_length)]
        mock_gene_factory.spawn.side_effect = mock_spawned_genes
        insert_indexes = ([] if param.initial_length > 0 else [0]) + param.randint_return_values
        for mock_spawned_gene, index in zip(mock_spawned_genes, insert_indexes):
            mock_expected_genes.insert(index, mock_spawned_gene)
    elif param.target_length < param.initial_length:
        pop_indexes = param.randint_return_values + ([] if param.target_length > 0 else [0])
        for index in pop_indexes:
            mock_expected_genes.pop(index)

    assert RandomLengthChromosomeFactory(
        gene_factory=mock_gene_factory,
        min_length=param.min_length,
        max_length=param.max_length,
        shortening_rate=1.0,
        lengthening_rate=1.0,
        throttling_factor=3
    ).clone(
        chromosome=Chromosome(genes=mock_initial_genes)
    ) == Chromosome(
        genes=mock_expected_genes
    )
    assert mock_gene_factory.mock_calls == [
        call.clone(mock_gene)
        for mock_gene in mock_initial_genes
    ] + [
        call.spawn()
        for _ in mock_spawned_genes
    ]
    assert mock_randint.mock_calls == [
        call(0, value)
        for value in param.randint_max_arg_values
    ]



@patch('pymlga.chromosome._clone', autospec=True)
@patch('random.choice', autospec=True)
def test_random_length_chromosome_factory_crossover(mock_choice: Mock, mock_clone: Mock):
    mock_chromosomes = [Mock() for _ in range(2)]
    gf = gene_factory()
    result = RandomLengthChromosomeFactory(
        gene_factory=gf,
        min_length=1,
        max_length=2,
        shortening_rate=0.2,
        lengthening_rate=0.1
    ).crossover(*mock_chromosomes)
    assert mock_choice.mock_calls == [call(mock_chromosomes)]
    assert mock_clone.mock_calls == [call(
        chromosome=mock_choice.return_value,
        gene_factory=gf,
        min_length=1,
        max_length=2,
        shortening_rate=0.2,
        lengthening_rate=0.1,
        throttling_factor=3
    )]
    assert result == mock_clone.return_value


@dataclass
class GetTargetLengthParam:
    description: str
    initial_length: int
    min_length: int
    max_length: int
    random_return_values: List[float]
    expected_result: int
    shortening_rate: float = 0.0
    lengthening_rate: float = 0.0
    throttling_factor: int = 3


@pytest.mark.parametrize(
    ids=lambda param: param.description,
    argnames='param',
    argvalues=[
        GetTargetLengthParam(
            '1 length, never grow or shrink',
            initial_length=1, min_length=0, max_length=10,
            random_return_values=[],
            expected_result=1
        ),
        GetTargetLengthParam(
            '3 length, do not grow',
            initial_length=3, min_length=0, max_length=10,
            lengthening_rate=0.2,
            random_return_values=[0.2],
            expected_result=3
        ),
        GetTargetLengthParam(
            '3 length, grow to max length',
            initial_length=3, min_length=0, max_length=10,
            lengthening_rate=0.2,
            random_return_values=[0.19, 0.99999],
            expected_result=10
        ),
        GetTargetLengthParam(
            '3 length, grow by one',
            initial_length=3, min_length=0, max_length=10,
            lengthening_rate=0.2,
            random_return_values=[0.19, 0.3],
            expected_result=4
        ),
        GetTargetLengthParam(
            '3 length, grow by two',
            initial_length=3, min_length=0, max_length=10,
            lengthening_rate=0.2,
            random_return_values=[0.19, 0.2],
            throttling_factor=1,
            expected_result=5
        ),
        GetTargetLengthParam(
            '3 length, do not shrink',
            initial_length=3, min_length=0, max_length=10,
            shortening_rate=0.2,
            random_return_values=[0.2],
            expected_result=3
        ),
        GetTargetLengthParam(
            '3 length, shrink to zero',
            initial_length=3, min_length=0, max_length=10,
            shortening_rate=0.2,
            random_return_values=[0.19, 0.99999999999],
            expected_result=0
        ),
        GetTargetLengthParam(
            '3 length, shrink by one',
            initial_length=3, min_length=0, max_length=10,
            shortening_rate=0.2,
            random_return_values=[0.19, 0.5],
            expected_result=2
        ),
        GetTargetLengthParam(
            '3 length, shrink by two',
            initial_length=3, min_length=0, max_length=10,
            shortening_rate=0.2,
            random_return_values=[0.19, 0.5],
            throttling_factor=1,
            expected_result=1
        ),
        GetTargetLengthParam(
            '5 length, do not grow or shrink',
            initial_length=5, min_length=0, max_length=10,
            shortening_rate=0.3,
            lengthening_rate=0.2,
            random_return_values=[0.3, 0.2],
            expected_result=5
        ),
        GetTargetLengthParam(
            '5 length, grow/shrink cancel out',
            initial_length=5, min_length=0, max_length=10,
            shortening_rate=0.3,
            lengthening_rate=0.2,
            random_return_values=[0.29, 0.5, 0.19, 0.5],
            expected_result=5
        ),
        GetTargetLengthParam(
            '5 length, net shrink 2',
            initial_length=5, min_length=0, max_length=10,
            shortening_rate=0.3,
            lengthening_rate=0.2,
            random_return_values=[0.29, 0.8, 0.19, 0.1],
            expected_result=3
        ),
        GetTargetLengthParam(
            '5 length, net grow 2',
            initial_length=5, min_length=0, max_length=10,
            shortening_rate=0.3,
            lengthening_rate=0.2,
            random_return_values=[0.29, 0.1, 0.19, 0.8],
            expected_result=7
        ),
        GetTargetLengthParam(
            'zero length, cannot shrink',
            initial_length=0, min_length=0, max_length=100,
            shortening_rate=0.3,
            lengthening_rate=0.2,
            random_return_values=[0.2],
            expected_result=0
        ),
        GetTargetLengthParam(
            'zero length, cannot grow',
            initial_length=100, min_length=0, max_length=100,
            shortening_rate=0.3,
            lengthening_rate=0.2,
            random_return_values=[0.3],
            expected_result=100
        ),
    ]
)
@patch('random.random', autospec=True)
def test_get_target_length(
        mock_random: Mock,
        param: GetTargetLengthParam
):
    mock_random.side_effect = param.random_return_values
    assert _get_target_length(
        initial_length=param.initial_length,
        min_length=param.min_length,
        max_length=param.max_length,
        shortening_rate=param.shortening_rate,
        lengthening_rate=param.lengthening_rate,
        throttling_factor=param.throttling_factor
    ) == param.expected_result
    assert mock_random.mock_calls == [call() for _ in param.random_return_values]
