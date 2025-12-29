import logging

from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from mumott import Geometry
from mumott.core.john_transform import john_transform, john_transform_adjoint
from mumott.core.hashing import list_to_hash
from .base_projector import Projector

logger = logging.getLogger(__name__)


class SAXSProjector(Projector):
    """
    Projector for transforms of tensor fields from three-dimensional space
    to projection space using a bilinear interpolation algorithm that produces results similar
    to those of :class:`SAXSProjectorCUDA <mumott.methods.projectors.SAXSProjectorCUDA>`
    using CPU computation.

    Parameters
    ----------
    geometry : Geometry
        An instance of :class:`Geometry <mumott.Geometry>` containing the
        necessary vectors to compute forwared and adjoint projections.
    """
    def __init__(self,
                 geometry: Geometry):

        super().__init__(geometry)
        self._update(force_update=True)
        self._numba_hash = None
        self._compiled_john_transform = None
        self._compiled_john_transform_adjoint = None

    @staticmethod
    def _get_zeros_method(array: NDArray):
        """ Internal method for dispatching functions for array allocation.
        Included to simplify subclassing."""
        return np.zeros

    def _get_john_transform_parameters(self,
                                       indices: NDArray[int] = None) -> Tuple:
        if indices is None:
            indices = np.s_[:]
        vector_p = self._basis_vector_projection[indices]
        vector_j = self._basis_vector_j[indices]
        vector_k = self._basis_vector_k[indices]
        j_offsets = self._geometry.j_offsets_as_array[indices]
        k_offsets = self._geometry.k_offsets_as_array[indices]
        return (vector_p, vector_j, vector_k, j_offsets, k_offsets)

    def forward(self,
                field: NDArray,
                indices: NDArray[int] = None) -> NDArray:
        """ Compute the forward projection of a tensor field.

        Parameters
        ----------
        field
            An array containing coefficients in its fourth dimension,
            which are to be projected into two dimensions. The first three
            dimensions should match the ``volume_shape`` of the sample.
        indices
            A one-dimensional array containing one or more indices
            indicating which projections are to be computed. If ``None``,
            all projections will be computed.

        Returns
        -------
            An array with four dimensions ``(I, J, K, L)``, where
            the first dimension matches :attr:`indices`, such that
            ``projection[i]`` corresponds to the geometry of projection
            ``indices[i]``. The second and third dimension contain
            the pixels in the ``J`` and ``K`` dimension respectively, whereas
            the last dimension is the coefficient dimension, matching ``field[-1]``.
        """
        if not np.allclose(field.shape[:-1], self._geometry.volume_shape):
            raise ValueError(f'The shape of the input field ({field.shape}) does not match the'
                             f' volume shape expected by the projector ({self._geometry.volume_shape})')
        self._update()
        if indices is None:
            return self._forward_stack(field)
        return self._forward_subset(field, indices)

    def _forward_subset(self,
                        field: NDArray,
                        indices: NDArray[int]) -> NDArray:
        """ Internal method for computing a subset of projections.

        Parameters
        ----------
        field
            The field to be projected.
        indices
            The indices indicating the subset of all projections in the
            system geometry to be computed.

        Returns
        -------
            The resulting projections.
        """
        indices = np.array(indices).ravel()
        init_method = self._get_zeros_method(field)
        projections = init_method((indices.size,) +
                                  tuple(self._geometry.projection_shape) +
                                  (field.shape[-1],), dtype=self.dtype)
        self._check_indices_kind_is_integer(indices)
        return self._john_transform(
             field, projections, *self._get_john_transform_parameters(indices))

    def _forward_stack(self,
                       field: NDArray) -> NDArray:
        """Internal method for forward projecting an entire stack.

        Parameters
        ----------
        field
            The field to be projected.

        Returns
        -------
            The resulting projections.
        """
        init_method = self._get_zeros_method(field)
        projections = init_method((len(self._geometry),) +
                                  tuple(self._geometry.projection_shape) +
                                  (field.shape[-1],), dtype=self.dtype)
        return self._john_transform(field, projections, *self._get_john_transform_parameters())

    def adjoint(self,
                projections: NDArray,
                indices: NDArray[int] = None) -> NDArray:
        """ Compute the adjoint of a set of projections according to the system geometry.

        Parameters
        ----------
        projections
            An array containing coefficients in its last dimension,
            from e.g. the residual of measured data and forward projections.
            The first dimension should match :attr:`indices` in size, and the
            second and third dimensions should match the system projection geometry.
            The array must be contiguous and row-major.
        indices
            A one-dimensional array containing one or more indices
            indicating from which projections the adjoint is to be computed.

        Returns
        -------
            The adjoint of the provided projections.
            An array with four dimensions ``(X, Y, Z, P)``, where the first
            three dimensions are spatial and the last dimension runs over
            coefficients.
        """
        if not np.allclose(projections.shape[-3:-1], self._geometry.projection_shape):
            raise ValueError(f'The shape of the projections ({projections.shape}) does not match the'
                             f' projection shape expected by the projector'
                             f' ({self._geometry.projection_shape})')
        if not projections.flags['C_CONTIGUOUS']:
            raise ValueError('The projections array must be contiguous and row-major, '
                             f'but has strides {projections.strides}.')

        self._update()
        if indices is None:
            return self._adjoint_stack(projections)
        return self._adjoint_subset(projections, indices)

    def _adjoint_subset(self,
                        projections: NDArray,
                        indices: NDArray[int]) -> NDArray:
        """ Internal method for computing the adjoint of only a subset of projections.

        Parameters
        ----------
        projections
            An array containing coefficients in its last dimension,
            from e.g. the residual of measured data and forward projections.
            The first dimension should match :attr:`indices` in size, and the
            second and third dimensions should match the system projection geometry.
        indices
            A one-dimensional array containing one or more indices
            indicating from which projections the adjoint is to be computed.

        Returns
        -------
            The adjoint of the provided projections.
            An array with four dimensions ``(X, Y, Z, P)``, where the first
            three dimensions are spatial and the last dimension runs over
            coefficients. """
        indices = np.array(indices).ravel()
        if projections.ndim == 3:
            assert indices.size == 1
            projections = projections[np.newaxis, ...]
        else:
            assert indices.size == projections.shape[0]
        self._check_indices_kind_is_integer(indices)
        init_method = self._get_zeros_method(projections)
        field = init_method(tuple(self._geometry.volume_shape) +
                            (projections.shape[-1],), dtype=self.dtype)
        return self._john_transform_adjoint(
            field, projections, *self._get_john_transform_parameters(indices))

    def _adjoint_stack(self,
                       projections: NDArray) -> NDArray:
        """ Internal method for computing the adjoint of a whole stack of projections.

        Parameters
        ----------
        projections
            An array containing coefficients in its last dimension,
            from e.g. the residual of measured data and forward projections.
            The first dimension should run over all the projection directions
            in the system geometry.

        Returns
        -------
            The adjoint of the provided projections.
            An array with four dimensions ``(X, Y, Z, P)``, where the first
            three dimensions are spatial, and the last dimension runs over
            coefficients. """
        assert projections.shape[0] == len(self._geometry)
        init_method = self._get_zeros_method(projections)
        field = init_method(tuple(self._geometry.volume_shape) +
                            (projections.shape[-1],), dtype=self.dtype)
        return self._john_transform_adjoint(
            field, projections, *self._get_john_transform_parameters())

    def _compile_john_transform(self,
                                field: NDArray[float],
                                projections: NDArray[float],
                                *args) -> None:
        """ Internal method for compiling John transform only as needed. """
        self._compiled_john_transform = john_transform(
                                            field, projections, *args)
        self._compiled_john_transform_adjoint = john_transform_adjoint(
                                                    field, projections, *args)

    def _john_transform(self,
                        field: NDArray[float],
                        projections: NDArray[float],
                        *args) -> None:
        """ Internal method for dispatching John Transform call. Included to
        simplify subclassing. Note that the result is calculated in-place."""
        to_hash = [field.shape[-1], *args]
        current_hash = list_to_hash(to_hash)
        if list_to_hash(to_hash) != self._numba_hash:
            self._compile_john_transform(field, projections, *args)
            self._numba_hash = current_hash
        return self._compiled_john_transform(field, projections)

    def _john_transform_adjoint(self,
                                field: NDArray[float],
                                projections: NDArray[float],
                                *args) -> None:
        """ Internal method for dispatching john transform adjoint function call. Included to
        simplify subclassing. Note that the result is calculated in-place."""
        to_hash = [field.shape[-1], *args]
        current_hash = list_to_hash(to_hash)
        if list_to_hash(to_hash) != self._numba_hash:
            self._compile_john_transform(field, projections, *args)
            self._numba_hash = current_hash
        return self._compiled_john_transform_adjoint(field, projections)

    @property
    def john_transform_parameters(self) -> tuple:
        """ Tuple of John Transform parameters, which can be passed manually
        to compile John Transform kernels and construct low-level pipelines.
        For advanced users only."""
        return self._get_john_transform_parameters()

    @property
    def dtype(self) -> np.typing.DTypeLike:
        """ Preferred dtype of this ``Projector``. """
        return np.float64

    def __hash__(self) -> int:
        to_hash = [self._basis_vector_projection,
                   self._basis_vector_j,
                   self._basis_vector_k,
                   self._geometry_hash,
                   hash(self._geometry),
                   self._numba_hash]
        return int(list_to_hash(to_hash), 16)

    def __str__(self) -> str:
        wdt = 74
        s = []
        s += ['-' * wdt]
        s += [self.__class__.__name__.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, edgeitems=2, precision=5, linewidth=60):
            s += ['{:18} : {}'.format('is_dirty', self.is_dirty)]
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
            s += ['<tr><td style="text-align: left;">is_dirty</td>']
            s += [f'<td>1</td><td>{self.is_dirty}</td></tr>']
            s += ['<tr><td style="text-align: left;">hash</td>']
            s += [f'<td>{len(hex(hash(self)))}</td><td>{hex(hash(self))[2:8]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
