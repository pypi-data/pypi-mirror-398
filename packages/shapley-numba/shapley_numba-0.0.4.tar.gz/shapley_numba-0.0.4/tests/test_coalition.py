"""
Tests based on coalition value
"""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from shapley_numba.examples import CoalitionGame
from shapley_numba.shapley import shapley

TEST_DATA = (
    'num_players, seats, expected',
    [
        (3, [40, 15, 25], [2 / 3, 1 / 6, 1 / 6]),
        (3, [40, 30, 25], [1 / 3, 1 / 3, 1 / 3]),
        (4, [40, 30, 20, 10], [5 / 12, 1 / 4, 1 / 4, 1 / 12]),
    ],
)


@pytest.mark.parametrize(*TEST_DATA)
def test_coalition(num_players, seats, expected):
    coalition_game = CoalitionGame(np.array(seats, dtype=np.float64))
    result = shapley(coalition_game, num_players)
    assert_allclose(result, expected)
