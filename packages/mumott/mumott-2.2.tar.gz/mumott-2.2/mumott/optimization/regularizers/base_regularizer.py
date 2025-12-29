from abc import ABC, abstractmethod

import numpy as np
from numpy.typing import NDArray

from mumott.core.hashing import list_to_hash


class Regularizer(ABC):

    """This is the base class from which specific regularizers are derived.
    """

    def __init__(self):
        pass

    @abstractmethod
    def get_regularization_norm(self,
                                coefficients: NDArray[float] = None,
                                get_gradient: bool = False,
                                gradient_part: str = None) -> dict[str, NDArray[float]]:
        """Returns regularization norm and possibly gradient based on the provided coefficients.

        Parameters
        ----------
        coefficients
            An ``np.ndarray`` of values, with shape `(X, Y, Z, W)`, where
            the last channel contains e.g. tensor components.
        get_gradient
            If ``True``, returns a ``'gradient'`` of the same shape as :attr:`coefficients`.
            Otherwise, the entry ``'gradient'`` will be ``None``.
        gradient_part
            Used for the zonal harmonics resonstructions to determine what part of the gradient is
            being calculated. Default is None.

        Returns
        -------
            A dictionary with at least two entries, ``residual_norm`` and ``gradient``.
        """
        pass

    @property
    @abstractmethod
    def _function_as_str(self) -> str:
        """ Should return a string representation of the associated norm
        of the coefficients in Python idiom, e.g. 'R(x) = 0.5 * x ** 2' for L2. """
        pass

    @property
    @abstractmethod
    def _function_as_tex(self) -> str:
        """ Should return a string representation of the associated norm
        of the coefficients in MathJax-renderable TeX, e.g. $R(x) = \frac{r^2}{2}$ for L2"""
        pass

    def __hash__(self) -> int:
        to_hash = [self._function_as_str]
        return int(list_to_hash(to_hash), 16)

    def __str__(self) -> str:
        s = []
        wdt = 74
        s += ['=' * wdt]
        s += [self.__class__.__name__.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, precision=5, linewidth=60, edgeitems=1):
            s += ['{:18} : {}'.format('Function of coefficients', self._function_as_str)]
            s += ['{:18} : {}'.format('hash', hex(hash(self))[2:8])]
        s += ['-' * wdt]
        return '\n'.join(s)

    def _repr_html_(self) -> str:
        s = []
        s += [f'<h3>{self.__class__.__name__}</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th><th>Data</th></tr></thead>']
        s += ['<tbody>']
        with np.printoptions(threshold=4, edgeitems=2, precision=2, linewidth=40):
            s += ['<tr><td style="text-align: left;">Function of coefficients</td>']
            s += [f'<td>1</td><td>{self._function_as_tex}</td></tr>']
            s += ['<tr><td style="text-align: left;">Hash</td>']
            h = hex(hash(self))
            s += [f'<td>{len(h)}</td><td>{h[2:8]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
