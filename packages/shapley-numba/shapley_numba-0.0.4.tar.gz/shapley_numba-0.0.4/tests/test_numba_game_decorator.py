import numba
import numpy as np
import pytest

from shapley_numba.core import numba_game
from shapley_numba.shapley import shapley

glove_spec = [('num_left_gloves', numba.int_)]


@numba_game(glove_spec)
class GloveGame:
    def __init__(self, num_left_gloves):
        self.num_left_gloves = num_left_gloves

    def value(self, subset):
        left_gloves = np.sum(subset[: self.num_left_gloves])
        right_gloves = np.sum(subset[self.num_left_gloves :])
        return min(left_gloves, right_gloves)


def test_cls():
    assert hasattr(GloveGame, 'original_class')
    assert GloveGame.original_class is not None
    assert GloveGame.original_class is GloveGame.__wrapped__
    assert hasattr(GloveGame, 'jitted_class')
    assert GloveGame.jitted_class is None
    _ = GloveGame(2)
    assert GloveGame.jitted_class is not None
    assert not isinstance(GloveGame.jitted_class, Exception)


def test_glove():
    game = GloveGame(2)
    assert game.value(np.array([1, 0, 1, 0])) == 1

@pytest.mark.requires_jit
def test_shapley():
    game = GloveGame(1)
    expected = [2 / 3, 1 / 6, 1 / 6]
    assert shapley(game, 3) == pytest.approx(expected)
    assert shapley(game, 3, use_numba=False) == pytest.approx(expected)
