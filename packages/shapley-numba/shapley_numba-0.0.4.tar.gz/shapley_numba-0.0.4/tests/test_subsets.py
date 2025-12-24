from math import comb

import numpy as np
import pytest
from numpy.testing import assert_equal

from shapley_numba.common import (
    combs_jit,
    subsets,
    subsets_of_fixed_size,
    subsets_of_subset,
)


def test_subsets_2_3():
    s = subsets(3)
    assert next(s).tolist() == [0, 0, 0]
    assert next(s).tolist() == [1, 0, 0]
    assert next(s).tolist() == [0, 1, 0]
    assert next(s).tolist() == [1, 1, 0]
    assert next(s).tolist() == [0, 0, 1]
    assert next(s).tolist() == [1, 0, 1]
    assert next(s).tolist() == [0, 1, 1]
    assert next(s).tolist() == [1, 1, 1]
    with pytest.raises(StopIteration):
        next(s)
    assert list(subsets(1)) == [[0], [1]]


def test_subsets_of_subset():
    s = subsets_of_subset(np.array([1, 1, 0]))
    assert next(s).tolist() == [0, 0, 0]
    assert next(s).tolist() == [1, 0, 0]
    assert next(s).tolist() == [0, 1, 0]
    assert next(s).tolist() == [1, 1, 0]
    assert_equal(
        np.array(list(subsets_of_subset(np.array([1, 0, 1])))),
        [[0, 0, 0], [1, 0, 0], [0, 0, 1], [1, 0, 1]],
    )


def test_subsets_of_subset_3_7():
    s = subsets_of_subset(np.array([0, 1, 0, 1, 0, 1, 0]))
    assert next(s).tolist() == [0, 0, 0, 0, 0, 0, 0]
    assert next(s).tolist() == [0, 1, 0, 0, 0, 0, 0]
    assert next(s).tolist() == [0, 0, 0, 1, 0, 0, 0]
    assert next(s).tolist() == [0, 1, 0, 1, 0, 0, 0]
    assert next(s).tolist() == [0, 0, 0, 0, 0, 1, 0]
    assert next(s).tolist() == [0, 1, 0, 0, 0, 1, 0]
    assert next(s).tolist() == [0, 0, 0, 1, 0, 1, 0]
    assert next(s).tolist() == [0, 1, 0, 1, 0, 1, 0]
    with pytest.raises(StopIteration):
        next(s)


def test_combs_jit_basic():
    assert_equal(combs_jit(3), [3, 3])
    assert_equal(combs_jit(4), [4, 6, 4])
    assert_equal(combs_jit(5), [5, 10, 10, 5])
    assert_equal(combs_jit(6), [6, 15, 20, 15, 6])
    assert_equal(combs_jit(7), [7, 21, 35, 35, 21, 7])


# random choices for numbers
@pytest.mark.parametrize('num_players', [7, 15])
def test_combs_jit(num_players):
    combs = combs_jit(num_players)
    expected = [comb(num_players, k + 1) for k in range(num_players - 1)]
    assert_equal(combs, expected)


@pytest.mark.requires_jit
@pytest.mark.parametrize('num_players', [19, 24, 33])
def test_combs_jit_large(num_players):
    combs = combs_jit(num_players)
    expected = [comb(num_players, k + 1) for k in range(num_players - 1)]
    assert_equal(combs, expected)


@pytest.mark.requires_jit
def test_combs_jit_max_with_int32_is_33():
    num_players = 33
    combs = combs_jit(num_players)
    expected = [comb(num_players, k + 1) for k in range(num_players - 1)]
    assert_equal(combs, expected)


@pytest.mark.requires_jit
@pytest.mark.parametrize(
    'max_num_players, type_', [(17, np.int16), (33, np.int32), (61, np.int64)]
)
def test_max_num_players(max_num_players, type_):
    combs = combs_jit(max_num_players, type_)
    expected = [comb(max_num_players, k + 1) for k in range(max_num_players - 1)]
    assert_equal(combs, expected)


def test_subsets_of_fixed_size_3():
    assert_equal(subsets_of_fixed_size(3, 1), [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert_equal(subsets_of_fixed_size(3, 2), [[1, 1, 0], [1, 0, 1], [0, 1, 1]])
    assert_equal(subsets_of_fixed_size(3, 3), [[1, 1, 1]])


def test_subsets_of_fixed_size_4():
    assert_equal(
        subsets_of_fixed_size(4, 1),
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
    )
    assert_equal(
        subsets_of_fixed_size(4, 2),
        [
            [1, 1, 0, 0],
            [1, 0, 1, 0],
            [1, 0, 0, 1],
            [0, 1, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 1],
        ],
    )
    assert_equal(
        subsets_of_fixed_size(4, 3),
        [[1, 1, 1, 0], [1, 1, 0, 1], [1, 0, 1, 1], [0, 1, 1, 1]],
    )
    assert_equal(subsets_of_fixed_size(4, 4), [[1, 1, 1, 1]])
