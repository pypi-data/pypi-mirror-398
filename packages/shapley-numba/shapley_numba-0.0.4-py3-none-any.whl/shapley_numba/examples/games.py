"""Examples of jit-compiled games in shapley-numba."""

import numba
import numpy as np

from shapley_numba import numba_game
from shapley_numba.typing import CoalitionType

__all__ = [
    'GloveGame',
    'CoalitionGame',
    'WikipediaExample',
]

glove_spec = [('num_left_gloves', numba.int_)]


@numba_game(glove_spec)
class GloveGame(object):
    """A game representing the value of glove market.

    The value of a coalition is the minimum of the number of left gloves
    and right gloves it possesses.

    Attributes
    ----------
    num_left_gloves : int
        The number of left gloves available in the game.

    """

    def __init__(self, num_left_gloves: int):
        """Initialize the GloveGame.

        Parameters
        ----------
        num_left_gloves : int
            The number of left gloves.

        """
        self.num_left_gloves = num_left_gloves

    def value(self, subset):
        """Compute the value of a given subset of players.

        Parameters
        ----------
        subset : numpy.ndarray
            A binary array where 1 indicates the presence of a player
            in the subset and 0 indicates absence. The length of the
            array should be `2 * num_left_gloves`.

        Returns
        -------
        int
            The value of the subset, which is `min(left_gloves, right_gloves)`.

        """
        left_gloves = np.sum(subset[: self.num_left_gloves])
        right_gloves = np.sum(subset[self.num_left_gloves :])
        return min(left_gloves, right_gloves)


coalition_spec = [('seats', numba.float64[:]), ('quorum', numba.float64)]


@numba_game(coalition_spec)
class CoalitionGame:
    """A game representing a political coalition.

    Game is "won" if a colation achieves majority
    """

    def __init__(self, seats):
        """Initialize the CoalitionGame.

        Parameters
        ----------
        seats : numpy.ndarray
            An array of floats representing the number of seats each player holds.

        """
        self.seats = seats
        self.quorum = np.sum(self.seats) / 2

    def value(self, subset):
        """Compute the value of a given subset of players."""
        return 1 if np.sum(subset * self.seats) > self.quorum else 0


wikipedia_example_spec = [('game', numba.types.DictType(numba.int32, numba.float64))]


@numba_game(wikipedia_example_spec)
class WikipediaExample:
    """Game taken from shapley value wikipedia page.

    Players are represented by their index:
    0 - "you"
    1 - "Emma"
    2 - Liam
    """

    def __init__(self) -> None:
        """Initialize the WikipediaExample."""
        game = {
            0: 0.0,  # empty
            1: 30.0,  # you
            2: 20.0,  # Emma
            4: 10.0,  # Liam
            3: 90.0,  # you + Emma
            5: 100.0,  # you + Liam
            6: 30.0,  # Emma + Liam
            7: 280.0,  # you + Emma + Liam
        }

        self.game = numba.typed.Dict.empty(numba.types.int32,
                                     numba.types.float64)
        for key, value in game.items():
            self.game[np.int32(key)] = value


    def value(self, subset: CoalitionType) -> np.float64:
        """Compute the value of a given subset of players."""
        return np.float64(self.game[np.sum(subset * (2 ** np.arange(3)))])
