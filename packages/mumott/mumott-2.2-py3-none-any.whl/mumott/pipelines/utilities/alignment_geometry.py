import numpy as np

from mumott.data_handling import DataContainer
from mumott import Geometry


def get_alignment_geometry(data_container: DataContainer) -> tuple[int, np.ndarray[int]]:
    """ Define the index of the main rotation axis relative to the data, and the related
    tomogram volume.

    Parameters
    ----------
    data_container
        A :class:'DataContainer <mumott.data_handling.DataContainer>' instance.

    Returns
    -------
        a tuple comprising the index of the main rotation axis (0 or 1) and
        the volume of the tomogram related to the data and the main rotation axis

    """
    volume_deduced = data_container.geometry.volume_shape
    # check that dimensions of the volume match with the projection
    # or raise error and stop
    projection_shape = data_container.geometry.projection_shape
    if not all(element in volume_deduced for element in projection_shape):
        raise ValueError('data_container.geometry.volume_shape and'
                         ' data_container.geometry.projection_shape must'
                         ' match in shape')
    # abs in case of negative axis
    geom_inner_axes_index = np.where(
        np.isclose(np.abs(data_container.geometry.inner_axes[0]), 1)
    )[0][0]

    data_inner_axes_index = np.where(
        data_container.diode.shape ==
        data_container.geometry.volume_shape[geom_inner_axes_index]
    )[0][0] - 1

    main_rot_axis_deduced = data_inner_axes_index

    return main_rot_axis_deduced, volume_deduced


def shift_center_of_reconstruction(geometry: Geometry,
                                   shift_vector: tuple[float] = (0., 0., 0.)) -> None:
    """ This utility function will shift the ``offsets`` in the
    :class:`geometry <mumott.core.geometry.Geometry>` based on a three-dimensional
    shift vector. Use this to reposition the reconstruction within the volume.

    Parameters
    ----------
    geometry
        A :class:`Geometry <mumott.core.geometry.Geometry>` instance.
        Its `j_offsets` and `k_offsets` are modified in-place.
    shift_vector
        A ``tuple`` that indicates the direction and magnitude of the
        desired shift in ``(x, y, z)``, in units of voxels.

    Example
    -------
    >>> import numpy as np
    >>> from scipy.spatial.transform import Rotation
    >>> from mumott.core.geometry import Geometry, GeometryTuple
    >>> from mumott.pipelines.utilities.alignment_geometry import shift_center_of_reconstruction
    >>> geo = Geometry()
    >>> geo.append(GeometryTuple(rotation=np.eye(3), j_offset=0., k_offset=0.))
    >>> geo.append(GeometryTuple(rotation=Rotation.from_euler('y', np.pi/4).as_matrix(),
                                 j_offset=0.,
                                 k_offset=0.))
    >>> geo.append(GeometryTuple(rotation=Rotation.from_euler('z', np.pi/4).as_matrix(),
                                 j_offset=0.,
                                 k_offset=0.))
    >>> print(geo.j_direction_0)
    [1. 0. 0.]
    >>> print(geo.k_direction_0)
    [0. 0. 1.]
    >>> shift_center_of_reconstruction(geo, shift_vector=(-5., 1.7, 3.))
    >>> print(geo[0].j_offset, geo[0].k_offset)
    -5.0 3.0
    >>> print(geo[1].j_offset, geo[1].k_offset)
    -1.4142... 5.6568...
    >>> print(geo[2].j_offset, geo[2].k_offset)
    -4.737... 3.0
    """
    j_vectors = np.einsum(
            'kij,i->kj',
            geometry.rotations_as_array,
            geometry.j_direction_0)
    k_vectors = np.einsum(
            'kij,i->kj',
            geometry.rotations_as_array,
            geometry.k_direction_0)
    shifts_j = np.einsum('ij, j', j_vectors, shift_vector)
    shifts_k = np.einsum('ij, j', k_vectors, shift_vector)
    geometry.j_offsets += shifts_j
    geometry.k_offsets += shifts_k
