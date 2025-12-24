"""Games and computations related to finance."""

import math

import numba
import numpy as np

from shapley_numba import numba_game
from shapley_numba.game_templates import (
    ParameterChangeExplanation,
    parameter_change_explanation_spec,
)

__all__ = [
    'BlackScholesCallGame',
]


@numba.jit(nopython=True)
def norm_cdf(x: float | int) -> float:
    """Compute norm cdf.

    The cumulative distribution function of the standard normal distribution.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


@numba.jit(nopython=True)
def black_scholes_call_price(params: list[float], strike: float) -> float:  # noqa: D417
    """Calculate the Black-Scholes call option price from a parameter array.

    Parameters
    ----------
    params : numpy.ndarray
        A 1D array containing the Black-Scholes parameters in the following order:
        [S, T, r, sigma]
        S : float - Spot price of the underlying asset.
        T : float - Time to expiration (in years).
        r : float - Risk-free interest rate (annualized).
        sigma : float - Volatility of the underlying asset (annualized).
        strike : float - Strike price of the option.

    Returns
    -------
    float
        The Black-Scholes call option price.

    """
    S, T, r, sigma = params[0], params[1], params[2], params[3]  # noqa: N806
    K = strike  # noqa: N806
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    call = S * norm_cdf(d1) - K * np.exp(-r * T) * norm_cdf(d2)
    return float(call)


black_scholes_call_price_game_spec = [
    ('strike', numba.float64)
] + parameter_change_explanation_spec


@numba_game(black_scholes_call_price_game_spec)
class BlackScholesCallGame(ParameterChangeExplanation):
    """A game representing the Black-Scholes call option price."""

    def __init__(self, old_parameters, new_parameters, strike: float):
        """Initialize the BlackScholesCallGame."""
        self.strike = strike
        # Unfortunately super doesn't work in jitclasses
        # super().__init__(old_parameters, new_parameters)
        self.old_parameters = old_parameters
        self.new_parameters = new_parameters

    def model_evaluate(self, params: list[float]) -> float:
        """Evaluate the Black-Scholes call option price with the given parameters."""
        return float(black_scholes_call_price(params, self.strike))


@numba.jit(nopython=True)
def black_scholes_put_price(params: list[float]):
    """Calculate the Black-Scholes put option price from a parameter array.

    Parameters
    ----------
    params : numpy.ndarray
        A 1D array containing the Black-Scholes parameters in the following order:
        [S, K, T, r, sigma]
        S : float - Spot price of the underlying asset.
        K : float - Strike price of the option.
        T : float - Time to expiration (in years).
        r : float - Risk-free interest rate (annualized).
        sigma : float - Volatility of the underlying asset (annualized).

    Returns
    -------
    float
        The Black-Scholes put option price.

    """
    S, K, T, r, sigma = params[0], params[1], params[2], params[3], params[4]  # noqa: N806
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    put = K * np.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
    return put
