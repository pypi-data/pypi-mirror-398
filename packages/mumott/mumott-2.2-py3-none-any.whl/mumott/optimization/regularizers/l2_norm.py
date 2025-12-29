import numpy as np
from numpy.typing import NDArray

from mumott.optimization.regularizers.base_regularizer import Regularizer
import logging
logger = logging.getLogger(__name__)


class L2Norm(Regularizer):

    r"""Regularizes using the :math:`L_2` norm of the coefficient vector, also known as the Euclidean norm.
    Suitable for most representations, including non-local ones. Tends to reduce large values,
    and often leads to fast convergence.

    The :math:`L_2` norm of a vector :math:`x` is given by :math:`\sum{\vert x \vert^2}`.

    See also `the Wikipedia article on the Euclidean norm
    <https://en.wikipedia.org/wiki/Euclidean_space#Euclidean_norm>`_
    """

    def __init__(self):
        super().__init__()

    def get_regularization_norm(self,
                                coefficients: NDArray[float],
                                get_gradient: bool = False,
                                gradient_part: str = None) -> dict[str, NDArray[float]]:
        """Retrieves the :math:`L_2` norm, of the coefficient vector. Appropriate for
        use with scalar coefficients or local basis sets.

        Parameters
        ----------
        coefficients
            An ``np.ndarray`` of values, with shape ``(X, Y, Z, W)``, where
            the last channel contains, e.g., tensor components.
        get_gradient
            If ``True``, returns a ``'gradient'`` of the same shape as :attr:`coefficients`.
            Otherwise, the entry ``'gradient'`` will be ``None``. Defaults to ``False``.
        gradient_part
            Used for the zonal harmonics (ZH) reconstructions to determine what part of the gradient is
            being calculated. Default is ``None``.
            If a flag is passed in (``'full'``, ``'angles'``, ``'coefficients'``),
            we assume that the ZH workflow is used and that the last two coefficients are Euler angles,
            which should not be regularized by this regularizer.

        Returns
        -------
            A dictionary with two entries, ``regularization_norm`` and ``gradient``.
        """

        result = dict(regularization_norm=None, gradient=None)
        if get_gradient:

            if gradient_part is None:
                result['gradient'] = coefficients
            elif gradient_part in ('full', 'coefficients'):
                result['gradient'] = np.copy(coefficients)
                result['gradient'][..., -2:] = 0
            elif gradient_part in ('angles'):
                result['gradient'] = np.zeros(coefficients.shape)
            else:
                logger.warning('Unexpected argument given for gradient part.')
                raise ValueError

        if gradient_part is None:
            result['regularization_norm'] = np.sum(coefficients ** 2)
        elif gradient_part in ('full', 'coefficients', 'angles'):
            result['regularization_norm'] = np.sum(coefficients[..., :-2] ** 2)
        else:
            raise ValueError('Unexpected argument given for gradient part.')

        return result

    @property
    def _function_as_str(self) -> str:
        return 'R(x) = lambda * abs(x) ** 2'

    @property
    def _function_as_tex(self) -> str:
        return r'$R(\vec{x}) = \lambda \Vert \vec{x} \Vert_2^2$'
