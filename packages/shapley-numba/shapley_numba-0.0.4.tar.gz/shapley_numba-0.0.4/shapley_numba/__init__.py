"""Shapley Numba.

Compute values of cooperative games in python more efficiently,
using numba. Shapley-numba aims to provide tools to author
cooperative games and compute various functions connected to them
more efficiently.

Package structure
------------------

core.py - contains the main decorator `numba_game`.
shapley.py - contains implementations of computing or approximating Shapley values.
harsanyi.py - contains implementation of Harsanyi dividends (also known as synergies).
tools.py - contains tools for working with games.
game_templates.py - contains templates for creating new games.
typing.py - contains type definitions and protocols for type checking.
"""

from shapley_numba.core import numba_game
from shapley_numba.typing import (
    CoalitionType,
    GameProtocol,
    GameSpecType,
    ShapleyNumbaGameProtocol,
)

from . import common, examples, game_templates, harsanyi, harsanyi_naive, shapley

__all__ = [
    'numba_game',
    'CoalitionType',
    'GameProtocol',
    'GameSpecType',
    'ShapleyNumbaGameProtocol',
    'common',
    'examples',
    'game_templates',
    'harsanyi',
    'harsanyi_naive',
    'shapley',
]
