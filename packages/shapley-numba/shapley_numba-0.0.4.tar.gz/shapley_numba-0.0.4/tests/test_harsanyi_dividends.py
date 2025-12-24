import pytest

from shapley_numba.common import subsets
from shapley_numba.examples.games import WikipediaExample
from shapley_numba.harsanyi import HarsanyiDividends
from shapley_numba.harsanyi_naive import harsanyi_dividends as harsanyi_dividends_naive


@pytest.mark.parametrize(
    'game, num_players', [(WikipediaExample(), 3)], ids=['wikipedia_example_3_players']
)
def test_harsanyi_dividends_vs_naive(game, num_players):
    hd = HarsanyiDividends(game, num_players)
    for subset in subsets(num_players):
        assert hd(subset) == pytest.approx(harsanyi_dividends_naive(game, subset))
