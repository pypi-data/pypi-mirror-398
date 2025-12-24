"""Tests based on 'glove game' - number of left/right gloves."""

import pytest
from numpy.testing import assert_allclose

from shapley_numba.examples import GloveGame
from shapley_numba.shapley import shapley

TEST_DATA = (
    'num_players, num_left_gloves, expected',
    [
        (1, 0, [0]),
        (1, 1, [0]),
        (2, 1, [1 / 2, 1 / 2]),
        (3, 1, [2 / 3, 1 / 6, 1 / 6]),
        (3, 2, [1 / 6, 1 / 6, 2 / 3]),
        (3, 3, [0, 0, 0]),
        (4, 1, [3 / 4, 1 / 12, 1 / 12, 1 / 12]),
        (4, 2, [1 / 2, 1 / 2, 1 / 2, 1 / 2]),
        (4, 3, [1 / 12, 1 / 12, 1 / 12, 3 / 4]),
        (4, 4, [0, 0, 0, 0]),
        (5, 1, [4 / 5, 1 / 20, 1 / 20, 1 / 20, 1 / 20]),
        (5, 2, [13 / 20, 13 / 20, 7 / 30, 7 / 30, 7 / 30]),
        (5, 3, [7 / 30, 7 / 30, 7 / 30, 13 / 20, 13 / 20]),
        (5, 4, [1 / 20, 1 / 20, 1 / 20, 1 / 20, 4 / 5]),
        (6, 2, [11 / 15, 11 / 15, 4 / 30, 4 / 30, 4 / 30, 4 / 30]),
    ],
)


@pytest.mark.parametrize(*TEST_DATA)
def test_glove(num_players, num_left_gloves, expected):
    glove_game = GloveGame(num_left_gloves)
    result = shapley(glove_game, num_players)
    assert_allclose(result, expected)


@pytest.mark.parametrize('num_players', range(4, 7))
def test_two_left_gloves(num_players):
    glove_game = GloveGame(2)
    result = shapley(glove_game, num_players)
    left_glove = (num_players - 2) / (num_players - 1) - 2 / (
        (num_players - 1) * num_players
    )
    right_glove = 2 / ((num_players - 1) * (num_players - 2)) + 4 / (
        num_players * (num_players - 1) * (num_players - 2)
    )
    expected = [left_glove] * 2 + [right_glove] * (num_players - 2)
    assert_allclose(result, expected)

@pytest.mark.requires_jit
@pytest.mark.parametrize('num_players', range(7, 25))
def test_two_left_gloves_large(num_players):
    glove_game = GloveGame(2)
    result = shapley(glove_game, num_players)
    left_glove = (num_players - 2) / (num_players - 1) - 2 / (
        (num_players - 1) * num_players
    )
    right_glove = 2 / ((num_players - 1) * (num_players - 2)) + 4 / (
        num_players * (num_players - 1) * (num_players - 2)
    )
    expected = [left_glove] * 2 + [right_glove] * (num_players - 2)
    assert_allclose(result, expected)
