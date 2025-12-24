"""Typing concepts for shapley_numba.

This module provides Protocol definitions and type aliases for working with
cooperative games in shapley-numba.

Examples
--------
Define a custom game that implements the GameProtocol::

    import numpy as np
    from shapley_numba import GameProtocol, CoalitionType, numba_game

    @numba_game()
    class MyGame:
        def __init__(self, data):
            self.data = data

        def value(self, subset: CoalitionType) -> np.float64:
            # Return value for the given coalition
            return np.float64(np.sum(self.data * subset))

    # Use with shapley value computation
    game = MyGame(np.array([1.0, 2.0, 3.0]))
    # shapley_values = shapley(game, num_players=3)

"""

from typing import Protocol, TypeAlias

from numpy import float64, int32
from numpy.typing import NDArray

__all__ = [
    'CoalitionType',
    'GameProtocol',
    'ShapleyNumbaGameProtocol',
    'GameSpecType',
]

# Shapley-numba set/coalition representation
CoalitionType: TypeAlias = NDArray[int32]
"""Type for coalition representation: binary array where 1 = player in coalition.

A coalition is represented as a binary array where each element corresponds to
a player. A value of 1 indicates the player is in the coalition, and 0 indicates
they are not.

Example: For 3 players, the coalition {0, 2} is represented as [1, 0, 1].
"""


class GameProtocol(Protocol):
    """Protocol that defines the interface for a cooperative game.

    Any class implementing this protocol can be used with shapley-numba functions.
    The only requirement is a `value` method that computes the worth of a coalition.

    Methods
    -------
    value(subset: CoalitionType) -> float64
        Compute the value (worth) of a given coalition of players.

    """

    def value(self, subset: CoalitionType) -> float64:
        """Return the value of coalition.

        Parameters
        ----------
        subset : CoalitionType
            Binary array indicating which players are in the coalition.

        Returns
        -------
        float64
            The value (worth) of the coalition.

        """
        ...


class ShapleyNumbaGameProtocol(Protocol):
    """Protocol for games wrapped by the numba_game decorator.

    When a game class is decorated with `@numba_game`, it gains additional
    attributes that provide both regular and JIT-compiled versions of the game.
    This protocol describes the interface of such decorated games.

    Attributes
    ----------
    game : GameProtocol
        The original (non-compiled) game instance.
    jitted_game : GameProtocol | Exception
        The numba JIT-compiled game instance, or an Exception if compilation failed.

    Methods
    -------
    value(subset: CoalitionType) -> float64
        Compute the value of a coalition, automatically using the compiled
        version if available, otherwise falling back to the Python version.

    """

    game: GameProtocol
    jitted_game: GameProtocol | Exception

    def value(self, subset: CoalitionType) -> float64:
        """Return the value of coalition.

        Parameters
        ----------
        subset : CoalitionType
            Binary array indicating which players are in the coalition.

        Returns
        -------
        float64
            The value (worth) of the coalition.

        """
        ...


GameSpecType: TypeAlias = dict[str, type] | list[tuple[str, type]] | None
"""Type for numba jitclass specifications.

The game specification defines the types of attributes in a game class for
numba compilation. Can be:
- A dictionary mapping attribute names to types: {'attr': numba.float64}
- A list of tuples: [('attr', numba.float64)]
- None for games without attributes or auto-detection
"""
