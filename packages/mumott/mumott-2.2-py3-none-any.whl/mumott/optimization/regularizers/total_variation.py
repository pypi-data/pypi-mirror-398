import numpy as np
from numpy.typing import NDArray

from mumott.optimization.regularizers.base_regularizer import Regularizer
import logging
logger = logging.getLogger(__name__)


class TotalVariation(Regularizer):

    r"""Regularizes using the symmetric total variation, i.e., the root-mean-square difference
    between nearest neighbours. It is combined with a `Huber norm
    <https://en.wikipedia.org/wiki/Huber_loss>`_, using the squared differences at small values,
    in order to improve convergence. Suitable for scalar fields or tensor fields in local
    representations. Tends to reduce noise.

    In two dimensions, the total variation spliced with its squared function like a
    Huber loss can be written

    .. math::
          \mathrm{TV}_1(f(x, y))
          = \frac{1}{h}\sum_i ((f(x_i, y_i) - f(x_i + h, y_i))^2 +
          (f(x_i, y_i) - f(x_i - h, y_i))^2 + \\ (f(x_i, y_i) - f(x_i, y_i + h))^2 +
          (f(x_i, y_i) - f(x_i, y_i - h))^2))^{\frac{1}{2}} - 0.5 \delta

    If :math:`\mathrm{TV}_1 < 0.5 \delta` we instead use

    .. math::
          \mathrm{TV}_2(f(x, y))
          = \frac{1}{2 \delta h^2}\sum_i (f(x_i, y_i) - f(x_i + h, y_i))^2 +
          (f(x_i, y_i) - f(x_i - h, y_i))^2 + \\
          (f(x_i, y_i) - f(x_i, y_i + h))^2 + (f(x_i, y_i) - f(x_i, y_i - h))^2

    See also the Wikipedia articles on
    `total variation denoising <https://en.m.wikipedia.org/wiki/Total_variation_denoising>`_
    and `Huber loss <https://en.wikipedia.org/wiki/Huber_loss>`_

    Parameters
    ----------
    delta : float
        Below this value, the scaled square of the total variation is used as the norm.
        This makes the norm differentiable everywhere, and can improve convergence.
        If :attr`delta` is ``None``, the standard total variation will be used everywhere,
        and the gradient will be ``0`` at the singular point where the norm is ``0``.
    """

    def __init__(self, delta: float = 1e-2):
        if delta is not None:
            if delta <= 0:
                raise ValueError('delta must be greater than or equal to zero, but a value'
                                 f' of {delta} was specified! To use the total variation without'
                                 ' Huber splicing, explicitly specify delta=None.')
            self._delta = float(delta)
        else:
            self._delta = delta
        super().__init__()

    def get_regularization_norm(self,
                                coefficients: NDArray[float],
                                get_gradient: bool = False,
                                gradient_part: str = None) -> dict[str, NDArray[float]]:
        """Retrieves the isotropic total variation, i.e., the symmetric root-mean-square difference
        between nearest neighbours.

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

        num = 6 * coefficients
        denom = np.zeros_like(coefficients)
        slices_r = [np.s_[1:, :, :], np.s_[:-1, :, :],
                    np.s_[:, 1:, :], np.s_[:, :-1, :],
                    np.s_[:, :, 1:], np.s_[:, :, :-1]]
        slices_coeffs = [np.s_[:-1, :, :], np.s_[1:, :, :],
                         np.s_[:, :-1, :], np.s_[:, 1:, :],
                         np.s_[:, :, :-1], np.s_[:, :, 1:]]

        for s, v in zip(slices_r, slices_coeffs):
            num[s] -= coefficients[v]
            denom[s] += (coefficients[s] - coefficients[v]) ** 2

        result = dict(regularization_norm=None, gradient=None)
        norm = np.sqrt(denom)
        gradient = np.zeros_like(coefficients)

        if self._delta is None:
            where = norm == 0
        else:
            where = norm < self._delta

            gradient[where] = num[where] * np.reciprocal(self._delta)

            norm[where] = np.reciprocal(self._delta) * 0.5 * norm[where] ** 2
            norm[~where] -= 0.5 * self._delta

        gradient[~where] = num[~where] / np.sqrt(denom[~where])

        if get_gradient:
            if gradient_part is None:
                result['gradient'] = gradient
            elif gradient_part in ('full', 'coefficients'):
                result['gradient'] = gradient
                result['gradient'][..., -2:] = 0
            elif gradient_part in ('angles'):
                result['gradient'] = np.zeros_like(coefficients)
            else:
                raise ValueError('Unexpected argument given for gradient part.')

        if gradient_part is None:
            result['regularization_norm'] = np.sum(norm)
        elif gradient_part in ('full', 'coefficients', 'angles'):
            result['regularization_norm'] = np.sum(norm[..., :-2])
        else:
            raise ValueError('Unexpected argument given for gradient part.')

        return result

    @property
    def _function_as_str(self) -> str:
        return ('R(x) = lambda * sqrt('
                '\n        (x[i, j] - x[i + 1, j]) ** 2 + (x[i, j] - x[i - 1, j]) ** 2 +'
                '\n        (x[i, j] - x[i, j + 1]) ** 2 + (x[i, j] - x[i, j - 1]) ** 2)')

    @property
    def _function_as_tex(self) -> str:
        # we use html line breaks <br> since LaTeX line breaks appear unsupported.
        return (r'$R(\vec{x}) = \sum_{ij} L(x_{ij})$ <br>'
                r'$L(x_{ij}) = \begin{Bmatrix}L_1(x_{ij})'
                r'\text{\quad if } L_1(x_{ij}) > 0.5 \delta \\ L_2(x_{ij})'
                r'\text{\quad otherwise}\end{Bmatrix}$<br>'
                r'$L_1(x_{ij}) = \lambda ((x_{ij} - x_{(i+1)j})^2 +$<br>'
                r'$(x_{ij} - x_{i(j+1)})^2 + (x_{ij} - x_{(i-1)j})^2 +$<br>'
                r'$(x_{ij} - x_{i(j-1)})^2 )^\frac{1}{2} - 0.5 \delta$<br>'
                r'$L_2(x_{ij}) = \dfrac{\lambda}{2 \delta} ((x_{ij} - x_{(i+1)j})^2 +$<br>'
                r'$(x_{ij} - x_{i(j+1)})^2 + (x_{ij} - x_{(i-1)j})^2 +$<br>'
                r'$(x_{ij} - x_{i(j-1)})^2 )$<br>')
