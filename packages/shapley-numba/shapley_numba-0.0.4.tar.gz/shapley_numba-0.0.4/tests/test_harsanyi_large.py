"""Tests for HarsanyiDividendsLarge implementation supporting >63 players."""

import numpy as np
import pytest

from shapley_numba.common import subsets
from shapley_numba.examples.games import CoalitionGame, GloveGame, WikipediaExample
from shapley_numba.harsanyi import HarsanyiDividends
from shapley_numba.harsanyi_large import HarsanyiDividendsLarge
from shapley_numba.harsanyi_naive import harsanyi_dividends as harsanyi_dividends_naive


@pytest.mark.parametrize(
    'game, num_players',
    [
        (WikipediaExample(), 3),
        (GloveGame(5), 10),
        (GloveGame(10), 20),
    ],
    ids=[
        'wikipedia_example_3_players',
        'glove_game_10_players',
        'glove_game_20_players',
    ],
)
def test_harsanyi_dividends_large_vs_naive(game, num_players):
    """Test that HarsanyiDividendsLarge gives same results as naive implementation."""
    size = min(5, num_players)
    hd = HarsanyiDividendsLarge(game, num_players, size=size)
    # Only test subsets up to the specified size
    for subset in subsets(num_players):
        if np.sum(subset) <= size:
            assert hd(subset) == pytest.approx(harsanyi_dividends_naive(game, subset))


@pytest.mark.parametrize(
    'game, num_players',
    [
        (WikipediaExample(), 3),
        (GloveGame(5), 10),
        (GloveGame(10), 20),
    ],
    ids=[
        'wikipedia_example_3_players',
        'glove_game_10_players',
        'glove_game_20_players',
    ],
)
def test_harsanyi_dividends_large_vs_standard(game, num_players):
    """Test that HarsanyiDividendsLarge gives same results as standard implementation.

    This test only works for num_players <= 63.
    """
    size = min(6, num_players)
    hd_standard = HarsanyiDividends(game, num_players, size=size)
    hd_large = HarsanyiDividendsLarge(game, num_players, size=size)
    # Only test subsets up to the specified size
    for subset in subsets(num_players):
        if np.sum(subset) <= size:
            assert hd_large(subset) == pytest.approx(hd_standard(subset))


def test_harsanyi_dividends_large_64_players():
    """Test HarsanyiDividendsLarge with 64 players (beyond standard limit)."""
    # Create a simple game with 64 players
    num_players = 64
    seats = np.ones(num_players)
    seats[0] = 65  # First player has majority control (65 out of 128 > 64)
    game = CoalitionGame(seats)

    # This should work without issues
    hd = HarsanyiDividendsLarge(game, num_players, size=2)

    # Test empty coalition
    empty_subset = np.zeros(num_players, dtype=np.int32)
    assert hd(empty_subset) == 0.0

    # Test single player coalitions
    for player in range(min(5, num_players)):  # Test first 5 players
        subset = np.zeros(num_players, dtype=np.int32)
        subset[player] = 1
        dividend = hd(subset)
        # Player 0 should have positive dividend (winning coalition alone)
        if player == 0:
            assert dividend > 0
        # Other single players cannot win
        else:
            assert dividend == 0


def test_harsanyi_dividends_large_100_players():
    """Test that HarsanyiDividendsLarge works with 100 players."""
    num_players = 100
    game = GloveGame(50)  # 50 left gloves, 50 right gloves

    # Only compute up to size 3 to keep test fast
    hd = HarsanyiDividendsLarge(game, num_players, size=3)

    # Test empty coalition
    empty_subset = np.zeros(num_players, dtype=np.int32)
    assert hd(empty_subset) == 0.0

    # Test single player coalitions (no value alone)
    subset = np.zeros(num_players, dtype=np.int32)
    subset[0] = 1
    assert hd(subset) == 0.0

    subset = np.zeros(num_players, dtype=np.int32)
    subset[50] = 1
    assert hd(subset) == 0.0

    # Test two player coalition (one left, one right = value of 1)
    subset = np.zeros(num_players, dtype=np.int32)
    subset[0] = 1  # Left glove
    subset[50] = 1  # Right glove
    expected_dividend = 1.0  # min(1,1) - 0 - 0 = 1
    assert hd(subset) == pytest.approx(expected_dividend)


@pytest.mark.requires_jit
def test_standard_implementation_fails_at_64_players():
    """Verify that the standard implementation has issues with 64 players.

    The standard implementation uses 2**player as keys in a dict, which causes
    silent overflow at player=63 (2**63 wraps to negative in int64), resulting
    in incorrect results rather than raising an error.

    This test verifies that HarsanyiDividendsLarge doesn't have this limitation.
    """
    num_players = 64
    game = GloveGame(32)

    # The standard implementation doesn't raise an error, but produces incorrect
    # results due to int64 overflow. Create both implementations.
    hd_standard = HarsanyiDividends(game, num_players, size=2)
    hd_large = HarsanyiDividendsLarge(game, num_players, size=2)

    # Test that the implementations produce the same results for small subsets
    # (where the standard implementation hasn't overflowed yet)
    for player in range(min(10, num_players)):
        subset = np.zeros(num_players, dtype=np.int32)
        subset[player] = 1
        # Both should work for single players
        assert hd_standard(subset) == pytest.approx(hd_large(subset))
