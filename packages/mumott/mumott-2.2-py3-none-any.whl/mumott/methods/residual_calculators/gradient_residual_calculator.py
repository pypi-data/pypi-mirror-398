import logging
from typing import Dict

import numpy as np
from numpy.typing import NDArray

from mumott import DataContainer
from mumott.core.hashing import list_to_hash
from .base_residual_calculator import ResidualCalculator
from mumott.methods.basis_sets.base_basis_set import BasisSet
from mumott.methods.projectors.base_projector import Projector


logger = logging.getLogger(__name__)


class GradientResidualCalculator(ResidualCalculator):
    """Class that implements the GradientResidualCalculator method.
    This residual calculator is an appropriate choice for :term:`SAXS` tensor tomography, as it relies
    on the small-angle approximation. It relies on inverting the John transform
    (also known as the X-ray transform) of a tensor field (where each tensor is a
    representation of a spherical function) by comparing it to scattering data which
    has been corrected for transmission.

    Parameters
    ----------
    data_container : DataContainer
        Container for the data which is to be reconstructed.
    basis_set : BasisSet
        The basis set used for representing spherical functions.
    projector : Projector
        The type of projector used together with this method.
    use_scalar_projections : bool
        Whether to use a set of scalar projections, rather than the data
        in :attr:`data_container`.
    scalar_projections : NDArray[float]
        If :attr:`use_scalar_projections` is true, the set of scalar projections to use.
        Should have the same shape as :attr:`data_container.data`, except with
        only one channel in the last index.
    """

    def __init__(self,
                 data_container: DataContainer,
                 basis_set: BasisSet,
                 projector: Projector,
                 use_scalar_projections: bool = False,
                 scalar_projections: NDArray[float] = None):
        super().__init__(data_container,
                         basis_set,
                         projector,
                         use_scalar_projections,
                         scalar_projections,)

    def get_residuals(self,
                      get_gradient: bool = False,
                      get_weights: bool = False,
                      gradient_part: str = None) -> dict[str, NDArray[float]]:
        """ Calculates a residuals and possibly a gradient between
        coefficients projected using the :attr:`BasisSet` and :attr:`Projector`
        attached to this instance.

        Parameters
        ----------
        get_gradient
            Whether to return the gradient. Default is ``False``.
        get_weights
            Whether to return weights. Default is ``False``. If ``True`` along with
            :attr:`get_gradient`, the gradient will be computed with weights.
        gradient_part
            Used for the zonal harmonics resonstructions to determine what part of the gradient is
            being calculated. Default is ``None``. Raises a ``NotImplementedError`` for any other value.

        Returns
        -------
            A dictionary containing the residuals, and possibly the
            gradient and/or weights. If gradient and/or weights
            are not returned, their value will be ``None``.
        """

        if gradient_part is not None:
            raise NotImplementedError('The GradientResidualCalculator class does not work with optimizing '
                                      'angles. Use the ZHTTResidualCalculator class instead.')

        projection = self._basis_set.forward(self._projector.forward(self._coefficients))
        residuals = projection - self._data
        if get_gradient:
            # todo: consider if more complicated behaviour is useful,
            # e.g. providing function to be applied to weights
            if get_weights:
                gradient = self._projector.adjoint(
                    self._basis_set.gradient(residuals * self._weights).astype(self.dtype))
            else:
                gradient = self._projector.adjoint(
                    self._basis_set.gradient(residuals).astype(self.dtype))
        else:
            gradient = None

        if get_weights:
            weights = self._weights
        else:
            weights = None

        return dict(residuals=residuals, gradient=gradient, weights=weights)

    def get_gradient_from_residual_gradient(self, residual_gradient: NDArray[float]) -> Dict:
        """ Projects a residual gradient into coefficient and volume space. Used
        to get gradients from more complicated residuals, e.g., the Huber loss.
        Assumes that any weighting to the residual gradient has already been applied.

        Parameters
        ----------
        residual_gradient
            The residual gradient, from which to calculate the gradient.

        Returns
        -------
            An ``NDArray`` containing the gradient.
        """
        return self._projector.adjoint(
                    self._basis_set.gradient(residual_gradient).astype(self.dtype))

    def _update(self, force_update: bool = False) -> None:
        """ Carries out necessary updates if anything changes with respect to
        the geometry or basis set. """
        if not (self.is_dirty or force_update):
            return
        self._basis_set.probed_coordinates = self.probed_coordinates
        len_diff = len(self._basis_set) - self._coefficients.shape[-1]
        vol_diff = self._data_container.geometry.volume_shape - np.array(self._coefficients.shape[:-1])
        # TODO: Think about whether the ``Method`` should do this or handle it differently
        if np.any(vol_diff != 0) or len_diff != 0:
            logger.warning('Shape of coefficient array has changed, array will be padded'
                           ' or truncated.')
            # save old array, no copy needed
            old_coefficients = self._coefficients
            # initialize new array
            self._coefficients = \
                np.zeros((*self._data_container.geometry.volume_shape, len(self._basis_set)),
                         dtype=self.dtype)
            # for comparison of volume shapes
            shapes = zip(old_coefficients.shape[:-1], self._coefficients.shape[:-1])
            # old coefficients go into middle of new coefficients except in last index
            slice_1 = tuple([slice(max(0, (d-s) // 2), min(d, (s + d) // 2)) for s, d in shapes]) + \
                (slice(0, min(old_coefficients.shape[-1], self._coefficients.shape[-1])),)
            # zip objects are depleted
            shapes = zip(old_coefficients.shape[:-1], self._coefficients.shape[:-1])
            slice_2 = tuple([slice(max(0, (s-d) // 2), min(s, (s + d) // 2)) for s, d in shapes]) + \
                (slice(0, min(old_coefficients.shape[-1], self._coefficients.shape[-1])),)
            # assumption made that old_coefficients[..., 0] correspnds to self._coefficients[..., 0]
            self._coefficients[slice_1] = old_coefficients[slice_2]
            # Assumption may not be true for all representations!
            # TODO: Consider more logic here using e.g. basis set properties.
            if len_diff != 0:
                logger.warning('Size of basis set has changed. Coefficients have'
                               ' been copied over starting at index 0. If coefficients'
                               ' of new size do not line up with the old size,'
                               ' please reinitialize the coefficients.')
        self._geometry_hash = hash(self._data_container.geometry)
        self._basis_set_hash = hash(self._basis_set)

    def __hash__(self) -> int:
        """ Returns a hash of the current state of this instance. """
        to_hash = [self._coefficients,
                   hash(self._projector),
                   hash(self._data_container.geometry),
                   self._basis_set_hash,
                   self._geometry_hash]
        return int(list_to_hash(to_hash), 16)

    @property
    def is_dirty(self) -> bool:
        """ ``True`` if stored hashes of geometry or basis set objects do
        not match their current hashes. Used to trigger updates """
        return ((self._geometry_hash != hash(self._data_container.geometry)) or
                (self._basis_set_hash != hash(self._basis_set)))

    def __str__(self) -> str:
        wdt = 74
        s = []
        s += ['=' * wdt]
        s += [self.__class__.__name__.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, precision=5, linewidth=60, edgeitems=1):
            s += ['{:18} : {}'.format('BasisSet', self._basis_set.__class__.__name__)]
            s += ['{:18} : {}'.format('Projector', self._projector.__class__.__name__)]
            s += ['{:18} : {}'.format('is_dirty', self.is_dirty)]
            s += ['{:18} : {}'.format('probed_coordinates (hash)',
                                      hex(hash(self.probed_coordinates))[:6])]
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
            s += ['<tr><td style="text-align: left;">BasisSet</td>']
            s += [f'<td>{1}</td><td>{self._basis_set.__class__.__name__}</td></tr>']
            s += ['<tr><td style="text-align: left;">Projector</td>']
            s += [f'<td>{len(self._projector.__class__.__name__)}</td>'
                  f'<td>{self._projector.__class__.__name__}</td></tr>']
            s += ['<tr><td style="text-align: left;">Is dirty</td>']
            s += [f'<td>{1}</td><td>{self.is_dirty}</td></tr>']
            s += ['<tr><td style="text-align: left;">probed_coordinates</td>']
            s += [f'<td>{self.probed_coordinates.vector.shape}</td>'
                  f'<td>{hex(hash(self.probed_coordinates))[:6]} (hash)</td></tr>']
            s += ['<tr><td style="text-align: left;">Hash</td>']
            h = hex(hash(self))
            s += [f'<td>{len(h)}</td><td>{h[2:8]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
