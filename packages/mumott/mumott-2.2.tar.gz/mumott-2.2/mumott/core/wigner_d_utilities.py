import numpy as np
import importlib.resources
import h5py
import logging
from typing import List
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


def load_d_matrices(ell_max: int) -> List[NDArray[float]]:
    """ Load Wigner (small) d-matrices corresponding to a rotation by 90 degrees
    around the x-axis up to order :attr:`ell_max`.
    The sign and normalization conventions are those adopted throughout :program:`mumott`.

    Parameters
    ----------
    ell_max
        maximum order of the Wigner (small) d-matrices to return

    Returns
    ---------
        list of Wigner (small) d-matrices as numpy arrays with shape ``(l*2+1)x(l*2+1)``
    """
    d_matrices = []
    # Open h5 file
    with importlib.resources.path(__package__, 'wigner_d_matrices.h5') as p:
        path = p

    with h5py.File(path, 'r') as file:
        for ell in range(ell_max + 1):
            d_matrices.append(file[str(ell)][...].T)
    return d_matrices


def calculate_sph_coefficients_rotated_by_90_degrees_around_positive_x(
        input_array: NDArray[float],
        ell_list: List[int],
        d_matrices: List[NDArray[float]],
        output_array: NDArray[float] = None,
        ) -> NDArray[float]:
    r""" Calculate the spherical harmonic coefficients after a rotation by 90 degrees around +x.

    Parameters
    ----------
    input_array
        spherical harmonic coefficients
    ell_list
        list of :math:`\ell` values to use. If ``None`` (default) we assume that all even orders are inluded
        until some :math:`\ell_\mathrm{max}`, which will be calculated from the shape of the coefficients
        array.
    d_matrices
        list of Wigner (small) d-matrices corresponding to a 90 degree rotation around x.
        If ``None`` (default) pre-calculated matrix elements are used.
    output_array
        numpy array with same shape as :attr:`input_array`.
        If ``None`` (default) a new array is initialized.
        If :attr:`output_array` is given, the calculations are carried out in place.

    Returns
    ---------
        numpy array with the same shape as :attr:`input_array`.
    """
    if output_array is None:
        output_array = np.zeros(input_array.shape, dtype=float)

    start_index = 0
    for ell in ell_list:
        output_array[..., start_index:start_index+(2*ell+1)]\
            = np.einsum('...m,nm->...n', input_array[..., start_index:start_index+(2*ell+1)], d_matrices[ell])
        start_index += 2 * ell + 1
    return output_array


def calculate_sph_coefficients_rotated_by_90_degrees_around_negative_x(
        input_array: NDArray[float],
        ell_list: List[int],
        d_matrices: List[NDArray[float]],
        output_array: NDArray[float] = None,
        ) -> NDArray[float]:
    r""" Calculate the spherical harmonic coefficients after a rotation by 90 degrees around -x.

    Parameters
    ----------
    input_array
        spherical harmonic coefficients
    ell_list
        list of :math:`\ell` values to use. If ``None`` (default) we assume that all even orders are inluded
        until some :math:`\ell_\mathrm{max}`, which will be calculated from the shape of the coefficients
        array.
    d_matrices
        list of Wigner (small) d-matrices corresponding to a 90 degree rotation around x.
        If ``None`` (default) pre-calculated matrix elements are used.
    output_array
        numpy array with same shape as :attr:`input_array`.
        If ``None`` (default) a new array is initialized.
        If :attr:`output_array` is given, the calculations are carried out in place.

    Returns
    ---------
        numpy array with same shape as :attr:`input_array`.
    """
    if output_array is None:
        output_array = np.zeros(input_array.shape, dtype=float)

    start_index = 0
    for ell in ell_list:
        output_array[..., start_index:start_index+(2*ell+1)]\
            = np.einsum('...m,mn->...n', input_array[..., start_index:start_index+(2*ell+1)], d_matrices[ell])
        start_index += 2 * ell + 1
    return output_array


def calculate_sph_coefficients_rotated_around_z(
        input_array: NDArray[float],
        angle: NDArray[float],
        ell_list: List[int],
        output_array: NDArray[float] = None,
        ) -> NDArray[float]:
    r""" Calculate the spherical harmonic coefficients after a rotation around +z.

    Parameters
    ----------
    input_array
        spherical harmonic coefficients
    angle
        either an array with the same shape as ``input_array.shape[:-1]`` or a scalar.
        If a scalar is given all coefficient lists are rotated by the same angle.
    ell_list
        list of :math:`\ell` values to use. If ``None`` (default) we assume that all even orders are inluded
        until some :math:`\ell_\mathrm{max}`, which will be calculated from the shape of the coefficients
        array.
    d_matrices
        list of Wigner (small) d-matrices corresponding to a 90 degree rotation around x.
        If ``None`` (default) pre-calculated matrix elements are used.
    output_array
        numpy array with same shape as :attr:`input_array`.
        If ``None`` (default) a new array is initialized.
        If :attr:`output_array` is given, the calculations are carried out in place.

    Returns
    ---------
        numpy array with same shape as :attr:`input_array`.
    """
    if output_array is None:
        output_array = np.zeros(input_array.shape, dtype=float)

    start_index = 0

    for ell in ell_list:

        if ell == 0:
            output_array[..., 0] = input_array[..., 0]
        else:
            m = np.arange(-ell, ell+1)  # using negative ms is a comp. trick
            ma = np.einsum('m,...->...m', m, angle)
            output_array[..., start_index:start_index+(2*ell+1)]\
                = input_array[..., start_index:start_index+(2*ell+1)] * np.cos(ma)\
                - input_array[..., start_index+(2*ell+1)-1:start_index-1:-1] * np.sin(ma)

        start_index += 2 * ell + 1

    return output_array


def calculate_sph_coefficients_rotated_around_z_derived_wrt_the_angle(
        input_array: NDArray[float],
        angle: List[float],
        ell_list: List[int],
        output_array: NDArray[float] = None,
        ) -> NDArray[float]:
    r""" Calculate the angular derivatives of spherical harmonic coefficients with respect
    at the specified angle, where the angle refers to the rotation around +z.

    Parameters
    ----------
    input_array
        spherical harmonic coefficients
    angle
        either an array with the same shape as :attr:`input_array.shape[:-1]` or a scalar.
        If a scalar is given all coefficient lists are rotated by the same angle.
    ell_list
        list of :math:`\ell` values to use. If ``None`` (default) we assume that all even orders are inluded
        until some :math:`\ell_\mathrm{max}`, which will be calculated from the shape of the coefficients
        array.
    d_matrices
        list of Wigner (small) d-matrices corresponding to a 90 degree rotation about x.
        If ``None`` (default) pre-calculated matrix elements are used.
    output_array
        numpy array with same shape as :attr:`input_array`.
        If ``None`` (default) a new array is initialized.
        If :attr:`output_array` is given, the calculations are carried out in place.

    Returns
    ---------
        numpy array with same shape as :attr:`input_array`.
    """
    if output_array is None:
        output_array = np.zeros(input_array.shape, dtype=float)

    start_index = 0

    for ell in ell_list:

        if ell == 0:
            output_array[..., 0] = 0
        else:
            m = np.arange(-ell, ell+1)  # using negative ms is a comp. trick
            ma = np.einsum('m,...->...m', m, angle)
            m = np.einsum('m,...->...m', m, np.ones(angle.shape))  # Hacky indexing trick

            output_array[..., start_index:start_index+(2*ell+1)]\
                = input_array[..., start_index:start_index+(2*ell+1)] * (-m) * np.sin(ma)\
                - input_array[..., start_index+(2*ell+1)-1:start_index-1:-1] * m * np.cos(ma)

        start_index += 2 * ell + 1

    return output_array


def calculate_sph_coefficients_rotated_by_euler_angles(
        input_array: NDArray[float],
        Psi: NDArray[float],
        Theta: NDArray[float],
        Phi: NDArray[float],
        ell_list: List[int] = None,
        d_matrices: List[NDArray] = None,
        output_array: NDArray[float] = None,
        ) -> NDArray[float]:
    r"""Calculate the spherical harmonics coefficients after a rotation specified by a set of Euler angles.
    The Euler angles need to be given in 'zyz' format.
    A rotation with ``(0, Theta, Phi)`` will move the z-axis into the coordinates ``(Theta, Phi)``.

    Parameters
    ----------
    input_array
        array, the last dimension of which runs over the spherical harmonics coefficients.
    Psi
        First Euler angle. Initial rotation about the z-axis. Can be either a scalar
        or a numpy array with shape :attr:`input_array.shape[:-1]`.
        If ``None`` the rotation is skipped.
    Theta
        Second Euler angle. Rotation about the y-axis. Can be either a scalar
        or a numpy array with shape ``input_array.shape[:-1]``.
        If ``None`` the rotation is skipped.
    Phi
        Third Euler angle. Final rotation about the z-axis. Can be either a scalar
        or a numpy array with shape ``input_array.shape[:-1]``.
        If ``None`` the rotation is skipped.
    ell_list
        list of :math:`\ell` values to use. If ``None`` (default) we assume that all even orders are inluded
        until some :math:`\ell_\mathrm{max}`, which will be calculated from the shape of the coefficients
        array.
    d_matrices
        list of Wigner (small) d-matrices corresponding to a 90 degree rotation around x.
        If ``None`` (default) pre-calculated matrix elements are used.
    output_array
        numpy array with same shape as :attr:`input_array`.
        If ``None`` (default) a new array is initialized.
        If :attr:`output_array` is given, the calculations are carried out in place.

    Returns
    ---------
        numpy array with same shape as :attr:`input_array`.
    """

    if output_array is None:
        output_array = np.zeros(input_array.shape, dtype=float)

    if isinstance(ell_list, int):
        ell_list = np.arange(0, ell_list+1, 2)
    elif ell_list is None:
        # figure out what ell_max is
        num_coeffs = input_array.shape[-1]
        ell = 0
        cum_sum = 1
        while cum_sum < num_coeffs:
            ell += 2
            cum_sum += 2 * ell + 1

        if cum_sum == num_coeffs:
            ell_list = np.arange(0, ell+1, 2)
        else:
            raise ValueError('ell_max cannot be derived from input')

        if d_matrices is None:
            d_matrices = load_d_matrices(np.max(ell_list))

    # Do z rotation of Psi
    if Psi is not None:
        output_array = calculate_sph_coefficients_rotated_around_z(input_array,
                                                                   Psi,
                                                                   ell_list,
                                                                   output_array=output_array)
    else:
        output_array = np.array(input_array, dtype=float)
    # Do y rotation about Theta
    if Theta is not None:
        # Do 90 degree rotation around x
        calculate_sph_coefficients_rotated_by_90_degrees_around_positive_x(output_array,
                                                                           ell_list,
                                                                           d_matrices,
                                                                           output_array=output_array)
        # Do z rotation of Theta
        calculate_sph_coefficients_rotated_around_z(output_array,
                                                    Theta,
                                                    ell_list,
                                                    output_array=output_array)
        # Do -90 degree rotation around x
        calculate_sph_coefficients_rotated_by_90_degrees_around_negative_x(output_array,
                                                                           ell_list,
                                                                           d_matrices,
                                                                           output_array=output_array)
    # Do z rotation of Phi
    if Phi is not None:
        # Do z rotation of Phi
        calculate_sph_coefficients_rotated_around_z(output_array,
                                                    Phi,
                                                    ell_list,
                                                    output_array=output_array)

    return output_array
