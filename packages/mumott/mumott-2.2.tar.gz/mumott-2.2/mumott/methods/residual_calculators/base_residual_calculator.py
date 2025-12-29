from abc import ABC, abstractmethod

import logging
import numpy as np
from numpy.typing import NDArray

from mumott import DataContainer
from mumott.methods.basis_sets.base_basis_set import BasisSet
from mumott.methods.projectors.base_projector import Projector
from mumott.methods.utilities.preconditioning import get_largest_eigenvalue

logger = logging.getLogger(__name__)


class ResidualCalculator(ABC):

    """This is the base class from which specific residual calculators are being derived.
    """

    def __init__(self,
                 data_container: DataContainer,
                 basis_set: BasisSet,
                 projector: Projector,
                 use_scalar_projections: bool = False,
                 scalar_projections: NDArray[float] = None):
        self._data_container = data_container
        self._geometry_hash = hash(data_container.geometry)
        self._basis_set = basis_set
        self._basis_set_hash = hash(self._basis_set)
        self._projector = projector
        # GPU-based projectors need float32
        self._coefficients = np.zeros((*self._data_container.geometry.volume_shape,
                                      len(self._basis_set)), dtype=self.dtype)
        self._use_scalar_projections = use_scalar_projections
        self._scalar_projections = scalar_projections

        self._basis_set.probed_coordinates = self.probed_coordinates

    @property
    def dtype(self) -> np.dtype:
        """ dtype used by the projector object attached to this instance. """
        return self._projector.dtype

    @abstractmethod
    def get_residuals(self) -> dict:
        pass

    @property
    def probed_coordinates(self) -> NDArray:
        """ An array of 3-vectors with the (x, y, z)-coordinates
        on the reciprocal space map probed by the method.
        Structured as ``(N, K, I, 3)``, where ``N``
        is the number of projections, ``K`` is the number of
        detector segments, ``I`` is the number of points to be
        integrated over, and the last axis contains the
        (x, y, z)-coordinates.

        Notes
        -----
        The region of the reciprocal space map spanned by
        each detector segment is represented as a parametric curve
        between each segment. This is intended to simulate the effect
        of summing up pixels on a detector screen. For other methods of
        generating data (e.g., by fitting measurements to a curve),
        it may be more appropriate to only include a single point, which
        will then have the same coordinates as the center of a detector
        segments. This can be achieved by setting the property
        :attr:`integration_samples`.

        The number of detector segments is
        `len(geometry.detecor_angles)*len(geometry.two_theta)`
        i.e. the product of the number of two_theta bins times the number of
        azimuthal bins. As a default, only on two theta bin is used.
        When several two_theta bins are used, the second index corresponds
        to a raveled array, where the azimuthal is the fast index and
        two theta is the slow index.
        """
        return self._data_container.geometry.probed_coordinates

    def get_estimate_of_matrix_norm(self):
        """Calculate the matrix norm of the matrix implied by the basis set and
        projector associated with this residual calculator.

        Returns
        -------
        An estimate of the matrix norm (largest singular value)
        """
        return get_largest_eigenvalue(self._basis_set, self._projector,)

    @property
    def coefficients(self) -> NDArray:
        """Optimization coefficients for this method."""
        return self._coefficients

    @coefficients.setter
    def coefficients(self, val: NDArray) -> None:
        self._coefficients = val.reshape(self._coefficients.shape).astype(self.dtype)

    @property
    def _data(self) -> NDArray:
        """ Internal method for choosing between scalar_projections and data. """
        if self._use_scalar_projections:
            return self._scalar_projections
        else:
            return self._data_container.data

    @property
    def _weights(self) -> NDArray:
        """ Internal method for choosing between weights for the
        scalar_projections or weights for the data. """
        if self._use_scalar_projections:
            return np.mean(self._data_container.projections.weights, axis=-1)[..., None]
        else:
            return self._data_container.projections.weights

    @property
    def _detector_angles(self) -> NDArray:
        """ Internal method for choosing between detector angles for the data
        or detector angles for the scalar_projections. """
        if self._use_scalar_projections:
            return np.array((0.,))
        else:
            return self._data_container.geometry.detector_angles

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def _repr_html_(self) -> str:
        pass
