"""Tests based on wikipedia example."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from shapley_numba.examples import WikipediaExample
from shapley_numba.harsanyi import HarsanyiDividends
from shapley_numba.harsanyi_naive import harsanyi_dividends
from shapley_numba.shapley import shapley, shapley_perm_mc


def test_wikipedia_example_shapley():
    num_players = 3
    game = WikipediaExample()
    result = shapley(game, num_players)
    assert_allclose(result, [120, 80, 80])


def test_wikipedia_example_shapley_perm_mc():
    num_players = 3
    game = WikipediaExample()
    result = shapley_perm_mc(game, num_players)
    assert_allclose(result, [120.5675, 80.089, 79.3435])

@pytest.mark.requires_jit
def test_wikipedia_example_shapley_perm_mc_python():
    num_players = 3
    game = WikipediaExample()
    result = shapley_perm_mc(game, num_players, use_numba=False)
    assert_allclose(result, [120.5675, 80.089, 79.3435])


def test_wikipedia_example_shapley_perm_mc_more_paths():
    num_players = 3
    game = WikipediaExample()
    result = shapley_perm_mc(game, num_players, 100_000)
    assert_allclose(result, [120.2712, 79.7904, 79.9384])


def test_wikipedia_example_shapley_perm_mc_no_seed_set():
    num_players = 3
    game = WikipediaExample()
    result = shapley_perm_mc(game, num_players, seed=None)
    assert result != pytest.approx([120.5675, 80.089, 79.3435])


def test_wikipedia_example_shapley_perm_mc_no_seed_set_random():
    num_players = 3
    game = WikipediaExample()
    result1 = shapley_perm_mc(game, num_players, seed=None)
    result2 = shapley_perm_mc(game, num_players, seed=None)
    assert result1 != pytest.approx(result2)


def test_wikipedia_example_harsanyi():
    game = WikipediaExample()
    hd = HarsanyiDividends(game, 3)
    assert_allclose(hd(np.array([0, 0, 0], dtype=np.int32)), 0)
    assert_allclose(hd(np.array([1, 0, 0], dtype=np.int32)), 30)
    assert_allclose(hd(np.array([0, 1, 0], dtype=np.int32)), 20)
    assert_allclose(hd(np.array([0, 0, 1], dtype=np.int32)), 10)
    assert_allclose(hd(np.array([1, 1, 0], dtype=np.int32)), 40)
    assert_allclose(hd(np.array([1, 0, 1], dtype=np.int32)), 60)
    assert_allclose(hd(np.array([0, 1, 1], dtype=np.int32)), 0)
    assert_allclose(hd(np.array([1, 1, 1], dtype=np.int32)), 120)


@pytest.mark.requires_jit
@pytest.mark.parametrize('use_numba', [True, False], ids=['numba', 'python'])
def test_wikipedia_example_harsanyi_naive(use_numba):
    game = WikipediaExample()
    # d(empty) = 0
    assert (
        harsanyi_dividends(
            game, np.array([0, 0, 0], dtype=np.int32), use_numba=use_numba
        )
        == 0
    )
    # d(you) = v(you) - v(empty) = 30 - 0 = 30
    assert (
        harsanyi_dividends(
            game, np.array([1, 0, 0], dtype=np.int32), use_numba=use_numba
        )
        == 30
    )
    # d(Emma) = v(Emma) - v(empty) = 20 - 0 = 20
    assert (
        harsanyi_dividends(
            game, np.array([0, 1, 0], dtype=np.int32), use_numba=use_numba
        )
        == 20
    )
    # d(Liam) = v(Liam) - v(empty) = 10 - 0 = 10
    assert (
        harsanyi_dividends(
            game, np.array([0, 0, 1], dtype=np.int32), use_numba=use_numba
        )
        == 10
    )
    # d(you, Emma) = v(you, Emma) - v(you) - v(Emma) + v(empty) = 90 - 30 - 20 + 0 = 40
    assert (
        harsanyi_dividends(
            game, np.array([1, 1, 0], dtype=np.int32), use_numba=use_numba
        )
        == 40
    )
    # d(you, Liam) = v(you, Liam) - v(you) - v(Liam) + v(empty) = 100 - 30 - 10 + 0 = 60
    assert (
        harsanyi_dividends(
            game, np.array([1, 0, 1], dtype=np.int32), use_numba=use_numba
        )
        == 60
    )
    # d(Emma, Liam) = v(Emma, Liam) - v(Emma) - v(Liam) + v(empty) = 30 - 20 - 10 + 0
    # = 0
    assert (
        harsanyi_dividends(
            game, np.array([0, 1, 1], dtype=np.int32), use_numba=use_numba
        )
        == 0
    )
    # d(you, Emma, Liam) = v(you, Emma, Liam) - v(you, Emma) - v(you, Liam)
    # - v(Emma, Liam) + v(you) + v(Emma) + v(Liam) - v(empty)
    # = 280 - 90 - 100 - 30 + 30 + 20 + 10 - 0 = 120
    assert (
        harsanyi_dividends(
            game, np.array([1, 1, 1], dtype=np.int32), use_numba=use_numba
        )
        == 120
    )
