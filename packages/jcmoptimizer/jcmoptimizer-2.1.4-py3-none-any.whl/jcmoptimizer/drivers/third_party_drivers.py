from .driver import Minimizer, LeastSquaresDriver


class DifferentialEvolution(Minimizer):
    """
    This class provides methods for retieving information of the
    result of the differential evolution.
    """

    pass


class CMAES(Minimizer):
    """
    This class provides methods for retieving information of the
    result of the CMA-ES minimization.
    """

    pass


class ScipyMinimizer(Minimizer):
    """
    This class provides methods for retieving information of the
    result of the minimization using ``scipy.optimize.minimize``.
    """

    pass


class ScipyLeastSquares(LeastSquaresDriver):
    """
    This class provides methods for retieving information of the
    result of the least squares minimization using ``scipy.optimize.least_squares``.
    """

    pass
