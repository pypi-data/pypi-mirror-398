import logging
from typing import Any, Dict, Iterator, Tuple

import numpy as np
from numpy.typing import NDArray

from mumott import ProbedCoordinates
from mumott.core.hashing import list_to_hash
from .base_basis_set import BasisSet


logger = logging.getLogger(__name__)


class TrivialBasis(BasisSet):
    """ Basis set class for the trivial basis, i.e., the identity basis.
    This can be used as a scaffolding class when implementing, e.g., scalar tomography,
    as it implements all the necessary functionality to qualify as a :class:`BasisSet`.

    Parameters
    ----------
    channels
        Number of channels in the last index. Default is ``1``. For scalar data,
        the default value of ``1`` is appropriate. For any other use-case, where the representation
        on the sphere and the representation in detector space are equivalent,
        such as reconstructing scalars of multiple q-ranges at once, a different
        number of channels can be set.
    """
    def __init__(self, channels: int = 1):
        self._probed_coordinates = ProbedCoordinates(vector=np.array((0., 0., 1.)))
        self._probed_coordinates_hash = hash(self.probed_coordinates)
        self._channels = channels

    def _get_projection_matrix(self, probed_coordinates: ProbedCoordinates = None):
        return np.eye(self._channels)

    def forward(self,
                coefficients: NDArray,
                *args,
                **kwargs) -> NDArray:
        """ Returns the provided coefficients with no modification.

        Parameters
        ----------
        coefficients
            An array of coefficients, of arbitrary shape, except the last index
            must specify the same number of channels as was specified for this basis.

        Returns
        -------
            The provided :attr`coefficients` with no modification.

        Notes
        -----
        The :attr:`args` and :attr:`kwargs` are ignored, but included for compatibility with methods
        that input other arguments.
        """
        assert coefficients.shape[-1] == len(self)
        return coefficients

    def gradient(self,
                 coefficients: NDArray,
                 *args,
                 **kwargs) -> NDArray:
        """ Returns the provided coefficients with no modification.

        Parameters
        ----------
        coefficients
            An array of coefficients of arbitrary shape except the last index
            must specify the same number of channels as was specified for this basis.

        Returns
        -------
            The provided :attr`coefficients` with no modification.

        Notes
        -----
        The :attr:`args` and :attr:`kwargs` are ignored, but included for compatibility with methods
        that input other argumetns.
        """
        assert coefficients.shape[-1] == len(self)
        return coefficients

    def get_inner_product(self,
                          u: NDArray,
                          v: NDArray) -> NDArray:
        r""" Retrieves the inner product of two coefficient arrays, that is to say,
        the sum-product over the last axis.

        Parameters
        ----------
        u
            The first coefficient array, of arbitrary shape and dimension.
        v
            The second coefficient array, of the same shape as :attr:`u`.
        """
        assert u.shape[-1] == len(self)
        assert u.shape == v.shape
        return np.einsum('...i, ...i -> ...', u, v,
                         optimize='greedy')

    def get_output(self,
                   coefficients: NDArray) -> Dict[str, Any]:
        r""" Returns a dictionary of output data for a given array of coefficients.

        Parameters
        ----------
        coefficients
            An array of coefficients of arbitrary shape and dimension.
            Computations only operate over the last axis of :attr:`coefficents`, so derived
            properties in the output will have the shape ``(*coefficients.shape[:-1], ...)``.

        Returns
        -------
            A dictionary containing a dictionary with the field ``basis_set``.

        Notes
        -----
        In detail, the dictionary under the key ``basis_set`` contains:

        basis_set
            name
                The name of the basis set, i.e., ``'TrivialBasis'``
            coefficients
                A copy of :attr:`coefficients`.
            projection_matrix
                The identity matrix of the same size as the number of chanenls.
        """
        assert coefficients.shape[-1] == len(self)
        # Update to ensure non-dirty output state.
        self._update()
        output_dictionary = {}

        # basis set-specific information
        basis_set = {}
        output_dictionary['basis_set'] = basis_set
        basis_set['name'] = type(self).__name__
        basis_set['coefficients'] = coefficients.copy()
        basis_set['projection_matrix'] = self.projection_matrix
        basis_set['hash'] = hex(hash(self))
        return output_dictionary

    def get_spherical_harmonic_coefficients(
        self,
        coefficients: NDArray[float],
        ell_max: int = None
    ) -> NDArray[float]:
        """ Convert a set of spherical harmonics coefficients to a different :attr:`ell_max`
        by either zero-padding or truncation and return the result.

        Parameters
        ----------
        coefficients
            An array of coefficients of arbitrary shape, provided that the
            last dimension contains the coefficients for one function.
        ell_max
            The band limit of the spherical harmonic expansion.
        """

        if coefficients.shape[-1] != len(self):
            raise ValueError(f'The number of coefficients ({coefficients.shape[-1]}) does not match '
                             f'the expected value. ({len(self)})')

        num_coeff_output = (ell_max+1) * (ell_max+2) // 2

        output_array = np.zeros((*coefficients.shape[:-1], num_coeff_output))
        output_array[..., 0] = coefficients[..., 0]
        return output_array

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """ Allows class to be iterated over and in particular be cast as a dictionary.
        """
        yield 'name', type(self).__name__
        yield 'projection_matrix', self._projection_matrix
        yield 'hash', hex(hash(self))[2:]

    def __len__(self) -> int:
        return self._channels

    def __hash__(self) -> int:
        """Returns a hash reflecting the internal state of the instance.

        Returns
        -------
            A hash of the internal state of the instance,
            cast as an ``int``.
        """
        to_hash = [self._channels,
                   self._probed_coordinates_hash]
        return int(list_to_hash(to_hash), 16)

    def _update(self) -> None:
        if self.is_dirty:
            self._probed_coordinates_hash = hash(self._probed_coordinates)

    @property
    def channels(self) -> int:
        """ The number of channels this basis supports. """
        return self._channels

    @channels.setter
    def channels(self, value: int) -> None:
        self._channels = value

    @property
    def projection_matrix(self):
        """The identity matrix of the same rank as the number of channels
        specified."""
        return np.eye(self._channels, dtype=np.float64)

    @property
    def is_dirty(self) -> bool:
        return hash(self._probed_coordinates) != self._probed_coordinates_hash

    def __str__(self) -> str:
        wdt = 74
        s = []
        s += ['-' * wdt]
        s += [self.__class__.__name__.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, edgeitems=2, precision=5, linewidth=60):
            s += ['{:18} : {}'.format('Hash', hex(hash(self))[2:8])]
        s += ['-' * wdt]
        return '\n'.join(s)

    def _repr_html_(self) -> str:
        s = []
        s += [f'<h3>{self.__class__.__name__}</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th><th>Data</th></tr></thead>']
        s += ['<tbody>']
        with np.printoptions(threshold=4, edgeitems=2, precision=2, linewidth=40):
            s += [f'<td>{len(hex(hash(self)))}</td><td>{hex(hash(self))[2:8]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
