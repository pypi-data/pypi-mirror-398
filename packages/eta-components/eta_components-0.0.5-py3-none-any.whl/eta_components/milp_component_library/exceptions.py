class InvalidUnitError(KeyError):
    """Raised when a producer or generator is accessed that does not exist within that context."""


class InvalidParameterNameError(KeyError):
    """Raised when a parameter is supplied which is not specified within the model."""


class MissingParameterError(KeyError):
    """Raised when a parameter for constructing a model is missing."""


class InvalidParameterValueError(ValueError):
    """Raised when a parameter has an invalid value or shape."""


class InvalidPwlfValuesError(ValueError):
    """Raised when the values for the piecewise linearization are invalid."""


class InfeasibleProblemError(ValueError):
    """Raised when the optimization problem has no feasible solution."""


class UnboundedProblemError(ValueError):
    """Raised when the optimization problem is unbounded."""
