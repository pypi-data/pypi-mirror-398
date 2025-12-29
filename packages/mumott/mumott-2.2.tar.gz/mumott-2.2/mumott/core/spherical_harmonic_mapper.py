""" Container for class SphericalHarmonicMapper. """
import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation as rot
from scipy.special import sph_harm, factorial2
from typing import Tuple


class SphericalHarmonicMapper:
    """
    Helper class for visualizing and analyzing spherical harmonics.
    Using this class, one can obtain the amplitudes for a given set
    of even-ordered harmonics and apply the Funk-Radon transform.
    These can then be plotted, analyzed, and so forth. In addition, the class
    allows one to represent functions in terms of spherical harmonics,
    if they are given as functions of the azimuthal and polar angles
    of the class instance.

    Parameters
    ----------
    ell_max : int, optional
        Maximum order of the spherical harmonics. Default is ``2``.
    polar_resolution : int, optional
        Number of samples in the polar direction. Default is ``16``.
    azimuthal_resolution : int, optional
        Number of samples in the azimuthal direction. Default is ``32``.
    polar_zero : float, optional
        The polar angle of the spherical harmonic coordinate system's
        pole, relative to the reference coordinate system. Default is ``0``.
    azimuthal_zero : float, optional
        The azimuthal angle of the spherical harmonic coordinate system's
        pole, relative to a reference coordinate system. Default is ``0``.
    enforce_friedel_symmetry : bool
        If set to ``True``, Friedel symmetry will be enforced, using the assumption that points
        on opposite sides of the sphere are equivalent.

    Example
    -------
        >>> import numpy as np
        >>> import matplotlib.pyplot as plt
        >>> S = SphericalHarmonicMapper(ell_max=4, polar_resolution=16, azimuthal_resolution=8)
        >>> S.ell_indices
        array([0, 2, 2, 2, 2, 2, 4, 4, ...])
        >>> S.emm_indices
        array([ 0, -2, -1,  0,  1,  2, -4, -3, ...])
        >>> a = S.get_amplitudes(np.random.rand(S.ell_indices.size) - 0.5)
        >>> plt.pcolormesh(S.phi * np.sqrt(1 / 2), # basic cylindrical equal-area projection
                           np.cos(S.theta) / np.sqrt(1 / 2),
                           a[:-1, :-1])
        ...
    """

    def __init__(self,
                 ell_max: int = 2,
                 polar_resolution: int = 16,
                 azimuthal_resolution: int = 32,
                 polar_zero: float = 0,
                 azimuthal_zero: float = 0,
                 enforce_friedel_symmetry: bool = True):
        self._polar_zero = polar_zero
        self._azimuthal_zero = azimuthal_zero
        self._ell_max = ell_max
        polar_coordinates = np.linspace(0, np.pi, polar_resolution)
        azimuthal_coordinates = np.linspace(-np.pi, np.pi, azimuthal_resolution + 1)[:-1]
        self._theta, self._phi = np.meshgrid(
            polar_coordinates,
            azimuthal_coordinates,
            indexing='ij')
        self._enforce_friedel_symmetry = enforce_friedel_symmetry
        self._update_l_and_m()

        self._map = np.zeros(self._theta.shape + self._ell_indices.shape)
        self._complex_map = np.zeros(self._theta.shape + self._ell_indices.shape).astype(complex)
        self._update_map()

        self._rotated_system = True
        self._get_coordinates()
        self._update_funk_coefficients()

        self._xyz = np.concatenate((self._X[..., None], self._Y[..., None], self._Z[..., None]), axis=2)
        self.update_zeros(self._polar_zero, self._azimuthal_zero)

    def get_amplitudes(self,
                       coefficients: NDArray[float],
                       apply_funk_transform: bool = False) -> NDArray[float]:
        """
        Returns the amplitudes of a set of spherical harmonics. For sorting
        of the coefficients, see the :attr:`orders` and :attr:`degrees` attributes.

        Parameters
        ----------
        coefficients
            The coefficients for which the amplitudes are to be calculated.
            Size must be equal to ``(ell_max + 1) * (ell_max / 2 + 1)``.
        apply_funk_fransform
            Whether to apply the Funk-Radon transform to the coefficients.
            This is useful for orientation analysis in some cases.
            Default is ``False``.
        """
        if apply_funk_transform:
            coefficients = (self._funk_coefficients * coefficients.ravel()).reshape(1, 1, -1)
        else:
            coefficients = coefficients.reshape(1, 1, -1)
        return np.einsum('...i, ...i', coefficients, self._map)

    def get_harmonic_coefficients(self, amplitude: NDArray[float]) -> NDArray[float]:
        """ Returns the spherical harmonic coefficients for the given amplitudes.
        Can be used with amplitudes from another instance of
        :class:`SphericalHarmonicParameters` with a different orientation
        in order to solve for the rotated coefficients. The accuracy of the
        representation depends on the maximum order and the polar and azimuthal
        resolution.

        Parameters
        ----------
        amplitude
            The amplitude of the spherical function to be
            represented, as a function of ``theta`` and ``phi``.
        """
        assert np.allclose(amplitude.shape[-1:-3:-1], self.theta.shape)
        area_normer = np.sin(self.theta)
        area_normer /= np.sum(area_normer)
        scaled_amp = np.einsum('...ij, ij -> ...ij',
                               amplitude,
                               area_normer, optimize='greedy')
        coeffs = np.einsum('ijk, ...ij -> ...k', self.map, scaled_amp, optimize='greedy')
        return coeffs

    def _get_coordinates(self) -> Tuple[NDArray[float], NDArray[float], NDArray[float]]:
        """ Gets the X, Y, and Z-coordinates. Updates them only if the system has
        been rotated since the last call. """
        if self._rotated_system:
            self._X, self._Y, self._Z = \
                (np.multiply(0.5, np.einsum('..., ...', np.sin(self._theta), np.cos(self._phi))),
                 np.multiply(0.5, np.einsum('..., ...', np.sin(self._theta), np.sin(self._phi))),
                 np.multiply(0.5, np.cos(self._theta)))
            self._rotated_system = False
        return self._X, self._Y, self._Z

    def _update_funk_coefficients(self) -> None:
        """ Updates the Funk coefficients used for the Funk transform. """
        funk_coefficients = []
        for i in range(self._ell_max+1):
            if i % 2 == 0:
                funk_coefficients.append(((-1) ** (i // 2)) * factorial2(i - 1) / factorial2(i))
        funk_coefficients = np.array(funk_coefficients)
        self._funk_coefficients = funk_coefficients[self._ell_indices // 2]

    def _update_l_and_m(self) -> None:
        """ Updates the order and degree vectors of the system. """
        if self._enforce_friedel_symmetry:
            ell_step = 2
        else:
            ell_step = 1
        self._ell_indices = []
        self._emm_indices = []
        for ll in range(0, self._ell_max+1, ell_step):
            for mm in range(-ll, ll+1):
                self._ell_indices.append(ll)
                self._emm_indices.append(mm)
        self._ell_indices = np.array(self._ell_indices)
        self._emm_indices = np.array(self._emm_indices)

    def _update_map(self) -> None:
        """ Updates the map of the system. """
        self._update_complex_map()
        self._update_real_map()

    def _update_complex_map(self) -> None:
        """ Retrieves the complex map used for determining
        the real map. """
        self._complex_map[...] = sph_harm(
            abs(self._emm_indices.reshape(1, 1, -1)),
            self._ell_indices.reshape(1, 1, -1),
            self._phi[:, :, None],
            self._theta[:, :, None])

    def _update_real_map(self) -> None:
        """ Calculates the real spherical harmonic map based on
        the complex map. """
        self._map[:, :, self._emm_indices == 0] = \
            np.sqrt(4 * np.pi) * self._complex_map[:, :, self._emm_indices == 0].real
        self._map[:, :, self._emm_indices > 0] = \
            ((-1.) ** (self._emm_indices[self._emm_indices > 0])) * np.sqrt(2) * \
            np.sqrt(4 * np.pi) * self._complex_map[:, :, self._emm_indices > 0].real
        self._map[:, :, self._emm_indices < 0] = \
            ((-1.) ** (self._emm_indices[self._emm_indices < 0])) * np.sqrt(2) * \
            np.sqrt(4 * np.pi) * self._complex_map[:, :, self._emm_indices < 0].imag

    def update_zeros(self, polar_zero: float, azimuthal_zero: float) -> None:
        """Changes the orientation of the coordinate system.

        Parameters
        ----------
        polar_zero
            The new polar angle at which the pole should be,
            relative to a fixed reference system.
        azimuthal_zero
            The new azimuthal angle at which the pole should be,
            relative to a fixed reference system.
        """
        if polar_zero == 0 and azimuthal_zero == 0:
            self._theta = np.arccos(self._xyz[..., 2] / np.sqrt((self._xyz ** 2).sum(-1)))
            self._phi = np.arctan2(self._xyz[..., 1], self._xyz[..., 0])
            return
        xyz = np.copy(self._xyz)
        xyz = xyz.reshape(-1, 3)
        rotvec = rot.from_euler('Z', (-azimuthal_zero))
        rotvec = rot.from_euler('Y', (-polar_zero)) * rotvec
        xyz = rotvec.apply(xyz).reshape(self._theta.shape + (3,))
        self._theta = np.arccos(xyz[..., 2] / np.sqrt((xyz ** 2).sum(-1)))
        self._phi = np.arctan2(xyz[..., 1], xyz[..., 0])
        self._polar_zero = polar_zero
        self._azimuthal_zero = azimuthal_zero
        self._rotated_system = True
        self._update_map()

    @property
    def unit_vectors(self):
        """ Probed coordinates object used by BasisSets to calculate function maps.
        """
        X, Y, Z = self.coordinates
        vectors = 2 * np.stack((X, Y, Z), axis=-1)  # The mapper uses a sphere of radius 0.5
        return vectors

    @property
    def ell_indices(self) -> NDArray[int]:
        """ The orders of the harmonics calculated
        by the class instance. """
        return self._ell_indices

    @property
    def emm_indices(self) -> NDArray[int]:
        """ The degrees of the harmonics calculated
        by the class instance. """
        return self._emm_indices

    @property
    def polar_zero(self) -> NDArray[float]:
        """ The polar angle of the spherical harmonic pole,
        relative to a fixed reference system. """
        return self._polar_zero

    @property
    def azimuthal_zero(self) -> NDArray[float]:
        """ The azimuthal angle of the spherical harmonic pole,
        relative to a fixed reference system. """
        return self._azimuthal_zero

    @property
    def theta(self) -> NDArray[float]:
        """ The polar angle to which the amplitude is mapped. """
        return self._theta

    @property
    def phi(self) -> NDArray[float]:
        """ The azimuthal angle to which the amplitude is mapped. """
        return self._phi

    @property
    def ell_max(self) -> int:
        """ Maximum order of the spherical harmonics. """
        return self._ell_max

    @property
    def map(self) -> NDArray[float]:
        """ Map between amplitude and harmonics. """
        return self._map

    @property
    def coordinates(self) -> Tuple[NDArray[float], NDArray[float], NDArray[float]]:
        """ The X, Y, Z coordinates that the amplitudes
        are mapped to. """
        return self._get_coordinates()

    @ell_max.setter
    def ell_max(self, new_ell_max: int):
        self._ell_max = new_ell_max
        self._update_l_and_m()
        self._map = np.zeros(self._theta.shape + self._ell_indices.shape)
        self._complex_map = np.zeros(self._theta.shape + self._ell_indices.shape).astype(complex)
        self._update_map()
        self._update_funk_coefficients()
