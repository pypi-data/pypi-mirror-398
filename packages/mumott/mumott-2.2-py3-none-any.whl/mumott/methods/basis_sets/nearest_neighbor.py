import logging
from typing import Tuple
from copy import deepcopy

import numpy as np
from numpy.typing import NDArray

from mumott import ProbedCoordinates, DataContainer, Geometry, SphericalHarmonicMapper
from mumott.core.hashing import list_to_hash
from mumott.methods.utilities.tensor_operations import (framewise_contraction,
                                                        framewise_contraction_transpose)
from mumott.output_handling.reconstruction_derived_quantities import\
    (ReconstructionDerivedQuantities, get_sorted_eigenvectors)
from .base_basis_set import BasisSet

logger = logging.getLogger(__name__)


class NearestNeighbor(BasisSet):
    r""" Basis set class for nearest-neighbor interpolation. Used to construct methods similar to that
    presented in `Schaff et al. (2015) <https://doi.org/10.1038/nature16060>`_.
    By default this representation is sparse and maps only a single direction on the sphere
    to each detector segment. This can be changed; see ``kwargs``.

    Parameters
    ----------
    directions : NDArray[float]
        Two-dimensional Array containing the ``N`` sensitivity directions with shape ``(N, 3)``.
    probed_coordinates : ProbedCoordinates
        Optional. Coordinates on the sphere probed at each detector segment by the
        experimental method. Its construction from the system geometry is method-dependent.
        By default, an empty instance of :class:`mumott.ProbedCoordinates` is created.
    enforce_friedel_symmetry : bool
        If set to ``True``, Friedel symmetry will be enforced, using the assumption that points
        on opposite sides of the sphere are equivalent.
    kwargs
        Miscellaneous arguments which relate to segment integrations can be
        passed as keyword arguments:

            integration_mode
                 Mode to integrate line segments on the reciprocal space sphere. Possible options are
                 ``'simpson'``, ``'midpoint'``, ``'romberg'``, ``'trapezoid'``.
                 ``'simpson'``, ``'trapezoid'``, and ``'romberg'`` use adaptive
                 integration with the respective quadrature rule from ``scipy.integrate``.
                 ``'midpoint'`` uses a single mid-point approximation of the integral.
                 Default value is ``'simpson'``.

            n_integration_starting_points
                 Number of points used in the first iteration of the adaptive integration.
                 The number increases by the rule ``N`` &larr; ``2 * N - 1`` for each iteration.
                 Default value is 3.
            integration_tolerance
                 Tolerance for the maximum relative error between iterations before the integral
                 is considered converged. Default is ``1e-3``.

            integration_maxiter
                 Maximum number of iterations. Default is ``10``.
            enforce_sparsity
                 If ``True``, limites the number of basis set elements
                 that can map to each detector segemnt. Default is ``False``.
            sparsity_count
                 If ``enforce_sparsity`` is set to ``True``, the number of
                 basis set elements that can map to each detector segment.
                 Default value is ``1``.
                 """
    def __init__(self,
                 directions: NDArray[float],
                 probed_coordinates: ProbedCoordinates = None,
                 enforce_friedel_symmetry: bool = True,
                 **kwargs):
        # This basis set struggles with integral convergence due to sharp transitions
        kwargs.update(dict(integration_tolerance=kwargs.get('integration_tolerance', 1e-3),
                           sparsity_count=kwargs.get('sparsity_count', 1)))
        super().__init__(probed_coordinates, **kwargs)
        # Handling grid of directions
        self._number_of_coefficients = directions.shape[0]
        if enforce_friedel_symmetry:
            self._directions_full = np.concatenate((directions, -directions), axis=0)
        else:
            self._directions_full = np.array(directions)

        self._probed_coordinates_hash = hash(self.probed_coordinates)

        self._enforce_friedel_symmetry = enforce_friedel_symmetry
        self._projection_matrix = self._get_integrated_projection_matrix()

    def find_nearest_neighbor_index(self, probed_directions: NDArray[float]) -> NDArray[int]:
        """
        Caluculate the nearest neighbor sensitivity directions for an array of x-y-z vectors.

        Parameters
        ----------
        probed_directions
            Array with length 3 along its last axis

        Returns
        -------
            Array with same shape as the input except for the last dimension, which
            contains the index of the nearest-neighbor sensitivity direction.
        """

        # normalize input directions
        input_shape = probed_directions.shape
        normed_probed_directions = probed_directions / \
            np.linalg.norm(probed_directions, axis=-1)[..., np.newaxis]

        # Find distance (3D euclidian) between each probed direction and sensitivity direction
        pad_dimension = (1,) * (len(input_shape)-1)
        distance = np.sum((normed_probed_directions[np.newaxis, ...] -
                           self._directions_full.reshape(self._directions_full.shape[0],
                           *pad_dimension, 3))**2, axis=-1)

        # Find nearest_neighbor
        best_dir = np.argmin(distance, axis=0)

        if self._enforce_friedel_symmetry:
            best_dir = best_dir % self._number_of_coefficients
        return best_dir

    def get_function_values(self, probed_directions: NDArray) -> NDArray[float]:
        """
        Calculate the value of the basis functions from an array of x-y-z vectors.

        Parameters
        ----------
        probed_directions
            Array with length 3 along its last axis

        Returns
        -------
            Array with same shape as input array except for the last axis, which now
            has length ``N``, i.e., the number of sensitivity directions.

        """

        best_dir = self.find_nearest_neighbor_index(probed_directions)
        input_shape = probed_directions.shape
        output_array = np.zeros((*input_shape[:-1], self._number_of_coefficients))
        for mode_number in range(self._number_of_coefficients):
            output_array[best_dir == mode_number, mode_number] = 1.0
        return output_array

    def get_amplitudes(self, coefficients: NDArray[float],
                       probed_directions: NDArray[float]) -> NDArray[float]:
        """
        Calculate function values of an array of coefficients.

        Parameters
        ----------
        coefficients
            Array of coefficients with coefficient number along its last index.
        probed_directions
            Array with length 3 along its last axis.

        Returns
        -------
            Array with function values. The shape of the array is
            ``(*coefficients.shape[:-1], *probed_directions.shape[:-1])``.
        """
        final_shape = (*coefficients.shape[:-1], *probed_directions.shape[:-1])
        nn_index = self.find_nearest_neighbor_index(probed_directions).ravel()
        amplitudes = np.zeros((np.prod(coefficients.shape[:-1]), np.prod(probed_directions.shape[:-1])))
        coefficients = np.reshape(coefficients, (np.prod(coefficients.shape[:-1]),
                                                 coefficients.shape[-1]))
        for coeff_index in range(amplitudes.shape[0]):
            amplitudes[coeff_index, :] = coefficients[coeff_index, nn_index]

        return amplitudes.reshape(final_shape)

    def get_second_moments(self, coefficients: NDArray[float]) -> NDArray[float]:
        """
        Calculate the second moments of the functions described by :attr:`coefficients`.

        Parameters
        ----------
        coefficients
            An array of coefficients (or residuals) of arbitrary shape so long as the last
            axis has the same size as the number of detector channels.

        Returns
        -------
            Array containing the second moments of the functions described by coefficients,
            formatted as rank-two tensors with tensor indices in the last 2 dimensions.
        """

        if not self._enforce_friedel_symmetry:
            raise NotImplementedError('NearestNeighbor.get_second_moments does not support'
                                      ' cases with Friedel symmetry.')

        second_moments_array = np.zeros((*coefficients.shape[:-1], 3, 3))

        sumint = np.zeros(coefficients.shape[:-1])
        sumxx = np.zeros(coefficients.shape[:-1])
        sumxy = np.zeros(coefficients.shape[:-1])
        sumxz = np.zeros(coefficients.shape[:-1])
        sumyy = np.zeros(coefficients.shape[:-1])
        sumyz = np.zeros(coefficients.shape[:-1])
        sumzz = np.zeros(coefficients.shape[:-1])

        for mode_number in range(len(self)):

            sumint += coefficients[..., mode_number]
            sumxx += coefficients[..., mode_number] * self._directions_full[mode_number, 0]**2
            sumxy += coefficients[..., mode_number] * self._directions_full[mode_number, 0]\
                * self._directions_full[mode_number, 1]
            sumxz += coefficients[..., mode_number] * self._directions_full[mode_number, 0]\
                * self._directions_full[mode_number, 2]
            sumyy += coefficients[..., mode_number] * self._directions_full[mode_number, 1]**2
            sumyz += coefficients[..., mode_number] * self._directions_full[mode_number, 1]\
                * self._directions_full[mode_number, 2]
            sumzz += coefficients[..., mode_number] * self._directions_full[mode_number, 2]**2

        second_moments_array[..., 0, 0] = sumxx / len(self)
        second_moments_array[..., 0, 1] = sumxy / len(self)
        second_moments_array[..., 0, 2] = sumxz / len(self)
        second_moments_array[..., 1, 0] = sumxy / len(self)
        second_moments_array[..., 1, 1] = sumyy / len(self)
        second_moments_array[..., 1, 2] = sumyz / len(self)
        second_moments_array[..., 2, 0] = sumxz / len(self)
        second_moments_array[..., 2, 1] = sumyz / len(self)
        second_moments_array[..., 2, 2] = sumzz / len(self)

        return second_moments_array

    def get_spherical_harmonic_coefficients(
        self,
        coefficients: NDArray[float],
        ell_max: int = None
    ) -> NDArray[float]:
        """ Computes and rturns the spherical harmonic coefficients of the spherical function
        represented by the provided :attr:`coefficients` using a Driscoll-Healy grid.

        For details on the Driscoll-Healy grid, see
        `the SHTools page <https://shtools.github.io/SHTOOLS/grid-formats.html>`_ for a
        comprehensive overview.

        Parameters
        ----------
        coefficients
            An array of coefficients of arbitrary shape, provided that the
            last dimension contains the coefficients for one function.
        ell_max
            The bandlimit of the spherical harmonic expansion.

        """
        dh_grid_size = 2*ell_max + 1
        mapper = SphericalHarmonicMapper(ell_max=ell_max, polar_resolution=dh_grid_size,
                                         azimuthal_resolution=dh_grid_size,
                                         enforce_friedel_symmetry=self._enforce_friedel_symmetry)
        coordinates = mapper.unit_vectors
        amplitudes = self.get_amplitudes(coefficients, coordinates)
        spherical_harmonics_coefficients = mapper.get_harmonic_coefficients(amplitudes)
        return spherical_harmonics_coefficients

    def _get_projection_matrix(self, probed_coordinates: ProbedCoordinates = None) -> NDArray[float]:
        """ Computes the matrix necessary for forward and gradient calculations.
        Called when the coordinate system has been updated, or one of
        :attr:`kernel_scale_parameter` or :attr:`grid_scale` has been changed."""
        if probed_coordinates is None:
            probed_coordinates = self._probed_coordinates
        return self.get_function_values(probed_coordinates.vector)

    def get_sub_geometry(self,
                         direction_index: int,
                         geometry: Geometry,
                         data_container: DataContainer = None,
                         ) -> tuple[Geometry, tuple[NDArray[float], NDArray[float]]]:
        """ Create and return a geometry object corresponding to a scalar tomography problem for
        scattering along the sensitivity direction with index :attr:`direction_index`.
        If optionally a :class:`mumott.DataContainer` is provided, the sinograms and weights for this
        scalar tomography problem will alse be returned.

        Used for an implementation of the algorithm descibed in [Schaff2015]_.

        Parameters
        ----------
        direction_index
            Index of the sensitivity direction.
        geometry
            :class:`mumott.Geometry` object of the full problem.
        data_container (optional)
            :class:`mumott.DataContainer` compatible with :attr:`Geometry` from which a scalar dataset
            will be constructed.

        returns
        -------
        sub_geometry
            Geometry of the scalar problem.
        data_tuple
            :class:`Tuple` containing two numpy arrays. :attr:`data_tuple[0]` is the data of the
            scalar problem. :attr:`data_tuple[1]` are the weights.
        """
        if self._integration_mode != 'midpoint':
            logger.info("The 'Discrete Directions' reconstruction workflow has not been tested"
                        "with detector segment integration. Set :attr:`integration_mode` to ``'midpoint'``"
                        ' or proceed with caution.')

        # Get projection weights
        probed_coordinates = ProbedCoordinates()
        probed_coordinates.vector = geometry.probed_coordinates.vector
        projection_matrix = self._get_integrated_projection_matrix(probed_coordinates)[..., direction_index]

        # Copy over certain parts of geometry
        sub_geometry = deepcopy(geometry)
        sub_geometry.delete_projections()
        sub_geometry.detector_angles = np.array([0])
        sub_geometry.detector_direction_origin = np.array([0, 0, 0])
        sub_geometry.detector_direction_positive_90 = np.array([0, 0, 0])

        if data_container is not None:
            data_list = []
            weight_list = []

        for projection_index in range(len(geometry)):
            if np.any(projection_matrix[projection_index, :] > 0.0):

                # append sub geometry
                sub_geometry.append(deepcopy(geometry[projection_index]))

                # Load data if given
                if data_container is not None:

                    projection_weight = projection_matrix[projection_index, :]
                    weighted_weights = data_container.projections[projection_index].weights\
                        * projection_weight[np.newaxis, np.newaxis, :]
                    weighted_data = data_container.projections[projection_index].data\
                        * weighted_weights

                    weight_list.append(np.sum(weighted_weights, axis=-1))
                    summed_data = np.sum(weighted_data, axis=-1)
                    data_list.append(
                            np.divide(summed_data,
                                      weight_list[-1],
                                      out=np.zeros(summed_data.shape),
                                      where=weight_list[-1] != 0)
                    )  # Avoid runtime warning when weights are zero.

        if data_container is None:
            return sub_geometry, None
        elif len(data_list) == 0:
            logger.warning('No projections found for current direction.')
            return sub_geometry, None
        else:
            data_array = np.stack(data_list, axis=0)
            weight_array = np.stack(weight_list, axis=0)
            return sub_geometry, (data_array, weight_array)

    # TODO there could be a bit of a speedup by doing this without matrix products
    def forward(self,
                coefficients: NDArray[float],
                indices: NDArray[int] = None) -> NDArray[float]:
        """ Carries out a forward computation of projections from reciprocal space modes to
        detector channels, for one or several tomographic projections.

        Parameters
        ----------
        coefficients
            An array of coefficients, of arbitrary shape so long as the last
            axis has the same size as this basis set.
        indices
            Optional. Indices of the tomographic projections for which the forward
            computation is to be performed. If ``None``, the forward computation will
            be performed for all projections.

        Returns
        -------
            An array of values on the detector corresponding to the :attr:`coefficients` given.
            If :attr:`indices` contains exactly one index, the shape is ``(coefficients.shape[:-1], J)``
            where ``J`` is the number of detector segments. If :attr:`indices` is ``None`` or contains
            several indices, the shape is ``(N, coefficients.shape[1:-1], J)`` where ``N``
            is the number of tomographic projections for which the computation is performed.
        """
        assert coefficients.shape[-1] == len(self)
        self._update()
        output = np.zeros(coefficients.shape[:-1] + (self._projection_matrix.shape[1],),
                          coefficients.dtype)
        if indices is None:
            framewise_contraction_transpose(self._projection_matrix,
                                            coefficients,
                                            output)
        elif indices.size == 1:
            np.einsum('ijk, ...k -> ...j',
                      self._projection_matrix[indices],
                      coefficients,
                      out=output,
                      optimize='greedy',
                      casting='unsafe')
        else:
            framewise_contraction_transpose(self._projection_matrix[indices],
                                            coefficients,
                                            output)
        return output

    def gradient(self,
                 coefficients: NDArray[float],
                 indices: NDArray[int] = None) -> NDArray[float]:
        """ Carries out a gradient computation of projections of projections from reciprocal space modes to
        detector channels, for one or several tomographic projections.

        Parameters
        ----------
        coefficients
            An array of coefficients (or residuals) of arbitrary shape so long as the last
            axis has the same size as the number of detector channels.
        indices
            Optional. Indices of the tomographic projections for which the gradient
            computation is to be performed. If ``None``, the gradient computation will
            be performed for all projections.

        Returns
        -------
            An array of gradient values based on the :attr:`coefficients` given.
            If :attr:`indices` contains exactly one index, the shape is ``(coefficients.shape[:-1], J)``
            where ``J`` is the number of detector segments. If indices is ``None`` or contains
            several indices, the shape is ``(N, coefficients.shape[1:-1], J)`` where ``N``
            is the number of tomographic projections for which the computation is performed.
        """
        self._update()
        output = np.zeros(coefficients.shape[:-1] + (self._projection_matrix.shape[2],),
                          coefficients.dtype)
        if indices is None:
            framewise_contraction(self._projection_matrix,
                                  coefficients,
                                  output)
        elif indices.size == 1:
            np.einsum('ikj, ...k -> ...j',
                      self._projection_matrix[indices],
                      coefficients,
                      out=output,
                      optimize='greedy',
                      casting='unsafe')
        else:
            framewise_contraction(self._projection_matrix[indices],
                                  coefficients,
                                  output)
        return output

    def get_output(self,
                   coefficients: NDArray) -> ReconstructionDerivedQuantities:
        r""" Returns a :class:`ReconstructionDerivedQuantities` instance of output data for
        a given array of basis set coefficients.

        Parameters
        ----------
        coefficients
            An array of coefficients of arbitrary shape and dimensions, except
            its last dimension must be the same length as the :attr:`len` of this instance.
            Computations only operate over the last axis of :attr:`coefficients`, so derived
            properties in the output will have the shape ``(*coefficients.shape[:-1], ...)``.

        Returns
        -------
            :class:`ReconstructionDerivedQuantities` containing a number of quantities that
            have been computed from the spherical functions represented by the input
            coefficients.
        """

        assert coefficients.shape[-1] == len(self)
        # Update to ensure non-dirty output state.
        self._update()

        mean_intensity = np.mean(coefficients, axis=-1)
        second_moment_tensor = self.get_second_moments(coefficients)
        eigenvalues, eigenvectors = get_sorted_eigenvectors(second_moment_tensor)
        fractional_anisotropy = np.sqrt((eigenvalues[..., 0] - eigenvalues[..., 1])**2
                                        + (eigenvalues[..., 1] - eigenvalues[..., 2])**2
                                        + (eigenvalues[..., 2] - eigenvalues[..., 0])**2)
        fractional_anisotropy = fractional_anisotropy / np.sqrt(2*np.sum(eigenvalues**2, axis=-1))

        reconstruction_derived_quantities = ReconstructionDerivedQuantities(
            volume_shape=tuple(coefficients.shape[:3]),
            mean_intensity=mean_intensity,
            fractional_anisotropy=fractional_anisotropy,
            eigenvector_1=np.copy(eigenvectors[..., 0]),
            eigenvector_2=np.copy(eigenvectors[..., 1]),
            eigenvector_3=np.copy(eigenvectors[..., 2]),
            eigenvalue_1=np.copy(eigenvalues[..., 0]),
            eigenvalue_2=np.copy(eigenvalues[..., 1]),
            eigenvalue_3=np.copy(eigenvalues[..., 2]),
            second_moment_tensor=second_moment_tensor
        )

        return reconstruction_derived_quantities

    def __len__(self) -> int:
        return self._number_of_coefficients

    def __hash__(self) -> int:
        """Returns a hash reflecting the internal state of the instance.

        Returns
        -------
            A hash of the internal state of the instance,
            cast as an ``int``.
        """
        to_hash = [self.grid,
                   self._enforce_friedel_symmetry,
                   self._projection_matrix,
                   self._probed_coordinates_hash]
        return int(list_to_hash(to_hash), 16)

    def _update(self) -> None:
        # We only run updates if the hashes do not match.
        if self.is_dirty:
            self._projection_matrix = self._get_integrated_projection_matrix()
            self._probed_coordinates_hash = hash(self._probed_coordinates)

    @property
    def is_dirty(self) -> bool:
        return hash(self._probed_coordinates) != self._probed_coordinates_hash

    @property
    def projection_matrix(self) -> NDArray:
        """ The matrix used to project spherical functions from the unit sphere onto the detector.
        If ``v`` is a vector of gaussian kernel coefficients, and ``M`` is the ``projection_matrix``,
        then ``M @ v`` gives the corresponding values on the detector segments associated with
        each projection. ``M[i] @ v`` gives the values on the detector segments associated with
        projection ``i``.
        """
        self._update()
        return self._projection_matrix

    @property
    def enforce_friedel_symmetry(self) -> bool:
        """ If ``True``, Friedel symmetry is enforced, i.e., the point
        :math:`-r` is treated as equivalent to :math:`r`. """
        return self._enforce_friedel_symmetry

    @property
    def grid(self) -> Tuple[NDArray['float'], NDArray['float']]:
        r""" Returns the polar and azimuthal angles of the grid used by the basis.

        Returns
        -------
            A ``Tuple`` with contents ``(polar_angle, azimuthal_angle)``, where the
            polar angle is defined as :math:`\arccos(z)`.
        """
        return self._directions_full[:self._number_of_coefficients, :]

    @property
    def grid_hash(self) -> str:
        """ Returns a hash of :attr:`grid`.
        """
        return list_to_hash([self.grid])

    @property
    def projection_matrix_hash(self) -> str:
        """ Returns a hash of :attr:`projection_matrix`.
        """
        return list_to_hash([self.projection_matrix])

    def __str__(self) -> str:
        wdt = 74
        s = [self.__class__.__name__]
        s += ['-' * wdt]
        s += [''.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, edgeitems=2, precision=5, linewidth=60):
            s += ['{:18} : {}'.format('number of directions', len(self))]
            s += ['{:18} : {}'.format('grid_hash', self.grid_hash[:6])]
            s += ['{:18} : {}'.format('enforce_friedel_symmetry', self.enforce_friedel_symmetry)]
            s += ['{:18} : {}'.format('projection_matrix_hash', self.projection_matrix_hash[2:8])]
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
            s += ['<tr><td style="text-align: left;">grid_hash</td>']
            s += [f'<td>{len(self.grid_hash)}</td><td>{self.grid_hash[:6]}</td></tr>']
            s += ['<tr><td style="text-align: left;">enforce_friedel_symmetry</td>']
            s += [f'<td>1</td>'
                  f'<td>{self.enforce_friedel_symmetry}</td></tr>']
            s += ['<tr><td style="text-align: left;">projection_matrix</td>']
            s += [f'<td>{len(self.projection_matrix_hash)}</td>'
                  f'<td>{self.projection_matrix_hash[:6]}</td></tr>']
            s += ['<tr><td style="text-align: left;">hash</td>']
            s += [f'<td>{len(hex(hash(self)))}</td><td>{hex(hash(self))[2:8]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
