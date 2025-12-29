import logging
from typing import Dict

import numpy as np
from numpy.typing import NDArray

from mumott.methods.residual_calculators.base_residual_calculator import ResidualCalculator
from .base_loss_function import LossFunction

logger = logging.getLogger(__name__)


class SquaredLoss(LossFunction):

    r"""Class object for obtaining the squared loss function and
    gradient from a given :ref:`residual_calculator <residual_calculators>`.

    This loss function can be written as :math:`L(r(x, d)) = 0.5 r(x, d)^2`, where :math:`r` is the
    residual, a function of :math:`x`, the optimization coefficients, and :math:`d`, the data.
    The gradient with respect to :math:`x` is then :math:`\frac{\partial r}{\partial x}`.
    The partial derivative of :math:`r` with respect to :math:`x` is the responsibility
    of the :attr:`residual_calculator` to compute.

    Generally speaking, the squared loss function is easy to compute and has a well-behaved
    gradient, but it is not robust against outliers in the data. Using weights to normalize
    residuals by the variance can mitigate this somewhat.

    Parameters
    ----------
    residual_calculator : ResidualCalculator
        The :ref:`residual calculator instance <residual_calculators>` from which the
        residuals, weights, and gradient terms are obtained.
    use_weights : bool
        Whether to use weighting in the computation of the residual norm and gradient.
        Default is ``False``.
    preconditioner : np.ndarray
        A preconditioner to be applied to the gradient. Must have the same shape as
        :attr:`residual_calculator.coefficients` or it must be possible to broadcast by multiplication.
    residual_norm_multiplier : float
        A multiplier that is applied to the residual norm and gradient. Useful in cases where
        a very small or large loss function value changes the optimizer behaviour.
    """

    def __init__(self,
                 residual_calculator: ResidualCalculator,
                 use_weights: bool = False,
                 preconditioner: NDArray[float] = None,
                 residual_norm_multiplier: float = 1):
        super().__init__(residual_calculator, use_weights, preconditioner, residual_norm_multiplier)

    def _get_residual_norm_internal(self, get_gradient: bool = False, gradient_part: str = None) -> Dict:
        """ Gets the residual norm, and if needed,
        the gradient, using the attached :attr:`residual_calculator`.

        Parameters
        ----------
        get_gradient
            Whether to return the gradient. Default is ``False``.
        gradient_part
            Used for the zonal harmonics resonstructions to determine what part of the gradient is
            being calculated. Default is None.

        Returns
        -------
             A ``dict`` with two entries, ``residual_norm`` and ``gradient``.
             If ``get_gradient`` is false, its value will be ``None``.
        """
        residual_calculator_output = self._residual_calculator.get_residuals(
            get_gradient=get_gradient, get_weights=self._use_weights, gradient_part=gradient_part)
        residuals = residual_calculator_output['residuals']
        if self.use_weights:
            # weights (1/variance) need to be applied since they depend on the loss function
            residual_norm = 0.5 * np.einsum(
                'ijkh, ijkh, ijkh -> ...', residuals, residuals, residual_calculator_output['weights'])
        else:
            residual_norm = 0.5 * np.einsum(
                'ijkh, ijkh -> ...', residuals, residuals)

        if residual_norm < 1:
            logger.warning(f'The residual norm value ({residual_norm}) is < 1.'
                           ' Note that some optimizers change their convergence criteria for'
                           ' loss functions < 1!')

        return dict(residual_norm=residual_norm, gradient=residual_calculator_output['gradient'])

    def get_estimate_of_lifschitz_constant(self) -> float:
        """
        Calculate an estimate of the Lifschitz constant of this cost function. Used to determine a
        safe step-size for certain optimization algorithms.

        Returns
        -------
        lifschitz_constant
            Lifschitz constant.
        """
        matrix_norm = self._residual_calculator.get_estimate_of_matrix_norm()
        return 2 / matrix_norm

    @property
    def _function_as_str(self) -> str:
        """ Should return a string representation of the associated loss function. """
        return 'L(r) = r ** 2'

    @property
    def _function_as_tex(self) -> str:
        """ Should return a string representation of the associated loss function
        in MathJax-renderable TeX."""
        return r'$L(r) = r^2$'
