import pytest
from scipy.special import comb

from shapley_numba.shapley import compute_coeffs


def inv_coeff(num_players: int, set_size: int) -> float:
    """Compute coefficients of a subset for shapley value."""
    return float(1 / comb(num_players - 1, set_size))


def compute_coeffs_legacy(num_players: int) -> list[float]:
    """Compute coefficients of all subsets for shapley value."""
    coeffs = [inv_coeff(num_players, set_size) for set_size in range(num_players)]
    coeffs.append(0)
    return coeffs


@pytest.mark.parametrize('num_players', range(1, 10))
def test_coeffs(num_players):
    result = compute_coeffs(num_players)
    legacy_result = compute_coeffs_legacy(num_players)
    assert result == pytest.approx(legacy_result) 


@pytest.mark.requires_jit
@pytest.mark.parametrize('num_players', range(10, 100))
def test_coeffs_jit(num_players):
    result = compute_coeffs(num_players)
    legacy_result = compute_coeffs_legacy(num_players)
    assert result == pytest.approx(legacy_result) 