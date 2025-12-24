"""Game templates module.

Provides templates for even easier game authoring.
"""

import numba
import numpy as np

__all__ = ['ParameterChangeExplanation', 'parameter_change_explanation_spec']

parameter_change_explanation_spec = [
    ('old_parameters', numba.float64[:]),
    ('new_parameters', numba.float64[:]),
]


class ParameterChangeExplanation:
    """Parameter Change Explanation Template.

    The "game" template for computing attribution due to
    a change in a multi-parameter model.

    Provides an attribution to each parameter change.

    See BlackScholesCallGame for an example of implementation.
    """

    def __init__(self, old_parameters, new_parameters):
        """Initialize the ParameterChangeExplanation."""
        self.old_parameters = old_parameters
        self.new_parameters = new_parameters

    def model_evaluate(self, parameters):
        """Evaluate the model with the given parameters."""
        raise NotImplementedError

    def value(self, subset):
        """Compute the value of a given subset of players."""
        parameters = np.where(subset == 1, self.new_parameters, self.old_parameters)
        return self.model_evaluate(parameters)
