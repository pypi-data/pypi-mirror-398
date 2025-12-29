import logging
import numpy as np
from mumott.optimization.regularizers.base_regularizer import Regularizer
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class GroupLasso(Regularizer):
    r"""Group lasso regularizer, where the coefficients are grouped by voxel.
    This approach is well suited for handling voxels with zero scattering and for suppressing missing wedge
    artifacts. Note that this type of regularization (:math:`L_1`) has convergence issues when using
    gradient-based optimizers due to the divergence of the derivative of the :math:`L_1`-norm at zero.
    This is why one commonly uses proximal operators for optimization.

    .. math::
        L(\mathrm{c}) = \sum_{xyz} \sqrt(\sum_{i}c_{xyzi}^2)

    Parameters
    ----------
    regularization_parameter : float
        Regularization weight used to define the proximal operator. Can be left as ``1`` (default)
        for the normal mumott workflow.

    step_size_parameter : float
        Step-size parameter used to define the proximal operator.
    """

    def __init__(self, regularization_parameter: float = 1, step_size_parameter: float = None):
        self._regularization_parameter = regularization_parameter
        self._step_size_parameter = step_size_parameter

    def get_regularization_norm(self, coefficients: NDArray[float], get_gradient: bool = False,
                                gradient_part: str = None) -> float:
        """Retrieves the group lasso regularization weight of the coefficients.

        Parameters
        ----------
        coefficients
            An ``np.ndarray`` of values, with shape ``(X, Y, Z, W)``, where
            the last channel contains, e.g., tensor components.
        get_gradient
            If ``True``, returns a ``'gradient'`` of the same shape as :attr:`coefficients`.
            Otherwise, the entry ``'gradient'`` will be ``None``. Defaults to ``False``.
        gradient_part
            Used for reconstructions with zonal harmonics (ZHs) to determine what part of the gradient
            is being calculated. Default is ``None``. If one of the flag in (``'full'``, ``'angles'``,
            ``'coefficients'``) is passed, we assume that the ZH workflow is used and that the last two
            coefficients are Euler angles, which should not be regularized by this regularizer.

        Returns
        -------
            A dictionary with two entries, ``regularization_norm`` and ``gradient``.
        """

        if gradient_part is None:
            grouped_norms = np.sqrt(np.sum(coefficients**2, axis=-1))
        elif gradient_part in ('full', 'coefficients', 'angles'):
            grouped_norms = np.sqrt(np.sum(coefficients[..., :-2]**2, axis=-1))

        result = {'regularization_norm': np.sum(grouped_norms) * self._regularization_parameter}

        if get_gradient:

            if gradient_part == 'angles':
                gradient = np.zeros(coefficients.shape)
            else:
                gradient = np.divide(coefficients,
                                     grouped_norms[..., np.newaxis],
                                     out=np.ones(coefficients.shape),
                                     where=grouped_norms[..., np.newaxis] != 0)
            if gradient_part in ('full', 'coefficients'):
                gradient[..., -2:] = 0

            result['gradient'] = gradient*self._regularization_parameter

        return result

    def proximal_operator(self, coefficients: NDArray[float]) -> NDArray[float]:
        """Proximal operator of the group lasso regularizer.

        Parameters
        ----------
        coefficients
            An ``np.ndarray`` of values, with shape ``(X, Y, Z, W)``, where
            the last channel contains, e.g., tensor components.

        Returns
        -------
        stepped_coefficient
            Input coefficients vector after the application of the proximal operator.
        """

        if self._step_size_parameter is None:
            logger.error('Proximal operator is not defined without a stepsize parameter.')
            return None

        grouped_norms = np.sqrt(np.sum(coefficients**2, axis=-1))
        stepped_coefficient = coefficients - self._regularization_parameter \
            * self._step_size_parameter * coefficients / grouped_norms[..., np.newaxis]
        mask = grouped_norms <= self._regularization_parameter * self._step_size_parameter
        stepped_coefficient[mask, :] = 0
        return stepped_coefficient

    @property
    def _function_as_str(self) -> str:
        return ('R(c) = lambda * sum_xyz( sqrt( sum_lm( c_lm(xyz)^2 ) ) )')

    @property
    def _function_as_tex(self) -> str:
        return (r'$R(\vec{c}) = \lambda \sum_{xyz} \sqrt{ \sum_{\ell, m}c_{\ell, m}(x,y,z)^2 }_2')
