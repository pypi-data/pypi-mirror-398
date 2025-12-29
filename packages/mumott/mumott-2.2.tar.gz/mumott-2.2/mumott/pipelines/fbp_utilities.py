import logging

import numpy as np

from mumott import Geometry
from mumott.data_handling.utilities import get_absorbances
from mumott.core.projection_stack import ProjectionStack

logger = logging.getLogger(__name__)


def _get_unique_indices(angles: np.ndarray[float],
                        indices: np.ndarray[int],
                        tolerance: float = 1e-4) -> np.ndarray[float]:
    """Filters indices based on angles."""
    angles = np.mod(angles, np.pi)
    out_indices = [indices[0]]
    out_angles = [angles[0]]

    for angle, index in zip(angles, indices):
        angle_delta = np.abs(angle - np.array(out_angles))
        if np.all((angle_delta > tolerance) & (angle_delta < np.pi - tolerance)):
            out_indices.append(index)
            out_angles.append(angle)
    return np.array(out_indices)


def _get_orthogonal_axis(geometry: Geometry,
                         projection_index: int = 0,
                         axis_string='inner'):
    """Retrieves index of axis orthogonal to inner or outer axis in geometry."""
    if axis_string == 'inner':
        axis = geometry.inner_axes[projection_index]
    elif axis_string == 'outer':
        axis = geometry.outer_axes[projection_index]
    else:
        raise ValueError('axis_string must be either "inner" or "outer", '
                         f'but a value of "{axis_string}" was specified.')
    j_projection = np.dot(axis, geometry.j_direction_0)
    k_projection = np.dot(axis, geometry.k_direction_0)
    if not np.isclose(abs(j_projection + k_projection), 1):
        raise ValueError('Rotation axis must be orthogonal to the j or k-axis.')

    if np.isclose(j_projection, 0):
        return 1
    else:
        return 2


def _get_filter(length: int,
                filter_type: str) -> np.ndarray[float]:
    """Retrieves a high-pass filter for FBP based on the string."""
    u = np.fft.fftfreq(length) / (4 * np.pi)
    filter = abs(u)
    filter[abs(u) > 1 / (16 * np.pi)] = 0.0
    if filter_type.lower() == 'ram-lak':
        return filter
    elif filter_type.lower() == 'hann':
        filter *= 0.5 + 0.5 * np.cos(2 * np.pi * u)
    elif filter_type.lower() == 'hamming':
        filter *= 0.54 + 0.46 * np.cos(2 * np.pi * u)
    elif filter_type.lower() == 'shepp-logan':
        filter *= np.sinc(u)
    elif filter_type.lower() == 'cosine':
        filter *= np.cos(u * np.pi)
    else:
        raise ValueError(f'Unknown filter type: "{filter_type}"!'
                         ' Permitted values are: "Ram-Lak", "Hamming", "Hann",'
                         ' "cosine", and "Shepp-Logan".')
    return filter


def get_filtered_projections(projections: ProjectionStack,
                             axis_string: str = 'inner',
                             filter_type: str = 'Ram-Lak',
                             normalization_percentile: float = 99.9,
                             transmittivity_cutoff: tuple[float, float] = (None, None)) \
                              -> tuple[np.ndarray, np.ndarray]:
    """
    Applies a high-pass filter to a selected subset of the
    absorbances for filtered back projection.

    Parameters
    ----------
    projections
        The :class:`ProjectionStack <mumott.data_handling.ProjectionStack>` to calculate the
        filtered projections from.
    axis_string
        Default is ``'inner'``, the value depends on how the sample is mounted to the holder. Typically,
        the inner axis is the rotation axis while the ``'outer'`` axis refers to the tilt axis.
    filter_string
        Default is ``'ram-lak'``, a high-pass filter. Other options are ``'Hamming'`` and ``'Hanning'``.
    normalization_percentile
        The normalization percentile to use for the transmittivity calculation. See
        :func:`get_transmittivities <mumott.data_handling.utilities.get_transmittivities>` for details.
    transmittivity_cutoff
        The cutoffs to use for the transmittivity calculation. See
        :func:`get_transmittivities <mumott.data_handling.utilities.get_transmittivities>` for details.

    Returns
    -------
        A tuple containing the filtered subset of the absorbances
        and the index of the axis orthogonal to the inner or outer axis.
    """
    geometry = projections.geometry
    if axis_string == 'inner':
        tilt_angles = geometry.outer_angles_as_array
        rotation_angles = geometry.inner_angles_as_array
    elif axis_string == 'outer':
        tilt_angles = geometry.inner_angles_as_array
        rotation_angles = geometry.outer_angles_as_array
    else:
        raise ValueError(f'Unknown axis: {axis_string}, '
                         'please specify "inner" or "outer".')

    # Check if we have any transmittivity cutoff values to consider
    cutoff_values = (1e-4, 1)  # default
    for k in range(2):
        if transmittivity_cutoff[k] is not None:
            cutoff_values[k] = transmittivity_cutoff[k]

    abs_dict = get_absorbances(
        projections.diode,
        normalize_per_projection=True,
        normalization_percentile=normalization_percentile,
        cutoff_values=cutoff_values)
    absorbances = abs_dict['absorbances']
    # Find projections without any tilt and the rotation of each such projection
    no_tilt_indices = np.where(np.isclose(tilt_angles, 0))[0]
    no_tilt_angles = rotation_angles[no_tilt_indices]

    # Remove 'duplicate' projections with equivalent or very similar rotation angles
    no_tilt_indices = _get_unique_indices(no_tilt_angles, no_tilt_indices)
    absorbances = absorbances[no_tilt_indices]
    filter_axis = _get_orthogonal_axis(geometry, 0, axis_string)
    filter = _get_filter(length=absorbances.shape[filter_axis],
                         filter_type=filter_type)
    if filter_axis == 1:
        filter = filter.reshape(1, -1, 1, 1)
    else:
        filter = filter.reshape(1, 1, -1, 1)

    # reduce weights over last index
    abs_mask = np.all(abs_dict['cutoff_mask'][no_tilt_indices] *
                      projections.weights[no_tilt_indices] > 0., axis=-1).astype(float)
    absorbances *= abs_mask[..., None]  # redundant axis needed for consistency reasons
    abs_fft = np.fft.fft(absorbances, axis=filter_axis)
    abs_fft *= filter
    filtered_absorbances = np.fft.ifft(abs_fft, axis=filter_axis).real
    return np.ascontiguousarray(filtered_absorbances), no_tilt_indices
