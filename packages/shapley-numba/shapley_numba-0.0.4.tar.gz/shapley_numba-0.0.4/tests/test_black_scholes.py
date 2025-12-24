import numpy as np
import pytest

from shapley_numba.examples.finance import (
    BlackScholesCallGame,
    black_scholes_call_price,
)
from shapley_numba.shapley import shapley


def test_example_black_scholes_call_price():
    assert black_scholes_call_price(
        (np.array([100, 1, 0.05, 0.2])), 100
    ) == pytest.approx(10.450583572185565)
    assert black_scholes_call_price(
        np.array([100, 0.25, 0.05, 0.2]), 110
    ) == pytest.approx(1.1911316636130707)
    assert black_scholes_call_price(
        np.array([105, 0.75, 0.055, 0.25]), 110
    ) == pytest.approx(8.800724823107544)


def test_black_scholes_game():
    old_parameters = np.array([100, 1, 0.05, 0.2])
    new_parameters = np.array([105, 0.75, 0.055, 0.25])
    strike = 110
    game = BlackScholesCallGame(old_parameters, new_parameters, strike)
    result = shapley(game, 4)
    assert result == pytest.approx([2.46650459, -1.78811388, 0.18826859, 1.89397739])
