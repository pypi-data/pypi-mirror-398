from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np
from numpy.typing import NDArray, DTypeLike
from numpy import float32

from mumott import Geometry


class Projector(ABC):
    """Projector for transforms of tensor fields from three-dimensional
    space to projection space.
    """

    def __init__(self,
                 geometry: Geometry):
        self._geometry = geometry
        self._geometry_hash = hash(geometry)
        self._basis_vector_projection = np.zeros((len(self._geometry), 3), dtype=np.float64)
        self._basis_vector_j = np.zeros((len(self._geometry), 3), dtype=np.float64)
        self._basis_vector_k = np.zeros((len(self._geometry), 3), dtype=np.float64)

    @abstractmethod
    def forward(self,
                field: NDArray,
                index: NDArray[int]) -> NDArray:
        pass

    @abstractmethod
    def adjoint(self,
                projection: NDArray,
                index: NDArray[int]) -> NDArray:
        pass

    def _calculate_basis_vectors(self) -> None:
        """ Calculates the basis vectors for the John transform, one projection vector
        and two coordinate vectors. """
        self._basis_vector_projection = np.einsum(
            'kij,i->kj', self._geometry.rotations_as_array, self._geometry.p_direction_0)
        self._basis_vector_j = np.einsum(
            'kij,i->kj', self._geometry.rotations_as_array, self._geometry.j_direction_0)
        self._basis_vector_k = np.einsum(
            'kij,i->kj', self._geometry.rotations_as_array, self._geometry.k_direction_0)

    def _check_indices_kind_is_integer(self, indices: NDArray):
        if indices.dtype.kind != 'i':
            raise TypeError('Elements of indices must be of integer kind,'
                            f' but the provided indices have dtype.kind {indices.dtype.kind}!')

    @property
    def dtype(self) -> DTypeLike:
        """ The dtype input fields and projections require."""
        return float32

    @property
    def is_dirty(self) -> bool:
        """ Returns ``True`` if the system geometry has changed without
        the projection geometry having been updated. """
        return self._geometry_hash != hash(self._geometry)

    def _update(self, force_update: bool = False) -> None:
        if self.is_dirty or force_update:
            self._calculate_basis_vectors()
            self._geometry_hash = hash(self._geometry)

    @property
    def number_of_projections(self) -> int:
        """ The number of projections as defined by the length of the
        :class:`Geometry <mumott.Geometry>` object attached to this
        instance. """
        self._update()
        return len(self._geometry)

    @property
    def volume_shape(self) -> Tuple[int]:
        """ The shape of the volume defined by the :class:`Geometry <mumott.Geometry>`
        object attached to this instance, as a tuple. """
        self._update()
        return tuple(self._geometry.volume_shape)

    @property
    def projection_shape(self) -> Tuple[int]:
        """ The shape of each projection defined by the :class:`Geometry <mumott.Geometry>`
        object attached to this instance, as a tuple. """
        self._update()
        return tuple(self._geometry.projection_shape)
