"""Tools for games.

Currently only creating dual game for peel-off Harsanyi dividends..
"""

import numba
import numpy as np

from shapley_numba.core import numba_game
from shapley_numba.typing import (
    CoalitionType,
    GameProtocol,
    ShapleyNumbaGameProtocol,
)

__all__ = ['dual_game']


def dual_game(
    game: GameProtocol | ShapleyNumbaGameProtocol, num_players: int
) -> ShapleyNumbaGameProtocol:
    """Create the dual of the game.

    The dual game is useful for computing "peel-off" Harsanyi dividends.

    Parameters
    ----------
    game : GameProtocol | ShapleyNumbaGameProtocol
        The original game to create a dual for.
    num_players : int
        Number of players in the game.

    Returns
    -------
    ShapleyNumbaGameProtocol
        The dual game wrapped with numba_game decorator.

    """
    if hasattr(game, 'jitted_class'):
        game_spec = [
            ('_original_game', game.jitted_class.class_type.instance_type),
            ('total', numba.float64),
        ]
    else:
        game_spec = None

    @numba_game(game_spec)
    class DualGame:
        """Define dual of game."""

        def __init__(self, game: GameProtocol) -> None:
            self._original_game = game
            self.total = self._original_game.value(np.ones(num_players, dtype=np.int32))

        def value(self, subset: CoalitionType) -> np.float64:
            return self.total - self._original_game.value(1 - subset)

    if hasattr(game, 'jitted_game'):
        return DualGame(game.jitted_game)  # type: ignore[return-value]
    return DualGame(game.game)  # type: ignore[return-value]
