import numpy as np
from numpy.typing import NDArray

from mumott.optimization.regularizers.base_regularizer import Regularizer
import logging
logger = logging.getLogger(__name__)


class Laplacian(Regularizer):

    """Regularizes using the Laplacian of the coefficients. Suitable for orthonormal representations,
    e.g., spherical harmonics.
    """

    def __init__(self):
        super().__init__()

    def get_regularization_norm(self,
                                coefficients: NDArray[float],
                                get_gradient: bool = False,
                                gradient_part: str = None) -> dict[str, NDArray[float]]:
        """Retrieves the regularization norm and possibly the gradient based on the provided coefficients.
        The norm is the 2-norm of the discrete nearest-neighbour Laplacian.

        This is in effect a smoothing kernel that enforces continuity between the tensors of
        neighbouring voxels. The calculation is most suitable for orthonormal representations.
        If the representation is in spherical harmonics, the norm corresponds to maximimzing
        the covariance between neighbours.

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

        r = 6 * coefficients
        slices_r = [np.s_[1:, :, :], np.s_[:-1, :, :],
                    np.s_[:, 1:, :], np.s_[:, :-1, :],
                    np.s_[:, :, 1:], np.s_[:, :, :-1]]
        slices_coeffs = [np.s_[:-1, :, :], np.s_[1:, :, :],
                         np.s_[:, :-1, :], np.s_[:, 1:, :],
                         np.s_[:, :, :-1], np.s_[:, :, 1:]]

        for s, v in zip(slices_r, slices_coeffs):
            r[s] -= coefficients[v]

        r *= 0.5

        result = dict(regularization_norm=None, gradient=None)
        if gradient_part is None:
            result['regularization_norm'] = np.dot(r.ravel(), r.ravel())
        elif gradient_part in ('full', 'coefficients', 'angles'):
            r = r[..., :-2]
            result['regularization_norm'] = np.dot(r.ravel(), r.ravel())
        else:
            raise ValueError('Unexpected argument given for gradient part.')

        if get_gradient:
            if gradient_part is None:
                result['gradient'] = r
            elif gradient_part in ('full', 'coefficients'):
                result['gradient'] = np.zeros(coefficients.shape)
                result['gradient'][..., :-2] = r
            elif gradient_part in ('angles'):
                result['gradient'] = np.zeros(coefficients.shape)
            else:
                raise ValueError('Unexpected argument given for gradient part.')

        return result

    @property
    def _function_as_str(self) -> str:
        return 'R(x) = 0.5 * lambda * (2 * x[i] - x[i + 1] - x[i - 1]) ** 2'

    @property
    def _function_as_tex(self) -> str:
        return r'$R(\vec{x}) = \lambda \frac{\Vert \nabla^2 \vec{x} \Vert^2}{2}$'
