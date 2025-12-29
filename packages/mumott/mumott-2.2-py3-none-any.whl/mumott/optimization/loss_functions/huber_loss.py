import logging

import numpy as np
from numpy.typing import NDArray

from mumott.methods.residual_calculators.base_residual_calculator import ResidualCalculator
from .base_loss_function import LossFunction

logger = logging.getLogger(__name__)


class HuberLoss(LossFunction):

    r"""Class object for obtaining the Huber loss function and gradient from a given
    :ref:`residual_calculator <residual_calculators>`.

    This loss function is used for so-called
    `robust regression <https://en.wikipedia.org/wiki/Robust_regression>`_ and can be written as

    .. math::
        L(r(x, D)) = \begin{Bmatrix}
                        \vert r(x, D) \vert - 0.5 \delta & \quad \text{if } \vert r(x, D) \vert > \delta \\
                        \dfrac{r(x, D)^2}{2 \delta} & \quad \text{if } \vert r(x, D) \vert < \delta
                     \end{Bmatrix},

    where :math:`r` is the residual, a function of :math:`x`, the optimization coefficients,
    and :math:`D`, the data. The gradient with respect to :math:`x`
    is then :math:`\sigma(\frac{\partial r}{\partial x})` for large :math:`r`, where :math:`\sigma(x)`
    is the sign function, and :math:`\frac{\partial r}{\partial x}` for small :math:`r`. The partial
    derivative of :math:`r` with respect to :math:`x` is the responsibility of the
    :attr:`residual_calculator` to compute.

    Broadly speaking, the Huber loss function is less sensitive to outliers than the squared (or :math:`L_2`)
    loss function, while it is easier to minimize than the :math:`L_1` loss function
    since it its derivative is continuous in the entire domain.

    See also the Wikipedia articles on `robust regression <https://en.wikipedia.org/wiki/Robust_regression>`_
    and the `Huber loss <https://en.wikipedia.org/wiki/Huber_loss>`_.

    Parameters
    ----------
    residual_calculator : ResidualCalculator
        The :ref:`residual calculator instance <residual_calculators>` from which the
        residuals, weights, and gradient terms are obtained.
    use_weights : bool
        Whether to use weighting in the computation of the residual
        norm and gradient.  Default is ``False``.
    preconditioner : np.ndarray
        A preconditioner to be applied to the gradient. Must have the same shape as
        :attr:`residual_calculator.coefficients` or it must be possible to broadcast by multiplication.
    residual_norm_multiplier : float
        A multiplier that is applied to the residual norm and gradient. Useful in cases where
        a very small or large loss function value changes the optimizer behaviour.
    delta : float
        The cutoff value where the :math:`L_1` loss function is spliced with the :math:`L_2` loss function.
        The default value is ``1.``, but the appropriate value to use depends on the data
        and the chosen representation.

    """

    def __init__(self,
                 residual_calculator: ResidualCalculator,
                 use_weights: bool = False,
                 preconditioner: NDArray[float] = None,
                 residual_norm_multiplier: float = 1.,
                 delta: float = 1.):
        if delta < 0:
            raise ValueError('delta must be greater than or equal to zero, but a value'
                             f' of {delta} was specified!')
        super().__init__(residual_calculator, use_weights, preconditioner, residual_norm_multiplier)
        self._delta = float(delta)

    def _get_residual_norm_internal(self,
                                    get_gradient: bool = False,
                                    gradient_part: str = None
                                    ) -> dict[str, NDArray[float]]:
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
            get_gradient=False, get_weights=self._use_weights, gradient_part=gradient_part)
        residuals = residual_calculator_output['residuals']
        # where indicates small values, use l2 at these points
        where = abs(residuals) < self._delta
        residual_norm = 0.
        if self.use_weights:
            # weights (e.g. 1/variance) need to be applied since they depend on the loss function
            residual_norm += 0.5 * np.reciprocal(self._delta) * np.einsum(
                'i, i, i',
                residuals[where].ravel(),
                residuals[where].ravel(),
                residual_calculator_output['weights'][where].ravel(),
                optimize='greedy')
            residual_norm += np.dot(abs(residuals[~where]) - 0.5 * self._delta,
                                    residual_calculator_output['weights'][~where])
        else:
            residual_norm += 0.5 * np.reciprocal(self._delta) * np.dot(
                residuals[where].ravel(), residuals[where].ravel())
            residual_norm += np.sum(abs(residuals[~where]) - 0.5 * self._delta)

        if get_gradient:
            residuals[where] *= np.reciprocal(self._delta)
            residuals[~where] = np.sign(residuals[~where])
            if self.use_weights:
                residuals *= residual_calculator_output['weights']
            gradient = self._residual_calculator.get_gradient_from_residual_gradient(residuals)
        else:
            gradient = None

        if residual_norm < 1:
            logger.warning(f'The residual norm value ({residual_norm}) is < 1.'
                           ' Note that some optimizers change their convergence criteria for'
                           ' loss functions < 1!')

        return dict(residual_norm=residual_norm, gradient=gradient)

    @property
    def _function_as_str(self) -> str:
        """ Should return a string representation of the associated loss function. """
        return ('L(r[abs(r) >= delta]) =\n'
                '            lambda * (abs(r) - 0.5 * delta)\n'
                '            R(x[abs(r) < delta]) = lambda * (r ** 2) / (2 * delta)')

    @property
    def _function_as_tex(self) -> str:
        """ Should return a string representation of the associated loss function
        in MathJax-renderable TeX."""
        # we use html line breaks <br> since LaTeX line breaks appear unsupported.
        return (r'$L(x_i) = \lambda (\vert \vec{x} \vert - 0.5\delta)'
                r'\quad \text{ if } \vert x \vert < \delta$<br>'
                r'$L(x_i) = \lambda \dfrac{x^2}{2 \delta} \quad \text{ if } x \leq \delta$<br>'
                r'$R(\vec{x}) = \sum_i L(x_i)$')
