import logging

import numpy as np
from numpy.typing import NDArray

from mumott import DataContainer
from mumott.core.wigner_d_utilities import (
    load_d_matrices, calculate_sph_coefficients_rotated_around_z,
    calculate_sph_coefficients_rotated_by_90_degrees_around_positive_x,
    calculate_sph_coefficients_rotated_by_90_degrees_around_negative_x,
    calculate_sph_coefficients_rotated_around_z_derived_wrt_the_angle)
from mumott.core.hashing import list_to_hash
from mumott.methods.projectors.base_projector import Projector
from mumott.methods.basis_sets.spherical_harmonics import SphericalHarmonics
from .base_residual_calculator import ResidualCalculator


logger = logging.getLogger(__name__)


class ZHTTResidualCalculator(ResidualCalculator):
    r"""Class that implements the gradient calculations for a model that uses a
    :class:`SphericalHarmonics` basis set restricted to zonal harmonics parametrized
    by a primary axis with polar coordinates :math:`\theta_0` and :math:`\phi_0`
    ,defined as:

    .. math::

        \begin{pmatrix} x_0\\ y_0\\ z_0\end{pmatrix}
        = \begin{pmatrix}
        \sin(\theta_0) \sin(\phi_0) \\
        \sin(\theta_0) \cos(\phi_0) \\
        \cos(\theta_0)
        \end{pmatrix}

    This model is equivalent to the one used in [Liebi2015]_, but uses a different approach to
    computation.

    This implementation avoids doing some of the expensive calculations of trigonometric functions and
    Legendre polynomials by doing the rotation in the space of the spherical harmonics using
    `Wigner (small) d-matrices <https://en.wikipedia.org/wiki/Wigner_D-matrix>`_.
    The forward model only involves a small number of trigonometric functions to evaluate the
    :math:`d_z(\text{angle})` matrices for the :math:`\theta` and :math:`\phi` rotations.
    Everything else is expressed as matrix products with precomputed matrices.

    The full forward model may be written as:

    .. math::

        \boldsymbol{I} =
        \boldsymbol{W} \boldsymbol{P}
        \boldsymbol{d}_z(\phi_0) \boldsymbol{d}_y(\frac{\pi}{4})^T
        \boldsymbol{d}_z(-\theta_0) \boldsymbol{d}_y(\frac{\pi}{4})
        \boldsymbol{a}'_{l0},

    where :math:`\boldsymbol{W}` is the mapping from spherical harmonic modes to detector segments,
    which can be precomputed.
    :math:`\boldsymbol{P}` is the typical projector from normal 3D tomography and
    :math:`\boldsymbol{d}_i(\text{angle})` with :math:`i = x,y,z`  are Wigner (small) d matrices
    for real spherical harmonics. :math:`\theta_0`, :math:`\phi_0`, and :math:`\boldsymbol{a}_{l0}`
    are the model parameters for each voxel.

    Derivatives are easy to evaluate because the angles only appear in the
    :math:`\boldsymbol{d}_z(\text{angle})`-matrices. All the expensive trigonometric and spherical
    harmonics calculations have been put into the precomputation of :math:`\boldsymbol{W}`
    and :math:`\boldsymbol{d}_y(\frac{\pi}{4})`.

    Parameters
    ----------
    data_container : DataContainer
        Container holding the data to be reconstructed.
    basis_set : SphericalHarmonics
        The basis set used for representing spherical functions.
    projector : Projector
        The type of projector used together with this method.
    """
    def __init__(self,
                 data_container: DataContainer,
                 basis_set: SphericalHarmonics,
                 projector: Projector):
        super().__init__(data_container, basis_set, projector)
        self._make_matrices()
        self._make_starting_guess()

    def _make_starting_guess(self) -> None:
        """Initializes the optimization parameters by setting the
        zonal coefficients to zero and randomizing the angles, which
        corresponds to sampling directions uniformly on the unit
        sphere.
        """
        volume_shape = self._projector.volume_shape
        self._zonal_coefficients = np.zeros((*volume_shape, self._basis_set.ell_max // 2 + 1))

        # Make random orientations by random sampling in 3D
        rng = np.random.default_rng()
        self._theta = np.arccos(rng.uniform(low=0, high=1, size=volume_shape))
        self._phi = rng.uniform(low=-np.pi, high=np.pi, size=volume_shape)

    def _make_matrices(self) -> None:
        """
        Loads Wigner d-matrices and creates the mapping from parameters
        to spherical harmonics coefficients.
        """
        # Load precomputed d-matrices
        ell_max = self._basis_set.ell_max
        self.d_matrices = load_d_matrices(ell_max)

        # Set up matrix for converting from zonal harmonics to full harmonics space
        ell_list = self._basis_set.ell_indices
        m_list = self._basis_set.emm_indices
        self._E = np.zeros((len(ell_list), ell_max//2+1))
        for full_index, (ell, m) in enumerate(zip(ell_list, m_list)):
            if m == 0:
                self._E[full_index, ell//2] = 1

    @property
    def coefficients(self) -> NDArray:
        """Optimization coefficients for this method.
        Contains both the zonal coefficients and the angles.
        The first N-2 elements are zonal coefficients.
        The N-1th element is the polar angle and the last element is the azimuthal angle.
        """
        self._cast_angles_to_symmetric_zone()
        return np.concatenate((self._zonal_coefficients,
                               self._theta[..., np.newaxis],
                               self._phi[..., np.newaxis]), axis=3)

    @coefficients.setter
    def coefficients(self, val: NDArray) -> None:
        # Convert from external to internal representation of optimization parameters
        val = val.reshape((*self._projector.volume_shape, self._basis_set.ell_max // 2 + 1 + 2))
        assert np.shape(val[..., :-2]) == np.shape(self._zonal_coefficients), \
            'Shape of new array inconsistent with expectation (zonal_coefficients)'
        assert np.shape(val[..., -2]) == np.shape(self._theta), \
            'Shape of new array inconsistent with expectation (theta)'
        assert np.shape(val[..., -1]) == np.shape(self._phi), \
            'Shape of new array inconsistent with expectation (phi)'
        self._zonal_coefficients = val[..., :-2]
        self._theta = val[..., -2]
        self._phi = val[..., -1]

    def _rotate_coeffs(self) -> NDArray:
        """Expand from the zonal harmonics basis to a full spherical harmonics basis and
        rotate the spherical harmonics coefficients from the symmetric coordinate system
        to the sample xyz system.

        Returns
        -------
            Array containing the rotated spherical harmonics coefficients.
        """
        ell_list = np.arange(0, self._basis_set.ell_max + 1, 2)
        # Expand symmetric coefficients into full basis
        self._coefficients = np.einsum('...i,ji->...j', self._zonal_coefficients, self._E)
        # Rotate by 90 degrees about x
        calculate_sph_coefficients_rotated_by_90_degrees_around_positive_x(
            self._coefficients, ell_list, self.d_matrices, output_array=self._coefficients)
        # Rotate by theta about z
        calculate_sph_coefficients_rotated_around_z(
            self._coefficients, self._theta, ell_list, output_array=self._coefficients)
        # Rotate by -90 degrees about x
        calculate_sph_coefficients_rotated_by_90_degrees_around_negative_x(
            self._coefficients, ell_list, self.d_matrices, output_array=self._coefficients)
        # Rotate by phi about z
        calculate_sph_coefficients_rotated_around_z(
            self._coefficients, self._phi, ell_list, output_array=self._coefficients)
        return self._coefficients

    def _rotate_and_derive(self):
        """
        Rotate spherical harmonics coefficients from the symmetric coordinate system
        to the sample xyz system and evaluate the derivative of the coefficients
        with respect to the two rotation angles.

        Returns
        ----------
        self._coefficients : NDArray
            Array containing the rotated spherical harmonics coefficients.
        theta_derivative : NDArray
            Rotated spherical coefficients derived with respect to the polar rotation angle
            evaluated at the current value of the rotation angles.
        phi_derivative : NDArray
            Rotated spherical coefficients derived with respect to the azimuthal rotation angle
            evaluated at the current value of the rotation angles.
        """

        ell_list = np.arange(0, self._basis_set.ell_max+1, 2)
        # Expand symmetric coefficients into full basis
        self._coefficients = np.einsum('...i,ji->...j', self._zonal_coefficients, self._E)
        theta_derivative = np.zeros((*self._projector.volume_shape, len(self._basis_set)))
        phi_derivative = np.zeros((*self._projector.volume_shape, len(self._basis_set)))

        # Do 90 degree rotation around x
        calculate_sph_coefficients_rotated_by_90_degrees_around_positive_x(
            self._coefficients, ell_list, self.d_matrices, output_array=self._coefficients)

        # Do z rotation of Theta and derivative
        calculate_sph_coefficients_rotated_around_z_derived_wrt_the_angle(
            self._coefficients, self._theta, ell_list, output_array=theta_derivative)
        calculate_sph_coefficients_rotated_around_z(
            self._coefficients, self._theta, ell_list, output_array=self._coefficients)

        # Do -90 degree rotation around x
        calculate_sph_coefficients_rotated_by_90_degrees_around_negative_x(
            self._coefficients, ell_list, self.d_matrices, output_array=self._coefficients)
        calculate_sph_coefficients_rotated_by_90_degrees_around_negative_x(
            theta_derivative, ell_list, self.d_matrices, output_array=theta_derivative)

        # Do z rotation of Phi
        calculate_sph_coefficients_rotated_around_z_derived_wrt_the_angle(
            self._coefficients, self._phi, ell_list, output_array=phi_derivative)
        calculate_sph_coefficients_rotated_around_z(
            self._coefficients, self._phi, ell_list, output_array=self._coefficients)
        calculate_sph_coefficients_rotated_around_z(
            theta_derivative, self._phi, ell_list, output_array=theta_derivative)

        return self._coefficients, theta_derivative, phi_derivative

    def _rotate_coeffs_inverse(self, coefficients: NDArray):
        """
        Rotate spherical harmonics coefficients from the sample xyz system
        to the symmetric coordinate system.
        """
        ell_list = np.arange(0, self._basis_set.ell_max+1, 2)

        # Do z rotation of -phi
        calculate_sph_coefficients_rotated_around_z(
            coefficients, -self._phi, ell_list, output_array=coefficients)

        # Do 90 degree rotation around x
        calculate_sph_coefficients_rotated_by_90_degrees_around_positive_x(
            coefficients, ell_list, self.d_matrices, output_array=coefficients)

        # Do z rotation of -theta
        calculate_sph_coefficients_rotated_around_z(
            coefficients, -self._theta, ell_list, output_array=coefficients)

        # Do -90 degree rotation around x
        calculate_sph_coefficients_rotated_by_90_degrees_around_negative_x(
            coefficients, ell_list, self.d_matrices, output_array=coefficients)

        return coefficients

    def get_residuals(self,
                      get_gradient: bool = False,
                      get_weights: bool = False,
                      gradient_part: str = 'full') -> dict[str, NDArray[float]]:
        """ Calculates the residuals and possibly the gradient of the residual square sum
        (without the factor of -2!) with respect to the parameters.
        The coefficients are projected using the :attr:`SphericalHarmonics` and :attr:`Projector`
        attached to this instance.

        Parameters
        ----------
        get_gradient
            Whether to return the gradient. Default is ``False``.
        get_weights
            Whether to return weights. Default is ``False``. If ``True`` along with
            :attr:`get_gradient`, the gradient will be computed with weights.
        gradient_part
            If :attr:`gradient_part` is ``'full'`` (Default) the gradient is computed with respect to all
            parameters;
            if :attr:`gradient_part` is ``'angles'`` only the gradient with respect to the angles is computed;
            if :attr:`gradient_part` is ``'coefficients'`` only the gradient with respect to the zonal
            spherical harmonics coefficients is computed.

        Returns
        -------
            A dictionary containing the residuals, and possibly the
            gradient and/or weights. If gradient and/or weights
            are not returned, their value will be ``None``.
        """

        if not get_gradient:
            # Rotate the coefficients
            self._rotate_coeffs()
            # Project from voxel to detector space and from coefficient to angle space
            projection = self._basis_set.forward(
                self._projector.forward(self._coefficients.astype(self.dtype)))
            # Calculate residuals
            residuals = self._data - projection
            if get_weights:
                residuals *= self._weights
            output = {'residuals': residuals, 'gradient': None}

        elif get_gradient:
            output = self.get_gradient(get_weights=get_weights)

        # Pass on weights, if asked to
        if get_weights:
            output['weights'] = self._weights
        else:
            output['weights'] = None

        return output

    def get_gradient(self,
                     get_weights: bool = False,
                     gradient_part: str = 'full') -> dict[str, NDArray[float]]:
        """ Calculates the gradient of *half* the sum of residuals squared.

        Parameters
        ----------
        get_gradient
            Whether to return the gradient. Default is ``False``.
        gradient_part
            If :attr:`gradient_part` is ``'full'`` (Default) the gradient is computed with respect to all
            parameters;
            if :attr:`gradient_part` is ``'angles'`` only the gradient with respect to the angles is computed;
            if :attr:`gradient_part` is ``'coefficients'`` only the gradient with respect to the zonal
            spherical harmonics coefficients is computed.

        Returns
        -------
            A dictionary containing the residuals of the gradient. If only a part of the
            gradient is computed, the rest of the elements will be filled with zeros.
        """
        # initialize output array
        gradient = np.zeros((*self._projector.volume_shape, self._basis_set.ell_max // 2 + 3))

        # If only the coefficients are needed, do not evaluate the derivatives.
        if gradient_part == 'coefficients':
            coefficients = self._rotate_coeffs()
        else:
            coefficients, theta_derivative, phi_derivative = self._rotate_and_derive()

        # Project from voxel to detector space and the from coeff-space to angle-space
        projection = self._basis_set.forward(self._projector.forward(coefficients.astype(self.dtype)))
        # Calculate residuals
        residuals = self._data - projection
        if get_weights:
            residuals *= self._weights
        # Backproject residual
        bp_res = self._projector.adjoint(
                    self._basis_set.gradient(residuals).astype(self.dtype))

        # If the gradient with respect to angles is needed, compute the inner products
        if gradient_part in ['full', 'angles']:
            gradient[:, :, :, -2] = -np.einsum('xyzm,xyzm->xyz', bp_res, theta_derivative)
            gradient[:, :, :, -1] = -np.einsum('xyzm,xyzm->xyz', bp_res, phi_derivative)

        if gradient_part == 'full' or gradient_part == 'coefficients':
            # back-rotate coefficients
            bp_res = self._rotate_coeffs_inverse(bp_res)
            gradient[..., :-2] += -np.einsum('...i,ij->...j', bp_res, self._E)

        return {'residuals': residuals, 'gradient': gradient}

    def _cast_angles_to_symmetric_zone(self):
        r"""
        Casts internal angle arrays into the range :math:`\theta \in [0, \phi/2[` and
        :math:`\phi \in [0, 2\phi[`.
        """
        self._theta = self._theta % np.pi
        southern_hemisphere = self._theta > (np.pi / 2)
        self._theta[southern_hemisphere] = np.pi - self._theta[southern_hemisphere]
        self._phi[southern_hemisphere] = self._phi[southern_hemisphere] + np.pi
        self._phi = self._phi % (2 * np.pi)

    @property
    def rotated_coefficients(self):
        """
        Returns the real spherical harmonics coefficients.
        """
        return self._rotate_coeffs()

    @property
    def directions(self):
        """
        Returns the direction of symmetry as a unit vector in in xyz coordinates.
        The vector index is the last index of the output.
        """
        # Make unit direction vectors
        directions = np.stack((np.cos(self._phi)*np.sin(self._theta),
                               np.sin(self._phi)*np.sin(self._theta),
                               np.cos(self._phi)), axis=-1)
        return directions

    @property
    def ell_max(self) -> int:
        """l max"""
        return self._basis_set.ell_max

    @property
    def volume_shape(self) -> int:
        """Shape of voxel volume"""
        return self._projector.volume_shape

    def _update(self, force_update: bool = False) -> None:
        """ Carries out necessary updates if anything changes with respect to
        the geometry or basis set."""
        if not (self.is_dirty or force_update):
            return
        self._basis_set.probed_coordinates = self.probed_coordinates

        # See ell_max changed
        old_ellmax = (self._zonal_coefficients.shape[-1] - 1) * 2
        old_num_coeffs = (old_ellmax + 1) * (old_ellmax + 2) // 2
        len_diff = len(self._basis_set) - old_num_coeffs

        vol_diff = self._data_container.geometry.volume_shape - np.array(self._coefficients.shape[:-1])
        # TODO: Think about whether the ``Method`` should do this or handle it differently
        if len_diff != 0 and not np.any(vol_diff != 0):
            logger.warning('ell_max has changed. Coefficients will be truncated or appended with zeros.')
            self._make_matrices()

            old_params = np.array(self._zonal_coefficients)
            self._zonal_coefficients = np.zeros((*self._projector.volume_shape,
                                                 self._basis_set.ell_max // 2 + 1))
            if len_diff > 0:
                self._zonal_coefficients[:, :, :, :old_params.shape[-1]] = old_params
                self._coefficients = np.zeros((*self._data_container.geometry.volume_shape,
                                               len(self._basis_set)), dtype=self.dtype)
            if len_diff < 0:
                self._zonal_coefficients = old_params[:, :, :, :self._zonal_coefficients.shape[-1]]
                self._coefficients = np.zeros((*self._data_container.geometry.volume_shape,
                                               len(self._basis_set)), dtype=self.dtype)

        elif np.any(vol_diff != 0):
            logger.warning('Volume shape has changed.'
                           ' Coefficients have been reset to zero and angles have been randomized.')
            self._make_matrices()
            self._random_starting_guess()

        self._geometry_hash = hash(self._data_container.geometry)
        self._basis_set_hash = hash(self._basis_set)

    def __hash__(self) -> int:
        """ Returns a hash of the current state of this instance. """
        to_hash = [self._zonal_coefficients,
                   self._theta,
                   self._phi,
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
                                      hex(hash(self.probed_coordinates))[2:8])]
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
                  f'<td>{hex(hash(self.probed_coordinates))[2:8]} (hash)</td></tr>']
            s += ['<tr><td style="text-align: left;">Hash</td>']
            h = hex(hash(self))
            s += [f'<td>{len(h)}</td><td>{h[2:8]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
