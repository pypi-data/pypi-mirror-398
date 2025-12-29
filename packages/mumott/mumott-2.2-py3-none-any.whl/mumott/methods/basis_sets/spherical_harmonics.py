import logging
from typing import Any, Iterator, List, Tuple

import numpy as np

from scipy.special import factorial

try:
    from scipy.special import assoc_legendre_p

    def legendre(n, m, z):
        # Get rid of extra dimension
        return assoc_legendre_p(n, m, z)[0]
except ImportError:
    from scipy.special import lpmv

    def legendre(n, m, z):
        # Call signature compatibility
        return lpmv(m, n, z)

from mumott import ProbedCoordinates
from mumott.core.hashing import list_to_hash
from mumott.methods.utilities.tensor_operations import (framewise_contraction,
                                                        framewise_contraction_transpose)
from mumott.output_handling.reconstruction_derived_quantities import\
    (ReconstructionDerivedQuantities, get_sorted_eigenvectors)
from .base_basis_set import BasisSet


logger = logging.getLogger(__name__)


class SphericalHarmonics(BasisSet):
    """ Basis set class for spherical harmonics, the canonical representation
    of polynomials on the unit sphere and a simple way of representing
    band-limited spherical functions which allows for easy computations of statistics
    and is suitable for analyzing certain symmetries.

    Parameters
    ----------
    ell_max : int
        The bandlimit of the spherical functions that you want to be able to represent.
        A good rule of thumb is that :attr:`ell_max` should not exceed the
        number of detector segments minus 1.
    probed_coordinates : ProbedCoordinates
        Optional. A container with the coordinates on the sphere probed at each detector segment by the
        experimental method. Its construction from the system geometry is method-dependent.
        By default, an empty instance of
        :class:`ProbedCoordinates <mumott.core.probed_coordinates.ProbedCoordinates>` is created.
    enforce_friedel_symmetry : bool
        If set to ``True``, Friedel symmetry will be enforced, using the assumption that points
        on opposite sides of the sphere are equivalent. This results in only even ``ell`` being used.
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
                 is considered converged. Default is ``1e-5``.
            integration_maxiter
                 Maximum number of iterations. Default is ``10``.
    """

    def __init__(self,
                 probed_coordinates: ProbedCoordinates = None,
                 ell_max: int = 0,
                 enforce_friedel_symmetry: bool = True,
                 **kwargs):
        super().__init__(probed_coordinates, **kwargs)
        self._probed_coordinates_hash = hash(self.probed_coordinates)
        self._ell_max = ell_max
        self._ell_indices = np.zeros(1)
        self._emm_indices = np.zeros(1)
        # Compute initial values for indices and matrix.
        self._enforce_friedel_symmetry = enforce_friedel_symmetry
        self._calculate_coefficient_indices()
        self._projection_matrix = self._get_integrated_projection_matrix()

    def _calculate_coefficient_indices(self) -> None:
        """
        Computes the attributes :attr:`~.SphericalHarmonics.ell_indices` and
        :attr:`~.SphericalHarmonics.emm_indices`. Called when :attr:`~.SphericalHarmonics.ell_max`
        changes.
        """
        if self._enforce_friedel_symmetry:
            divisor = 2
        else:
            divisor = 1

        mm = np.zeros((self._ell_max + 1) * (self._ell_max // divisor + 1), dtype=int)
        ll = np.zeros((self._ell_max + 1) * (self._ell_max // divisor + 1), dtype=int)
        count = 0
        for h in range(0, self._ell_max + 1, divisor):
            for i in range(-h, h + 1):
                ll[count] = h
                mm[count] = i
                count += 1
        self._ell_indices = ll
        self._emm_indices = mm

    @staticmethod
    def _sph_harm(emms: np.ndarray[int], ells: np.ndarray[int],
                  azimuthal_angles: np.ndarray[float],
                  z: np.ndarray[float]):
        """
        Internal function for computing spherical harmonics using the z-coordinates from
        :attr:`~.SphericalHarmonics.probed_coordinates`.
        """
        legendre_part = legendre(ells, emms, z)
        norm = np.sqrt(((2 * ells + 1) / (4 * np.pi)) * (factorial(ells - emms) / factorial(ells + emms)))
        phase = np.exp(1j * emms * azimuthal_angles)
        return legendre_part * norm * phase

    def _get_projection_matrix(self, probed_coordinates: ProbedCoordinates = None) -> None:
        """ Computes the matrix necessary for forward and gradient calculations.
        Called when the coordinate system has been updated or ``ell_max`` has changed."""
        if probed_coordinates is None:
            probed_coordinates = self._probed_coordinates
        _, _, probed_azim_angles = probed_coordinates.to_spherical
        # retrieve complex spherical harmonics with emm >= 0, shape (N, M, len(ell_indices), K)
        complex_factors = self._sph_harm(abs(self._emm_indices)[np.newaxis, np.newaxis, np.newaxis, ...],
                                         self._ell_indices[np.newaxis, np.newaxis, np.newaxis, ...],
                                         probed_azim_angles[..., np.newaxis],
                                         probed_coordinates.vector[..., 2, np.newaxis])
        # cancel Condon-Shortley phase factor in scipy.special.sph_harm
        condon_shortley_factor = (-1.) ** self._emm_indices
        # 4pi normalization factor and complex-to-real normalization factor for m != 0
        norm_factor = np.sqrt(4 * np.pi) * \
            np.sqrt(1 + (self._emm_indices != 0).astype(int)) * condon_shortley_factor
        matrix = norm_factor[np.newaxis, np.newaxis, np.newaxis, ...] * (
            (self._emm_indices >= 0)[np.newaxis, np.newaxis, np.newaxis, ...] * complex_factors.real +
            (self._emm_indices < 0)[np.newaxis, np.newaxis, np.newaxis, ...] * complex_factors.imag)
        return matrix

    def forward(self,
                coefficients: np.array,
                indices: np.array = None) -> np.array:
        """ Carries out a forward computation of projections from spherical harmonic space
        into detector space, for one or several tomographic projections.

        Parameters
        ----------
        coefficients
            An array of coefficients, of arbitrary shape so long as the last
            axis has the same size as :attr:`~.SphericalHarmonics.ell_indices`, and if
            :attr:`indices` is `None` or greater than one, the first axis should have the
            same length as :attr:`indices`
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

        Notes
        -----
        The assumption is made in this implementation that computations over several
        indices act on sets of images from different projections. For special usage
        where multiple projections of entire fields is desired, it may be better
        to use :attr:`projection_matrix` directly. This also applies to
        :meth:`gradient`.
        """
        assert coefficients.shape[-1] == self._ell_indices.size
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
                 coefficients: np.array,
                 indices: np.array = None) -> np.array:
        """ Carries out a gradient computation of projections from spherical harmonic space
        into detector space, for one or several tomographic projections.

        Parameters
        ----------
        coefficients
            An array of coefficients (or residuals) of arbitrary shape so long as the last
            axis has the same size as the number of detector segments.
        indices
            Optional. Indices of the tomographic projections for which the gradient
            computation is to be performed. If ``None``, the gradient computation will
            be performed for all projections.

        Returns
        -------
            An array of gradient values based on the `coefficients` given.
            If :attr:`indices` contains exactly one index, the shape is ``(coefficients.shape[:-1], J)``
            where ``J`` is the number of detector segments. If indices is ``None`` or contains
            several indices, the shape is ``(N, coefficients.shape[1:-1], J)`` where ``N``
            is the number of tomographic projections for which the computation is performed.

        Notes
        -----
        When solving an inverse problem, one should not to attempt to optimize the
        coefficients directly using the ``gradient`` one obtains by applying this method to the data.
        Instead, one must either take the gradient of the residual between the
        :meth:`~.SphericalHarmonics.forward` computation of the coefficients and the data.
        Alternatively one can apply both the forward and the gradient computation to the
        coefficients to be optimized, and the gradient computation to the data, and treat
        the residual of the two as the gradient of the optimization coefficients. The approaches
        are algebraically equivalent, but one may be more efficient than the other in some
        circumstances.
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

    def get_inner_product(self,
                          u: np.array,
                          v: np.array,
                          resolve_spectrum: bool = False,
                          spectral_moments: List[int] = None) -> np.array:
        r""" Retrieves the inner product of two coefficient arrays.

        Notes
        -----
            The canonical inner product in a spherical harmonic representation
            is :math:`\sum_\ell N(\ell) \sum_m u_m^\ell v_m^\ell`, where :math:`N(\ell)` is
            a normalization constant (which is unity for the :math:`4\pi` normalization).
            This inner product is a rotational invariant. The rotational invariance also holds
            for any partial sums over :math:`\ell`.
            One can define a function of :math:`\ell` that returns such
            products, namely :math:`S(\ell, u, v) = N(\ell)\sum_m u_m^\ell v_m^\ell`,
            called the spectral power function.
            The sum :math:`\sum_{\ell = 1}S(\ell)` is equal to the covariance of the
            band-limited spherical functions represented by :math:`u` and :math:`v`, and each
            :math:`S(\ell, u, v)` is the contribution to the covariance of the band :math:`\ell`.
            See also
            `the SHTOOLS documentation <https://shtools.github.io/SHTOOLS/real-spherical-harmonics.html>`_
            for an excellent overview of this.

        Parameters
        ----------
        u
            The first coefficient array, of arbitrary shape and dimension,
            except the last dimension must be the same as the length of
            :attr:`~.SphericalHarmonics.ell_indices`.
        v
            The second coefficient array, of the same shape as ``u``.
        resolve_spectrum
            Optional. Whether to resolve the product according to each frequency band, given by the
            coefficients of each ``ell`` in :attr:`~SphericalHarmonics.ell_indices`.
            Defaults to ``False``, which means that the sum of every component of the spectrum is returned.
            If ``True``, components are returned in order of ascending ``ell``.
            The ``ell`` included in the spectrum depends on :attr:`spectral_moments`.
        spectral_moments
            Optional. List of particular values of ``ell`` to calculate the inner product for.
            Defaults to ``None``, which is identical to including all values of ``ell``
            in the calculation.
            If :attr:`spectral_moments` contains all nonzero values of ``ell`` and
            :attr:`resolve_spectrum` is ``False``, the covariance of
            :attr:`v` and :attr:`u` will be calculated (the sum of the inner product over all non-zero ``ell``
            If ``resolve_spectrum`` is ``True``, the covariance per `ell` in ``spectral_moments``, will
            be calculated, i.e., the inner products will not be summed over.

        Returns
        -------
            An array of the inner products of the spherical functions represented by ``u`` and ``v``.
            Has the shape ``(u.shape[:-1])`` if :attr:`resolve_spectrum` is ``False``,
            ``(u.shape[:-1] + (ell_max // 2 + 1,))`` if :attr:`resolve_spectrum` is ``True`` and
            ``spectral_moments`` is ``None``, and finally the shape
            ``(u.shape[:-1] + (np.unique(spectral_moments).size,))`` if :attr:`resolve_spectrum` is ``True``
            and :attr:`spectral_moments` is a list of integers found
            in :attr:`~.SphericalHarmonics.ell_indices`
         """
        assert u.shape == v.shape
        assert u.shape[-1] == self._ell_indices.size
        if not resolve_spectrum:
            if spectral_moments is None:
                return np.einsum('...i, ...i -> ...', u, v)
            # pick out only the subset where ell matches the provided spectral moments
            where = np.any([np.equal(self._ell_indices, ell) for ell in spectral_moments], axis=0)
            return np.einsum('...i, ...i -> ...', u[..., where], v[..., where])
        if spectral_moments is None:
            which_ell = np.unique(self._ell_indices)
        else:
            which_ell = np.unique(spectral_moments)
            which_ell = [ell for ell in which_ell if np.any(np.equals(self._ell_indices, ell))]
        power_spectrum = np.zeros((*u.shape[:-1], which_ell.size))
        # power spectrum for any one ell is given by inner product over each ell
        for i, ell in enumerate(which_ell):
            power_spectrum[..., i] = np.einsum('...i, ...i -> ...',
                                               u[..., self._ell_indices == ell],
                                               v[..., self._ell_indices == ell],
                                               optimize='greedy')
        return power_spectrum

    def get_covariances(self,
                        u: np.array,
                        v: np.array,
                        resolve_spectrum: bool = False) -> np.array:
        """ Returns the covariances of the spherical functions represented by
        two coefficient arrays.

        Parameters
        ----------
        u
            The first coefficient array, of arbitrary shape
            except its last dimension must be the same length as
            the length of :attr:`~SphericalHarmonics.ell_indices`.
        v
            The second coefficient array, of the same shape as :attr:`u`.
        resolve_spectrum
            Optional. Whether to resolve the product according to each frequency band, given by the
            coefficients of each ``ell`` in :attr:`~.SphericalHarmonics.ell_indices`.
            Default value is ``False``.

        Returns
        -------
            An array of the covariances of the spherical functions represented by ``u`` and ``v``.
            Has the shape ``(u.shape[:-1])`` if `resolve_spectrum` is ``False``, and
            ``(u.shape[:-1] + (ell_max // 2 + 1,))`` if `resolve_spectrum` is ``True``, where
            ``ell_max`` is :attr:`.SphericalHarmonics.ell_max`.

        Notes
        -----
        Calling this function is equivalent to calling :func:`~.SphericalHarmonics.get_inner_product`
        with ``spectral_moments=np.unique(ell_indices[ell_indices > 0])`` where ``ell_indices`` is
        :attr:`.SphericalHarmonics.ell_indices`. See the note to
        :func:`~.SphericalHarmonics.get_inner_product` for mathematical details.
        """
        spectral_moments = np.unique(self._ell_indices[self._ell_indices > 0])
        return self.get_inner_products(u, v, resolve_spectrum, spectral_moments)

    def get_output(self,
                   coefficients: np.array) -> ReconstructionDerivedQuantities:
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

        mean_intensity = coefficients[..., 0]
        second_moment_tensor = self._get_rank2_tensor(coefficients)
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

    def get_spherical_harmonic_coefficients(
            self,
            coefficients: np.array,
            ell_max: int = None) -> np.array:
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
            raise ValueError(f'The number of coefficients ({coefficients.shape[-1]}) does not '
                             f'match the expected value. ({len(self)})')

        if self._enforce_friedel_symmetry:
            num_coeff_output = (ell_max+1) * (ell_max+2) // 2
        elif not self._enforce_friedel_symmetry:
            num_coeff_output = (ell_max+1)**2

        output_array = np.zeros((*coefficients.shape[:-1], num_coeff_output))
        output_array[..., :min(len(self), num_coeff_output)] = \
            coefficients[..., :min(len(self), num_coeff_output)]
        return output_array

    def _get_rank2_tensor(self, coefficients: np.array(float)) -> np.array(float):
        """ Computes the second moments of the reciprocal space maps
        represented by `coefficients`.

        Parameters
        ----------
        coefficients
            An array of coefficients of arbitrary shape, as long as the last axis has the same shape
            as :attr:`~.SphericalHarmonics.ell_indices`.

        Returns
        -------
            First, the 2nd moment tensors of all the functions represented by the :attr:`coefficients`,
            in 3-by-3 matrix form stored in the last two indices:
            ``[[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]]``
        """
        r2_tensor = coefficients[..., 0, np.newaxis, np.newaxis]\
            * np.eye(3)[np.newaxis, np.newaxis, np.newaxis, :, :] * 1/3

        if self._ell_max < 2:
            logger.info('Note: ell_max < 2, so rank-2 tensors will all be diagonal matrices.')
            return r2_tensor

        r2_tensor[..., 0, 1] = coefficients[..., 1] / np.sqrt(15)
        r2_tensor[..., 1, 0] = coefficients[..., 1] / np.sqrt(15)
        r2_tensor[..., 1, 2] = coefficients[..., 2] / np.sqrt(15)
        r2_tensor[..., 2, 1] = coefficients[..., 2] / np.sqrt(15)
        r2_tensor[..., 2, 2] += coefficients[..., 3] * 2 * np.sqrt(5) / 15
        r2_tensor[..., 0, 0] += -coefficients[..., 3] * np.sqrt(5) / 15 + coefficients[..., 5] / np.sqrt(15)
        r2_tensor[..., 1, 1] += -coefficients[..., 3] * np.sqrt(5) / 15 - coefficients[..., 5] / np.sqrt(15)
        r2_tensor[..., 0, 2] = coefficients[..., 4] / np.sqrt(15)
        r2_tensor[..., 2, 0] = coefficients[..., 4] / np.sqrt(15)

        return r2_tensor

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """ Allows class to be iterated over and in particular be cast as a dictionary.
        """
        yield 'name', type(self).__name__
        yield 'ell_max', self._ell_max
        yield 'ell_indices', self._ell_indices
        yield 'emm_indices', self._emm_indices
        yield 'projection_matrix', self._projection_matrix
        yield 'hash', hex(hash(self))[2:]

    def __len__(self) -> int:
        return len(self._ell_indices)

    def __hash__(self) -> int:
        """Returns a hash reflecting the internal state of the instance.

        Returns
        -------
            A hash of the internal state of the instance,
            cast as an ``int``.
        """
        to_hash = [self._ell_max,
                   self._ell_indices,
                   self._emm_indices,
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
    def projection_matrix(self) -> np.array:
        """ The matrix used to project spherical functions from the unit sphere onto the detector.
        If ``v`` is a vector of spherical harmonic coefficients, and ``M`` is the ``projection_matrix``,
        then ``M @ v`` gives the corresponding values on the detector segments associated with
        each projection. ``M[i] @ v`` gives the values on the detector segments associated with
        projection ``i``.

        If ``r`` is a residual between a projection from spherical to detector space and data from
        projection ``i``, then ``M[i].T @ r`` gives the associated gradient in spherical harmonic
        space.
        """
        self._update()
        return self._projection_matrix

    @property
    def ell_max(self) -> int:
        r""" The maximum ``ell`` used to represent spherical functions.

        Notes
        -----
        The word ``ell`` is used to represent the cursive small L, also written
        :math:`\ell`, often used as an index for the degree of the Legendre polynomial
        in the definition of the spherical harmonics.
        """
        return self._ell_max

    @ell_max.setter
    def ell_max(self, val: int) -> np.array(int):
        if (val % 2 != 0 and self._enforce_friedel_symmetry) or val < 0 or val != round(val):
            raise ValueError('ell_max must be an even (if Friedel symmetry is enforced),'
                             ' non-negative integer,'
                             f' but a value of {val} was given!')
        self._ell_max = val
        self._calculate_coefficient_indices()
        self._projection_matrix = self._get_integrated_projection_matrix()

    @property
    def ell_indices(self) -> np.ndarray[int]:
        r""" The ``ell`` associated with each coefficient and its corresponding
        spherical harmonic. Updated when :attr:`~.SphericalHarmonics.ell_max` changes.

        Notes
        -----
        The word ``ell`` is used to represent the cursive small L, also written
        :math:`\ell`, often used as an index for the degree of the Legendre polynomial
        in the definition of the spherical harmonics.
        """
        return self._ell_indices

    @property
    def emm_indices(self) -> np.ndarray[int]:
        r""" The ``emm`` associated with each coefficient and its corresponding
        spherical harmonic. Updated when :attr:`~.SphericalHarmonics.ell_max` changes.

        Notes
        -----
        For consistency with :attr:`~.SphericalHarmonics.ell_indices`, and to avoid
        visual confusion with other letters, ``emm`` is
        used to represent the index commonly written :math:`m` in mathematical notation,
        the frequency of the sine-cosine parts of the spherical harmonics,
        often called the spherical harmonic order.
        """
        return self._emm_indices

    def __str__(self) -> str:
        wdt = 74
        s = []
        s += ['-' * wdt]
        s += ['SphericalHarmonics'.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, edgeitems=2, precision=5, linewidth=60):
            s += ['{:18} : {}'.format('Maximum "ell"', self.ell_max)]
            s += ['{:18} : {}'.format('"ell" indices', self.ell_indices)]
            s += ['{:18} : {}'.format('"emm" indices', self.emm_indices)]
            s += ['{:18} : {}'.format('Projection matrix', self.projection_matrix)]
            s += ['{:18} : {}'.format('Hash', hex(hash(self))[2:8])]
        s += ['-' * wdt]
        return '\n'.join(s)

    def _repr_html_(self) -> str:
        s = []
        s += ['<h3>SphericalHarmonics</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th><th>Data</th></tr></thead>']
        s += ['<tbody>']
        with np.printoptions(threshold=4, edgeitems=2, precision=2, linewidth=40):
            s += ['<tr><td style="text-align: left;">Maximum "ell"</td>']
            s += [f'<td>{1}</td><td>{self.ell_max}</td></tr>']
            s += ['<tr><td style="text-align: left;">"ell" indices</td>']
            s += [f'<td>{len(self.ell_indices)}</td><td>{self.ell_indices}</td></tr>']
            s += ['<tr><td style="text-align: left;">"emm" indices</td>']
            s += [f'<td>{len(self.emm_indices)}</td><td>{self.emm_indices}</td></tr>']
            s += ['<tr><td style="text-align: left;">Coefficient projection matrix</td>']
            s += [f'<td>{self.projection_matrix.shape}</td><td>{self.projection_matrix}</td></tr>']
            s += ['<tr><td style="text-align: left;">Hash</td>']
            s += [f'<td>{len(hex(hash(self)))}</td><td>{hex(hash(self))[2:8]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
