import numpy as np
from numpy.typing import NDArray

from mumott.optimization.regularizers.base_regularizer import Regularizer
import logging
logger = logging.getLogger(__name__)


class HuberNorm(Regularizer):

    r"""Regularizes using the Huber norm of the coefficient, which splices the :math`L_1`
    and :math:`L_2` norms.
    Suitable for scalar fields or tensor fields in local representations.
    Tends to reduce noise while converging more easily than the :math:`L_1` loss function.

    The Huber norm of a vector :math:`x` is given by :math:`R(\vec{x}) = \sum_i L(x_i)`,
    where :math:`L(x_i)` is given by

    .. math::
        L(x_i) = \begin{Bmatrix}\vert x_i \vert - 0.5 \delta & \quad \text{if } \vert x_i \vert > \delta \\
                 \dfrac{x^2}{2 \delta} & \quad \text{if } \vert x_i \vert \leq \delta\end{Bmatrix}

    See also `the Wikipedia article on the Huber loss <https://en.wikipedia.org/wiki/Huber_loss>`_.

    Parameters
    ----------
    delta : float
        The threshold value for the Huber norm. Must be greater than ``0``. Default value
        is ``1.``, but the appropriate value is data-dependent.
    """

    def __init__(self, delta: float = 1.):
        if delta <= 0:
            raise ValueError('delta must be greater than zero, but a value'
                             f' of {delta} was specified! For pure L1 regularization, use L1Norm.')
        super().__init__()
        self._delta = float(delta)

    def get_regularization_norm(self,
                                coefficients: NDArray[float],
                                get_gradient: bool = False,
                                gradient_part: str = None) -> dict[str, NDArray[float]]:
        """Retrieves the Huber loss of the coefficients. Appropriate for
        use with scalar fields or tensor fields in local representations.

        Parameters
        ----------
        coefficients
            An ``np.ndarray`` of values, with shape ``(X, Y, Z, W)``, where
            the last channel contains, e.g., tensor components.
        get_gradient
            If ``True``, returns a ``'gradient'`` of the same shape as :attr:`coefficients`.
            Otherwise, the entry ``'gradient'`` will be ``None``. Defaults to ``False``.
        gradient_part
            Used for the zonal harmonics resonstructions to determine what part of the gradient is
            being calculated. Default is None. If a flag is passed in ('full', 'angles', 'coefficients'),
            we assume that the ZH workflow is used and that the last two coefficients are euler angles,
            which should not be regularized by this regularizer.

        Returns
        -------
            A dictionary with two entries, ``regularization_norm`` and ``gradient``.
        """

        r = abs(coefficients)

        where = r < self._delta

        # where indicates small values, use l2 at these points
        r[where] *= r[where] * np.reciprocal(2 * self._delta)
        r[~where] -= 0.5 * self._delta

        result = dict(regularization_norm=None, gradient=None)

        if get_gradient:
            if gradient_part is None:
                gradient = coefficients * np.reciprocal(self._delta)
                gradient[~where] = np.sign(gradient[~where])
                result['gradient'] = gradient
            elif gradient_part in ('full', 'coefficients'):
                gradient = coefficients * np.reciprocal(self._delta)
                gradient[~where] = np.sign(gradient[~where])
                result['gradient'] = gradient
                result['gradient'][..., -2:] = 0
            elif gradient_part in ('angles'):
                result['gradient'] = np.zeros(coefficients.shape)
            else:
                logger.warning('Unexpected argument given for gradient part.')
                raise ValueError

        if gradient_part is None:
            result['regularization_norm'] = np.sum(r)
        elif gradient_part in ('full', 'coefficients', 'angles'):
            result['regularization_norm'] = np.sum(r[..., :-2] ** 2)
        else:
            logger.warning('Unexpected argument given for gradient part.')
            raise ValueError

        return result

    @property
    def _function_as_str(self) -> str:
        return ('R(x[abs(x) >= delta]) =\n'
                '        lambda * (abs(x) - 0.5 * delta)\n'
                '        R(x[abs(x) < delta]) = lambda * (x ** 2) / (2 * delta)')

    @property
    def _function_as_tex(self) -> str:
        # we use html line breaks <br> since LaTeX line breaks appear unsupported.
        return (r'$L(x_i) = \lambda (\vert \vec{x} \vert - 0.5\delta)'
                r'\quad \text{if } \vert x \vert \geq \delta$<br>'
                r'$L(x_i) = \lambda \dfrac{x^2}{2 \delta} \quad \text{ if } x < \delta$<br>'
                r'$R(\vec{x}) = \sum_i L(x_i)$')
