import sys
from tqdm import tqdm
from typing import Tuple
import numpy as np
from numpy.typing import NDArray
from mumott.core.wigner_d_utilities import load_d_matrices, calculate_sph_coefficients_rotated_by_euler_angles


def find_approximate_symmetry_axis(coefficients: NDArray[float],
                                   ell_max: int,
                                   resolution: int = 10,
                                   filter: str = None) -> Tuple[NDArray[float]]:
    r""" Find the axis of highest apparent symmetry voxel-by-voxel for a voxel map of sperical harmonics
    coefficients. As a default, the measure of degree of symmetry is a power of the function rotationally
    averaged around the given axis.

    Parameters
    ----------
    coefficients
        Voxel map of spherical harmonic coefficients.
    ell_max
        Largest order :math:`\ell` used in the fitting. If :attr:`coefficients` contains higher orders,
        it will be truncated.
    resolution
        Number or angular steps along a half-circle, used in the search for the optimal axis.
    filter
        Weighing of different orders used to calculate the degree of symmetry.
        Possible values are "ramp" and "square". By default no filter is applied (`None`).

    Returns
    ---------
    optimal_zonal_coeffs
        Zonal harmonics coefficients in the frame-of-reference corresponding
        to the axis of highest degree of symmetry.
    optimal_theta
        Voxel-by-voxel polar angles of the axis with highest degree of symmetry.
    optimal_phi
        Voxel-by-voxel azimuthal angles of the axis with highest degree of symmetry.
    """
    # Use only the coefficients up until ell_max
    truncated_coefficients = coefficients[..., :(ell_max+1)*(ell_max+2)//2]
    volume_shape = coefficients.shape[:-1]

    # Find the zonal coefficients
    zonal_indexes = np.zeros((ell_max+1)*(ell_max+2)//2, dtype=bool)
    inc = 0
    f = np.ones(ell_max//2+1)
    for ell in range(0, ell_max+1, 2):
        zonal_indexes[inc + ell] = True
        if filter == 'ramp':
            f[ell//2] = ell
        elif filter == 'square':
            f[ell//2] = ell**2
        inc += 2*ell + 1

    # Load d matrices
    d_matrices = load_d_matrices(ell_max)

    optimal_theta = np.zeros(volume_shape)
    optimal_phi = np.zeros(volume_shape)
    maximum_degree_of_symmetry = np.zeros(volume_shape)
    optimal_zonal_coeffs = np.zeros((*volume_shape, ell_max//2 + 1))

    # Loop through grid of directions
    theta_points = np.linspace(0, np.pi/2, resolution//2, endpoint=True)
    phi_points = np.linspace(0, 2*np.pi, 2*resolution, endpoint=False)
    for theta in tqdm(theta_points, file=sys.stdout):
        for phi in phi_points:
            rotated_coefficients = calculate_sph_coefficients_rotated_by_euler_angles(
                truncated_coefficients,
                Psi=-phi,
                Theta=-theta,
                Phi=None,
                d_matrices=d_matrices)
            # Check if degree of symmetry (DOS) is higher than maximum so far
            zonal_coeffs = rotated_coefficients[..., zonal_indexes]
            degree_of_symmetry = np.sum(zonal_coeffs**2*f[np.newaxis, np.newaxis, np.newaxis, :], axis=-1)
            indices = degree_of_symmetry > maximum_degree_of_symmetry
            maximum_degree_of_symmetry[indices] = degree_of_symmetry[indices]
            optimal_theta[indices] = theta
            optimal_phi[indices] = phi
            optimal_zonal_coeffs[indices, :] = zonal_coeffs[indices, :]

    return optimal_zonal_coeffs, optimal_theta, optimal_phi


def degree_of_symmetry_map(coefficients: NDArray[float],
                           ell_max: int,
                           resolution: int = 10,
                           filter: str = None) -> Tuple[NDArray[float]]:
    r""" Make a longitude-latitude map of the degree of symmetry. Can be used to make illustrating
    plots and to decide which filter is more appropriate.

    Parameters
    ----------
    coefficients
        Spherical harmonic coefficients of a single voxel.
    ell_max
        Largest order :math:`\ell` used in the fitting. If :attr:`coefficients` contains higher
        orders, it will be truncated.
    resolution
        Number or angular steps along a half-circle used in the search for the optimal axis.
    filter
        Weighing of different orders used to calculate the degree of symmetry.
        Possible values are "ramp" and "square". By default no filter is applied (`None`).

    Returns
    ---------
    dos
        Map of the calculated degree of symmetry.
    theta
        Polar angle coordinates of the map.
    phi
        Azimuthal angle coordinates of the map.
    """
    # Use only the coefficients up until ell_max
    truncated_coefficients = coefficients[..., :(ell_max+1)*(ell_max+2)//2]

    # Find the zonal coefficients
    zonal_indexes = np.zeros((ell_max+1)*(ell_max+2)//2, dtype=bool)
    inc = 0
    f = np.ones(ell_max//2+1)
    for ell in range(0, ell_max+1, 2):
        zonal_indexes[inc + ell] = True
        if filter == 'ramp':
            f[ell//2] = ell
        elif filter == 'square':
            f[ell//2] = ell**2
        inc += 2*ell + 1

    # Load d matrices
    d_matrices = load_d_matrices(ell_max)

    # Loop through grid of directions
    theta_points = np.linspace(0, np.pi, resolution, endpoint=True)
    phi_points = np.linspace(0, 2*np.pi, 2*resolution, endpoint=True)
    dos = np.zeros((resolution, 2*resolution))

    for ii, theta in enumerate(theta_points):
        for jj, phi in enumerate(phi_points):
            rotated_coefficients = calculate_sph_coefficients_rotated_by_euler_angles(
                truncated_coefficients,
                Psi=-phi,
                Theta=-theta,
                Phi=None,
                d_matrices=d_matrices)
            # Check if degree of symmetry (DOS) is higher than maximum so far
            zonal_coeffs = rotated_coefficients[..., zonal_indexes]
            degree_of_symmetry = np.sum(zonal_coeffs**2*f, axis=-1)
            dos[ii, jj] = degree_of_symmetry

    theta, phi = np.meshgrid(theta_points, phi_points, indexing='ij')
    dos = dos / np.sum(truncated_coefficients**2)

    return dos, theta, phi


def symmetric_part_along_given_direction(coefficients: NDArray[float],
                                         theta: NDArray[float],
                                         phi: NDArray[float],
                                         ell_max: int) -> NDArray[float]:
    r""" Find the zonal harmonic coefficients along the given input directions. This can be
    used if eigenvector analysis is used to generate the symmetry directions used for a
    further zonal-harmonics refinement step.

    Parameters
    ----------
    coefficients
        Voxel map of spherical harmonic coefficients.
    theta
        Voxel map of polar angles.
    phi
        Voxel map of azimuthal angles.
    ell_max
        Largest order :math:`\ell` used in the fitting. If :attr:`coefficients` contains higher orders,
        it will be truncated.

    Returns
    ---------
        Zonal harmonics coefficients in the frame of reference corresponding
        to the axis of highest degree of symmetry.
    """
    # Use only the coefficients up until ell_max
    truncated_coefficients = coefficients[..., :(ell_max+1)*(ell_max+2)//2]

    # Find the zonal coefficients
    zonal_indexes = np.zeros((ell_max+1)*(ell_max+2)//2, dtype=bool)
    inc = 0
    for ell in range(0, ell_max+1, 2):
        zonal_indexes[inc + ell] = True
        inc += 2*ell + 1

    # Load d matrices
    d_matrices = load_d_matrices(ell_max)
    rotated_coefficients = calculate_sph_coefficients_rotated_by_euler_angles(
        truncated_coefficients,
        Psi=-phi,
        Theta=-theta,
        Phi=None,
        d_matrices=d_matrices)
    # Pick out symmetric part
    zonal_coeffs = rotated_coefficients[..., zonal_indexes]
    return zonal_coeffs
