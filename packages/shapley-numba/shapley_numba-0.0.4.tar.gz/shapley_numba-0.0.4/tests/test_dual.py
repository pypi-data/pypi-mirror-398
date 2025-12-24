import numpy as np
import pytest

from shapley_numba.common import subsets
from shapley_numba.examples import WikipediaExample
from shapley_numba.examples.games import GloveGame
from shapley_numba.harsanyi_naive import harsanyi_dividends
from shapley_numba.shapley import shapley
from shapley_numba.tools import dual_game


@pytest.mark.requires_jit
def test_dual_compiles():
    game = WikipediaExample()
    dual_wiki = dual_game(game, 3)
    result = shapley(dual_wiki, 3)
    assert result == pytest.approx([120, 80, 80])

@pytest.mark.requires_jit
def test_dual_glove():
    num_players = 3
    game = GloveGame(1)
    dual_glove = dual_game(game, num_players)
    assert dual_glove.value(np.array([1, 0, 0])) == pytest.approx(1)
    assert dual_glove.value(np.array([0, 1, 0])) == pytest.approx(0)
    result = shapley(dual_glove, num_players)
    assert result == pytest.approx([2 / 3, 1 / 6, 1 / 6])


@pytest.mark.skip(reason='work in progress')
def test_dual_harsanyi_naive():
    game = WikipediaExample()
    dual_wiki = dual_game(game, WikipediaExample, 3)
    for subset in subsets(3):
        peel_off_hd = harsanyi_dividends(dual_wiki, np.array(subset))
        pile_up_hd = harsanyi_dividends(game, 1 - np.array(subset))
        assert peel_off_hd == pytest.approx(pile_up_hd)
