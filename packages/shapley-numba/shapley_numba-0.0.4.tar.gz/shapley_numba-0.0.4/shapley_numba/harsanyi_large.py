"""Numba jit compiled computation of Harsanyi dividends for arbitrary number of players.

This implementation generates specialized JIT-compiled functions for each player count,
removing the 63-player limitation while maintaining full Numba acceleration.
"""

from typing import Callable, cast

import numba
import numpy as np
from numba.typed import Dict

from shapley_numba.common import subsets_of_next_fixed_size, subsets_of_subset
from shapley_numba.core import has_jitted_game
from shapley_numba.typing import CoalitionType, ShapleyNumbaGameProtocol


def _generate_harsanyi_function(
    num_players: int,
) -> Callable[[ShapleyNumbaGameProtocol, int], dict[tuple[int, ...], float]]:
    """Generate a specialized Harsanyi dividends function.

    Creates a function for a specific number of players.

    This creates a JIT-compiled function with the tuple size known at compile time.

    Parameters
    ----------
    num_players : int
        Number of players in the game

    Returns
    -------
    function
        JIT-compiled function that computes Harsanyi dividends

    """
    # Create the tuple type with fixed size
    tuple_type = numba.types.UniTuple(numba.int32, num_players)

    # Generate array_to_tuple function code dynamically
    # This creates explicit tuple construction: (arr[0], arr[1], ..., arr[n-1])
    # NOTE: We use exec here as a workaround for a Numba limitation.
    # Numba requires the size of a tuple to be a compile-time constant.
    # By generating the code dynamically, we can create a specialized
    # function for each `num_players` with a hardcoded tuple size.
    tuple_elements = ', '.join(f'arr[{i}]' for i in range(num_players))
    array_to_tuple_code = f"""
@numba.njit
def array_to_tuple(arr):
    return ({tuple_elements})
"""

    # Execute the generated code to create the function
    local_scope = {'numba': numba}
    exec(array_to_tuple_code, local_scope)
    array_to_tuple = local_scope['array_to_tuple']  # type: ignore[misc]

    @numba.jit(nopython=True)
    def _harsanyi_dividends_impl(game: ShapleyNumbaGameProtocol, size: int):
        """Compute Harsanyi dividends for specific number of players."""
        if size > num_players:
            size = num_players

        current_size = 1
        result_map = Dict.empty(key_type=tuple_type, value_type=numba.float64)

        # Empty coalition
        subset = np.zeros(num_players, dtype=np.int32)
        result_map[array_to_tuple(subset)] = float(game.value(subset))  # type: ignore[operator]

        # Single player coalitions
        for player in range(num_players):
            subset[player] = 1
            result_map[array_to_tuple(subset)] = float(game.value(subset))  # type: ignore[operator]
            subset[player] = 0

        # Higher size coalitions
        subsets_arr, last_pos = subsets_of_next_fixed_size(
            num_players,
            1,
            np.zeros((1, num_players), dtype=np.int32),
            np.zeros(num_players, dtype=np.int32),
        )

        while current_size < size:
            current_size += 1
            subsets_arr, last_pos = subsets_of_next_fixed_size(
                num_players, current_size, subsets_arr, last_pos
            )
            for subset in subsets_arr:
                hd = game.value(subset)
                for subsubset in subsets_of_subset(subset, self_included=False):
                    hd -= result_map[array_to_tuple(subsubset)]  # type: ignore[operator]
                result_map[array_to_tuple(subset)] = hd  # type: ignore[operator]

        return result_map

    return cast(
        Callable[[ShapleyNumbaGameProtocol, int], dict[tuple[int, ...], float]],
        _harsanyi_dividends_impl,
    )


# Cache compiled functions to avoid recompilation
_compiled_functions_cache = {}


def _get_harsanyi_function(num_players):
    """Get or create a JIT-compiled Harsanyi function for the given player count.

    Parameters
    ----------
    num_players : int
        Number of players in the game

    Returns
    -------
    function
        JIT-compiled Harsanyi dividends function

    """
    if num_players not in _compiled_functions_cache:
        _compiled_functions_cache[num_players] = _generate_harsanyi_function(
            num_players
        )
    return _compiled_functions_cache[num_players]


class HarsanyiDividendsLarge:
    """Harsanyi Dividends class for arbitrary number of players.

    This implementation generates specialized JIT-compiled functions for each
    player count, removing the 63-player limitation while maintaining full
    Numba acceleration.

    The first call for a given player count will trigger JIT compilation,
    subsequent calls with the same player count will reuse the compiled function.
    """

    def __init__(
        self, game: ShapleyNumbaGameProtocol, num_players: int, size: int | None = None
    ):
        """Initialize the HarsanyiDividendsLarge class.

        Parameters
        ----------
        game : game object
            Game object with jitted_game attribute
        num_players : int
            Number of players in the game
        size : int, optional
            Maximum coalition size to compute dividends for.
            If None, computes for all coalition sizes.

        Raises
        ------
        NotImplementedError
            If game is not jit-compiled

        Notes
        -----
        The first time this is called for a given num_players value,
        it will compile a specialized function. This compilation takes
        a few seconds, but subsequent calls with the same num_players
        will be instant.

        """
        self.num_players = num_players
        if not has_jitted_game(game):
            raise NotImplementedError(
                'This implementation works only for jit-compiled games'
            )

        # Get or compile the specialized function for this player count
        harsanyi_func = _get_harsanyi_function(num_players)

        # Compute the dividends
        self.result_map = harsanyi_func(game.jitted_game, size)

    def __call__(self, subset: CoalitionType) -> np.float64:
        """Return the dividend for a subset.

        Parameters
        ----------
        subset : array-like
            Binary array indicating which players are in the subset

        Returns
        -------
        float
            The Harsanyi dividend for the given subset

        Notes
        -----
        If the subset was not computed (beyond the specified size),
        returns 0.0.

        """
        key = tuple(subset)
        return cast(np.float64, self.result_map.get(key, 0.0))
