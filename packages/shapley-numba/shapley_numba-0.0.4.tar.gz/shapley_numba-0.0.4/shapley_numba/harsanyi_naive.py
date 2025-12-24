"""Compute Harsanyi dividends via the naive formula."""

from typing import cast

import numba
import numpy as np

from shapley_numba.common import subsets_of_subset
from shapley_numba.core import has_jitted_game
from shapley_numba.typing import CoalitionType, ShapleyNumbaGameProtocol

__all__ = ['harsanyi_dividends']


def harsanyi_dividends(
    game: ShapleyNumbaGameProtocol, subset: CoalitionType, use_numba: bool = True
) -> np.float64:
    """Compute the naive version of Harsanyi dividends."""
    if use_numba:
        if has_jitted_game(game):
            return cast(np.float64, _harsanyi_dividends(game.jitted_game, subset))
        raise ValueError('This implementation works only for jit-compiled games')
    return cast(np.float64, _harsanyi_dividends.py_func(game.game, subset))


@numba.jit(nopython=True)
def _harsanyi_dividends(
    game: ShapleyNumbaGameProtocol, subset: CoalitionType
) -> np.float64:
    r"""Compute the naive version of Harsanyi dividends.

    d(A)  = \sum_{B\subset A} (-1)^{|A|-|B|} v(B)
    """
    subset = subset.astype(np.int32)
    result = game.value(subset)
    order_subset = sum(subset)
    for subsubset in subsets_of_subset(subset, self_included=False):
        result += (-1) ** (order_subset - np.sum(subsubset)) * game.value(subsubset)
    return np.float64(result)
