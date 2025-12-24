"""Numba jit compiled computation of Harsanyi dividends."""

from typing import cast

import numba
import numpy as np
from numba.typed import Dict
from numpy import float64

from shapley_numba.common import subsets_of_next_fixed_size, subsets_of_subset
from shapley_numba.core import has_jitted_game
from shapley_numba.typing import CoalitionType, GameProtocol, ShapleyNumbaGameProtocol

__all__ = ['HarsanyiDividends']


@numba.jit(nopython=True)
def _harsanyi_dividends(game: GameProtocol, num_players: int, size: int) -> Dict:
    """Compute Harsanyi dividends."""
    current_size = 1
    result_map = Dict.empty(key_type=numba.int32, value_type=numba.float64)
    subset = np.zeros(num_players, dtype=np.int32)
    result_map[0] = game.value(subset)
    players_index = 2 ** np.arange(num_players, dtype=np.int64)
    for player in range(num_players):
        subset[player] = 1
        result_map[2**player] = game.value(subset)
        subset[player] = 0
    subsets, last_pos = subsets_of_next_fixed_size(
        num_players,
        1,
        np.zeros((1, num_players), dtype=np.int32),
        np.zeros(num_players, dtype=np.int32),
    )
    while current_size < size:
        current_size += 1
        subsets, last_pos = subsets_of_next_fixed_size(
            num_players, current_size, subsets, last_pos
        )
        for subset in subsets:
            hd = game.value(subset)
            for subsubset in subsets_of_subset(subset, self_included=False):
                hd -= result_map[np.sum(players_index * subsubset)]
            result_map[np.sum(players_index * subset)] = hd
    return result_map


class HarsanyiDividends:
    """Harsanyi Dividends class.

    Wrapper for the numba jit compiled function.

    Usage:
    ```python
    game = GloveGame(2)

    hd = HarsanyiDividends(game, 5, 3)

    hd(np.array([1, 1, 0, 0, 0])
    ```
    """

    def __init__(
        self, game: ShapleyNumbaGameProtocol, num_players: int, size: int | None = None
    ) -> None:
        """Initialize the HarsanyiDividends class.

        Compute all dividends up to size `size` and
        store them as a map

        Parameters
        ----------
        game : ShapleyNumbaGameProtocol
            A game wrapped with the numba_game decorator.
        num_players : int
            Number of players in the game.
        size : int | None, optional
            Maximum coalition size to compute dividends for.
            If None, computes for all coalition sizes. Default is None.

        Raises
        ------
        NotImplementedError
            If the game is not JIT-compiled.

        """
        if size is None:
            size = num_players
        self.num_players = num_players
        self.player_index = 2 ** np.arange(num_players, dtype=np.int64)
        if not has_jitted_game(game):
            raise NotImplementedError(
                'This implementation works only for jit-compiled games'
            )
        # has_jitted_game ensures jitted_game is not an Exception
        jitted = cast(GameProtocol, game.jitted_game)
        self.result_map = _harsanyi_dividends(jitted, num_players, size)

    def __call__(self, subset: CoalitionType) -> float64:
        """Return the dividend for a subset.

        Parameters
        ----------
        subset : CoalitionType
            Binary array indicating which players are in the coalition.

        Returns
        -------
        float64
            The Harsanyi dividend for the given coalition.

        """
        index = np.sum(self.player_index * subset)
        return float64(self.result_map[index])
