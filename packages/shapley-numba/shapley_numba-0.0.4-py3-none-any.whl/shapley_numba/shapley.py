"""Shapley value computation using numba.

Provides a jitted version of Shapley value computation.
And Monte Carlo approximation of Shapley value.
"""

import logging
import math
from typing import cast

import numba
import numpy as np
from numpy.typing import NDArray

from shapley_numba.typing import GameProtocol, ShapleyNumbaGameProtocol

logger = logging.getLogger(__name__)

__all__ = ['shapley', 'shapley_perm_mc']


@numba.jit(nopython=True)
def compute_coeffs(num_players: int) -> NDArray[np.float64]:
    """Compute 1/C(num_players-1, k) for k=0 to num_players-1."""
    if num_players == 1:
        return np.array([1.0, 0.0])
    result = np.zeros(num_players + 1, dtype=np.float64)
    current_log = 0.0
    iterations = num_players - 1
    for index in range(num_players // 2 + num_players % 2):
        value = math.exp(current_log)
        result[index] = value
        result[iterations - index] = value
        current_log += math.log(index + 1) - math.log(iterations - index)
    return result


def shapley(
    game: ShapleyNumbaGameProtocol, num_players: int, *, use_numba: bool = True
) -> NDArray[np.float64]:
    """Compute shapley value of a game.

    Parameters
    ----------
    game: ShapleyNumbaGameProtocol
        `numba-game` or a class that implements `value` function.
    num_players: int
        number of players in the game.
    use_numba: bool
        try to use numba-compiled version of the game.

    Returns
    -------
    np.array[np.float64] - shapley value of the game.

    Raises
    ------
    ValueError - when `use_numba=True` but
                the game failed to be compiled with numba or was never compiled.

    """
    coeffs = np.array(compute_coeffs(num_players))
    if not hasattr(game, 'game') and not hasattr(game.game, 'value'):
        logger.warning(
            'not a numba game. Please use numba_game decorator from shapley_numba.core'
        )
    if use_numba:
        if not hasattr(game, 'jitted_game'):
            logger.warning(
                'not a numba game. Please use numba_game decorator from '
                'shapley_numba.core'
            )
            return cast(
                NDArray[np.float64], shapley_jit.py_func(num_players, game, coeffs)
            )
        else:
            if isinstance(game.jitted_game, Exception):
                exc = game.jitted_game
                raise ValueError(
                    'The game failed to compile with numba\n'
                    'Either use `use_numba=False`'
                    ' or fix compilation error\n'
                    f'{exc.__class__.__name__}: {exc}'
                )

        return cast(
            NDArray[np.float64], shapley_jit(num_players, game.jitted_game, coeffs)
        )
    if not hasattr(game, 'value'):
        raise ValueError(f'game {game} has to implement value method')
    return cast(NDArray[np.float64], shapley_jit.py_func(num_players, game, coeffs))


@numba.jit(nopython=True)
def shapley_jit(
    num_players: int, game: GameProtocol, coeffs: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Compute shapley value of a game using numba jit."""
    result = np.zeros(num_players)
    for subset_int in range(2**num_players):
        subset = np.zeros(num_players, dtype=np.int32)
        i = 0
        while subset_int > 0:
            subset[i] = subset_int % 2
            i += 1
            subset_int = subset_int >> 1
        val = game.value(subset)
        set_size = int(np.sum(subset))
        if set_size == 0:
            contains = 0
        else:
            contains = coeffs[set_size - 1] * val
        contains_not = -coeffs[set_size] * val
        result += subset * contains + (1 - subset) * contains_not
    return result / num_players


def shapley_perm_mc(
    game: ShapleyNumbaGameProtocol,
    num_players: int,
    paths: int = 40_000,
    seed: int | None = 0xDEADBEEF,
    use_numba: bool = True,
) -> NDArray[np.float64]:
    """Compute shapley value of a game using permutation Monte Carlo.

    Parameters
    ----------
    game : object
        Game object with value method.
    num_players : int
        Number of players in the game.
    paths : int, optional
        Number of Monte Carlo paths, by default 4e4.
    seed : int, optional
        Seed for random number generator, by default 0xDEADBEEF
        in order to maintain reproducibility.
        Pass `None` to get a random result.
    use_numba : bool, optional
        Whether to use numba jit compiled function, by default True.

    Returns
    -------
    numpy.ndarray
        Shapley value for each player.

    Raises
    ------
    ValueError
        If the game fails to compile with numba and `use_numba` is True.
        If the game does not implement a `value` method and `use_numba` is False.

    """
    if not hasattr(game, 'game') and not hasattr(game.game, 'value'):
        logger.warning(
            'not a numba game. Please use numba_game decorator from shapley_numba.core'
        )
    if use_numba:
        if not hasattr(game, 'jitted_game'):
            logger.warning(
                'not a numba game. Please use numba_game decorator from '
                'shapley_numba.core'
            )
        else:
            if isinstance(game.jitted_game, Exception):
                exc = game.jitted_game
                raise ValueError(
                    'The game failed to compile with numba\n'
                    'Either use `use_numba=False`'
                    ' or fix compilation error\n'
                    f'{exc.__class__.__name__}: {exc}'
                )
        if seed is None:
            seed = np.random.randint(0, 2**32)
        return cast(
            NDArray[np.float64],
            _shapley_perm_mc(game.jitted_game, num_players, paths, seed),
        )
    if not hasattr(game, 'value'):
        raise ValueError(f'game {game} has to implement value method')
    return cast(
        NDArray[np.float64], _shapley_perm_mc.py_func(game, num_players, paths, seed)
    )


@numba.jit(nopython=True)
def _shapley_perm_mc(
    game: GameProtocol, num_players: int, paths: int, seed: int
) -> NDArray[np.float64]:
    """Compute shapley value of a game using permutation Monte Carlo."""
    result = np.zeros(num_players)
    perm = np.arange(num_players)
    np.random.seed(seed)
    for _ in range(paths):
        np.random.shuffle(perm)
        subset = np.zeros(num_players, dtype=np.int32)
        val_without = 0.0
        for index in range(num_players):
            player = perm[index]
            subset[player] = 1  # HORROR, MUTATION
            val_with = game.value(subset)
            result[player] += val_with - val_without
            val_without = val_with
    return result / paths
