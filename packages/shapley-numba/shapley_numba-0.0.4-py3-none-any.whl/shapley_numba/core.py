"""Core functions to work with shapley-numba."""

from functools import wraps
from logging import getLogger
from typing import Callable

from numba.experimental import jitclass
from numpy import float64

from shapley_numba.typing import (
    CoalitionType,
    GameProtocol,
    GameSpecType,
    ShapleyNumbaGameProtocol,
)

logger = getLogger(__name__)

__all__ = ['numba_game', 'has_jitted_game', 'numba_game_func']


def numba_game(
    gamespec: GameSpecType=None,
) -> Callable[[type[GameProtocol]], type[ShapleyNumbaGameProtocol]]:
    """Decorate the game to allow use of games with numba and without.

    The game class needs to implement a `value` method with parameter `subset`.
    `subset` is a numpy integer array of zeros and ones indicating membership
    in every subset.
    """

    def decorator(cls: type[GameProtocol]) -> type[ShapleyNumbaGameProtocol]:
        @wraps(cls, updated=())
        class _NumbaGameClass(ShapleyNumbaGameProtocol):
            original_class = cls
            jitted_class = None

            @classmethod
            def _set_jitted_class(cls, jitted_game) -> None:
                cls.jitted_class = jitted_game

            def __init__(self, *args, **kwargs):
                if self.jitted_class is None:
                    try:
                        self._set_jitted_class(jitclass(gamespec)(cls))
                    except Exception as e:
                        logger.warning(
                            'failed to compile game with numba, due to error %s: %s',
                            e.__class__.__name__,
                            e,
                        )
                        logger.error(e)
                        self._set_jitted_class(e)
                self.game = cls(*args, **kwargs)
                if not isinstance(self.jitted_class, Exception):
                    try:
                        self.jitted_game = self.jitted_class(*args, **kwargs)
                    except Exception as e:
                        self.jitted_game = e
                else:
                    self.jitted_game = self.jitted_class

            def value(self, subset: CoalitionType) -> float64:
                """Return value of the game.

                Just a convenience method to hide actual class.
                """
                if not isinstance(self.jitted_game, Exception):
                    return float64(self.jitted_game.value(subset))
                return float64(self.game.value(subset))

        return _NumbaGameClass

    return decorator


def has_jitted_game(game: ShapleyNumbaGameProtocol) -> bool:
    """Check if the game has a jitted version."""
    if not hasattr(game, 'jitted_game'):
        return False
    return not isinstance(game.jitted_game, Exception)


def numba_game_func(numba_function):
    """Apply a jit compiled function onto a numba_game."""

    @wraps(numba_function)
    def _numba_func(game: ShapleyNumbaGameProtocol, *args, force_numba=False, **kwargs):
        if has_jitted_game(game):
            return numba_function(game.jitted_game, *args, **kwargs)
        if force_numba:
            if hasattr(game, 'jitted_game'):
                jitted = game.jitted_game
                if isinstance(jitted, Exception):
                    raise ValueError(
                        'Cannot force numba due to compilation error'
                    ) from jitted
                raise ValueError('Cannot force numba due to compilation error')
            raise ValueError(f'{game} is not numba_game, cannot force numba')
        if hasattr(game, 'game'):
            return numba_function.py_func(game.game, *args, **kwargs)
        if hasattr(game, 'value'):
            logger.warning('Trying to duck-type %s', game)
            return numba_function.py_func(game, *args, **kwargs)
        raise ValueError(f'{game} is not numba_game')

    return _numba_func
