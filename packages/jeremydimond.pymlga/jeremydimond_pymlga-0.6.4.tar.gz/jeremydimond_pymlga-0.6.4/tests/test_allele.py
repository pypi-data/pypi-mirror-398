from typing import Callable
from unittest.mock import Mock, call, patch

import pytest
from pytesthelpers.exceptionhandling import raises_assertion_error, does_not_raise

from pymlga.allele import RepeatingQueueAlleleFactory, RandomChoiceAlleleFactory


@pytest.mark.parametrize(
    argnames=['alleles', 'expected_exception'],
    argvalues=[
        (None, raises_assertion_error),
        ([], raises_assertion_error),
        (['x'], does_not_raise),
    ]
)
def test_constructor(alleles: list, expected_exception: Callable):
    with expected_exception():
        RepeatingQueueAlleleFactory(alleles=alleles)
        RandomChoiceAlleleFactory(alleles=alleles)


def test_repeating_queue_allele_factory():
    factory = RepeatingQueueAlleleFactory(alleles=['a', 1, True, None])
    for _ in range(3):
        assert factory.spawn() == 'a'
        assert factory.spawn() == 1
        assert factory.spawn() == True
        assert factory.spawn() is None


@patch('random.choice', autospec=True)
def test_random_selection_allele_factory(mock_choice: Mock):
    mock_choice.side_effect = [None, 1]
    factory = RandomChoiceAlleleFactory(alleles=['a', 1, True, None])
    assert factory.spawn() is None
    assert factory.spawn() == 1
    assert mock_choice.mock_calls == 2 * [call(factory.alleles)]