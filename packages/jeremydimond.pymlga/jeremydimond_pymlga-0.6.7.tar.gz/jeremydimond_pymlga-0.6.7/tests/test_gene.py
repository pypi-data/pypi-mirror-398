from typing import Callable
from unittest.mock import Mock, patch

import pytest
from pytesthelpers.exceptionhandling import raises_assertion_error, does_not_raise

from pymlga.allele import RepeatingQueueAlleleFactory
from pymlga.gene import Gene, SimpleGeneFactory, RandomMutatingGeneFactory

def allele_factory():
    return RepeatingQueueAlleleFactory(alleles=['one', 'two', 'three'])


def test_simple_gene_factory():
    factory = SimpleGeneFactory(allele_factory=allele_factory())
    assert factory.clone(Gene(allele='one')) == Gene(allele='one')
    for _ in range(3):
        assert factory.spawn() == Gene(allele='one')
        assert factory.spawn() == Gene(allele='two')
        assert factory.spawn() == Gene(allele='three')


@pytest.mark.parametrize(
    argnames=['mutation_rate', 'expected_exception'],
    argvalues=[
        (-0.01, raises_assertion_error),
        (0.0, does_not_raise),
        (0.5, does_not_raise),
        (1.0, does_not_raise),
        (1.01, raises_assertion_error)
    ]
)
def test_random_mutating_gene_factory_constructor(mutation_rate: float, expected_exception: Callable):
    with expected_exception():
        RandomMutatingGeneFactory(allele_factory=allele_factory(), mutation_rate=mutation_rate)


def test_random_mutating_gene_factory_never_mutate():
    factory = RandomMutatingGeneFactory(allele_factory=allele_factory(), mutation_rate=0)
    for _ in range(3):
        assert factory.clone(Gene(allele='one')) == Gene(allele='one')


def test_random_mutating_gene_factory_always_mutate():
    factory = RandomMutatingGeneFactory(allele_factory=allele_factory(), mutation_rate=1)
    for _ in range(3):
        assert factory.clone(Gene(allele='xxx')) == Gene(allele='one')
        assert factory.clone(Gene(allele='xxx')) == Gene(allele='two')
        assert factory.clone(Gene(allele='xxx')) == Gene(allele='three')


@patch('random.random', autospec=True)
def test_random_mutating_gene_factory_sometimes_mutate(mock_random: Mock):
    mock_random.side_effect = [0.0, 0.49, 0.5, 0.51, 0.99]
    factory = RandomMutatingGeneFactory(allele_factory=allele_factory(), mutation_rate=0.5)
    assert factory.clone(Gene(allele='xxx')) == Gene(allele='one')
    assert factory.clone(Gene(allele='xxx')) == Gene(allele='two')
    assert factory.clone(Gene(allele='xxx')) == Gene(allele='xxx')
    assert factory.clone(Gene(allele='xxx')) == Gene(allele='xxx')
    assert factory.clone(Gene(allele='xxx')) == Gene(allele='xxx')
