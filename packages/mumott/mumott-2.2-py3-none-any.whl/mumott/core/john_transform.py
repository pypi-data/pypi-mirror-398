from math import floor
from numba import njit, int32, float32, float64, prange, void
from numpy.typing import NDArray
import numpy as np


def john_transform(
        field: NDArray[float],
        projections: NDArray[float],
        unit_vector_p: NDArray[float],
        unit_vector_j: NDArray[float],
        unit_vector_k: NDArray[float],
        offsets_j: NDArray[float],
        offsets_k: NDArray[float],
        float_type: str = 'float64') -> callable:
    r""" Frontend for performing the John transform with parallel
    CPU computing, using an algorithm akin to :func:`mumott.core.john_transform_cuda`.

    Parameters
    ----------
    field
        The field to be projected, with 4 dimensions. The last index should
        have the same size as the last index of :attr:`projections`.
    projections
        A 4-dimensional numpy array where the projections are stored.
        The first index runs over the different projection directions.
    unit_vector_p
        The direction of projection in Cartesian coordinates.
    unit_vector_j
        One of the directions for the pixels of :attr:`projections``.
    unit_vector_k
        The other direction for the pixels of :attr:`projections`.
    offsets_j
        Offsets which align projections in the direction of `j`
    offsets_k
        Offsets which align projections in the direction of `k`.
    float_type
        Whether to use 'float64' (default) or 'float32'. The argument should be supplied
        as a string. The types of :attr:`field` and :attr:`projections` must match this type.


    Notes
    -----
    The computation performed by this function may be written as

    .. math::

        p(I, J, K)_i = \sum_{s=0}^{N-1} d \cdot \sum_{t=0}^3 t_w V_i(\lfloor \mathbf{r}_j + d s \cdot \mathbf{v} \rfloor + \mathbf{t})

    where :math:`p(I, J, K)_i` is ``projection[I, J, K, i]``,  :math:`V_i` is ``volume[..., i]``,
    and :math:`\mathbf{v}` is ``unit_vector_p[I]``. :math:`N` is the number of voxels in the maximal direction
    of ``unit_vector_p[I]``. :math:`d` is the step length, and is given by the norm of
    :math:`\Vert \mathbf{v}_I \Vert / \vert \max(\mathbf{v})) \vert`.
    :math:`t_w` and :math:`\mathbf{t}` are weights and index shifts, respectively.
    The latter are necessary to perform bilinear interpolation between the four
    closest voxels in the two directions orthogonal to the
    maximal direction of :math:`\mathbf{v}`.
    :math:`\mathbf{r}_j` is the starting position for the ray,
    and is given by

    .. math::

        \mathbf{r}_j(J, K) = (J + 0.5 + o_J - 0.5 \cdot J_\text{max}) \cdot \mathbf{u} + \\
                (K + 0.5 + o_K - 0.5 \cdot K_\text{max}) \cdot \mathbf{w} + \\
                (\Delta_p) \cdot \mathbf{v} + 0.5 \cdot \mathbf{r}_\text{max} \\

    where :math:`o_J` is ``offsets_j[I]``,
    :math:`o_K` is ``offsets_k[I]``,
    :math:`\mathbf{u}` is ``unit_vector_j[I]``, :math:`\mathbf{w}` is ``unit_vector_k[I]``,
    :math:`J_\text{max}` and :math:`K_\text{max}` are ``projections.shape[1]`` and
    ``projections.shape[2]`` respectively, and :math:`\mathbf{r}_\text{max}` is
    ``volume.shape[:3]``. :math:`\Delta_p` is an additional offset that places the
    starting position at the edge of the volume.
    """ # noqa

    if float_type == 'float64':
        numba_float = float64
    elif float_type == 'float32':
        numba_float = float32
    else:
        raise ValueError('float_type must be either "float64" or "float32", '
                         f'but a value of {float_type} was specified!')

    if str(field.dtype) != float_type:
        raise TypeError('The dtype of the argument "field" must be the same '
                        f'as the dtype specified by "float_type" ({float_type}), but '
                        f'field.dtype is {field.dtype}!')
    if str(projections.dtype) != float_type:
        raise TypeError('The dtype of the argument "projections" must be the same '
                        f'as the dtype specified by "float_type" ({float_type}), but '
                        f'projections.dtype is {projections.dtype}!')

    # Find zeroth, first and second directions for indexing. Zeroth is the maximal projection direction.

    # (x, y, z), (y, x, z), (z, x, y)
    direction_0_index = np.argmax(abs(unit_vector_p), axis=1).reshape(-1, 1).astype(np.int32)
    direction_1_index = 1 * (direction_0_index == 0).astype(np.int32).reshape(-1, 1).astype(np.int32)
    direction_2_index = (2 - (direction_0_index == 2)).astype(np.int32).reshape(-1, 1).astype(np.int32)

    # Step size for direction 1 and 2.
    step_sizes_1 = (np.take_along_axis(unit_vector_p, direction_1_index, 1) /
                    np.take_along_axis(unit_vector_p, direction_0_index, 1)).astype(str(numba_float)).ravel()
    step_sizes_2 = (np.take_along_axis(unit_vector_p, direction_2_index, 1) /
                    np.take_along_axis(unit_vector_p, direction_0_index, 1)).astype(str(numba_float)).ravel()

    # Shape in each of the three directions.
    dimensions_0 = np.array(field.shape, dtype=str(numba_float))[direction_0_index.ravel()]
    dimensions_1 = np.array(field.shape, dtype=str(numba_float))[direction_1_index.ravel()]
    dimensions_2 = np.array(field.shape, dtype=str(numba_float))[direction_2_index.ravel()]

    # Correction factor for length of line when taking a one-slice step.
    distance_multipliers = np.sqrt(1.0 + step_sizes_1 ** 2 + step_sizes_2 ** 2).astype(str(numba_float))

    max_index = projections.shape[0]
    max_j = projections.shape[1]
    max_k = projections.shape[2]

    # CUDA chunking and memory size constants.
    channels = int(field.shape[-1])

    # Indices to navigate each projection. s is the surface positioning.
    k_vectors = unit_vector_k.astype(str(numba_float))
    j_vectors = unit_vector_j.astype(str(numba_float))
    s_vectors = (unit_vector_k * (-0.5 * max_k + offsets_k.reshape(-1, 1)) +
                 unit_vector_j * (-0.5 * max_j + offsets_j.reshape(-1, 1))).astype(str(numba_float))

    # (0, 1, 2) if x main, (1, 0, 2) if y main, (2, 0, 1) if z main.
    direction_indices = np.stack((direction_0_index.ravel(),
                                  direction_1_index.ravel(),
                                  direction_2_index.ravel()), axis=1)
    max_x, max_y, max_z = field.shape[:3]

    # Bilinear interpolation over each slice.

    @njit(void(numba_float[:, :, :, ::1], int32, numba_float, numba_float,
               numba_float, int32[::1], numba_float[::1]),
          fastmath=True,
          nogil=True,
          cache=True)
    def bilinear_interpolation(field: NDArray[float], direction_0: int,
                               r0: float, r1: float, r2: float, dimensions,
                               accumulator: NDArray[float]):
        """ Kernel for bilinear interpolation. Replaces texture interpolation."""
        if not ((0 <= r0 < dimensions[0]) and (-1 <= r1 < dimensions[1]) and
                (-1 <= r2 < dimensions[2])):
            return
        if direction_0 == 0:
            coordinate_directions = {'x': 0, 'y': 1, 'z': 2}
        elif direction_0 == 1:
            coordinate_directions = {'x': 1, 'y': 0, 'z': 2}
        elif direction_0 == 2:
            coordinate_directions = {'x': 1, 'y': 2, 'z': 0}
        # At edges, use nearest-neighbor interpolation.
        positions = (r0, r1, r2)
        weight_1 = numba_float(positions[1] - floor(positions[1]))
        weight_2 = numba_float(positions[2] - floor(positions[2]))
        t = ((1 - weight_1) * (1 - weight_2) * (positions[1] >= 0) *
             (positions[2] >= 0), ((1 - weight_2) * weight_1) *
             (positions[1] < (dimensions[1] - 1)) * (positions[2] >= 0),
             ((1 - weight_1) * weight_2) *
             (positions[2] < (dimensions[2] - 1)) * (positions[1] >= 0),
             (weight_1 * weight_2) * (positions[1] < (dimensions[1] - 1)) *
             (positions[2] < (dimensions[2] - 1)))

        x0 = int32(max(floor(positions[coordinate_directions['x']]), 0))
        x1 = x0 + int32((direction_0 != 0) * (x0 < (max_x - 1)))

        y0 = int32(max(floor(positions[coordinate_directions['y']]), 0))
        y1 = y0 + int32((direction_0 == 0) * (y0 < (max_y - 1)))
        y2 = y0 + int32((direction_0 == 2) * (y0 < (max_y - 1)))
        y3 = y0 + int32((direction_0 != 1) * (y0 < (max_y - 1)))

        z0 = int32(max(floor(positions[coordinate_directions['z']]), 0))
        z1 = int32(z0) + int32((direction_0 != 2) * (z0 < (max_z - 1)))
        for i in range(accumulator.size):
            accumulator[i] += (field[x0, y0, z0, i] * t[0] +
                               field[x1, y1, z0, i] * t[1] +
                               field[x0, y2, z1, i] * t[2] +
                               field[x1, y3, z1, i] * t[3])

    @njit(void(numba_float[:, :, :, ::1], numba_float[:, :, :, ::1]),
          fastmath=True, nogil=True, parallel=True, cache=True)
    def john_transform_inner(field: NDArray[float], projection: NDArray[float]):
        """ Performs the John transform of a field. Relies on a large number
        of pre-defined constants outside the kernel body. """
        for index in range(max_index):
            # Define compile-time constants.
            step_size_1 = step_sizes_1[index]
            step_size_2 = step_sizes_2[index]
            k_vectors_c = k_vectors[index]
            j_vectors_c = j_vectors[index]
            s_vectors_c = s_vectors[index]
            dimensions_0_c = dimensions_0[index]
            dimensions_1_c = dimensions_1[index]
            dimensions_2_c = dimensions_2[index]
            dimensions = np.empty(3, int32)
            dimensions[0] = dimensions_0_c
            dimensions[1] = dimensions_1_c
            dimensions[2] = dimensions_2_c
            direction_indices_c = direction_indices[index]
            distance_multiplier = distance_multipliers[index]

            for j in prange(max_j):
                accumulator = np.empty(channels, numba_float)
                # Could be chunked for very asymmetric samples.
                fj = numba_float(j) + 0.5
                for k in range(max_k):
                    for i in range(channels):
                        accumulator[i] = 0.

                    fk = numba_float(k) + 0.5

                    # Initial coordinates of projection.
                    start_position_0 = (s_vectors_c[direction_indices_c[0]] +
                                        fj * j_vectors_c[direction_indices_c[0]] +
                                        fk * k_vectors_c[direction_indices_c[0]])
                    start_position_1 = (s_vectors_c[direction_indices_c[1]] +
                                        fj * j_vectors_c[direction_indices_c[1]] +
                                        fk * k_vectors_c[direction_indices_c[1]])
                    start_position_2 = (s_vectors_c[direction_indices_c[2]] +
                                        fj * j_vectors_c[direction_indices_c[2]] +
                                        fk * k_vectors_c[direction_indices_c[2]])

                    # Centering w.r.t volume.
                    centering_step_1 = start_position_1 - step_size_1 * start_position_0
                    centering_step_2 = start_position_2 - step_size_2 * start_position_0

                    position_0 = numba_float(0) + 0.5
                    position_1 = step_size_1 * (numba_float(0) - 0.5 * dimensions[0] + 0.5) + \
                        centering_step_1 + 0.5 * dimensions[1] - 0.5
                    position_2 = step_size_2 * (numba_float(0) - 0.5 * dimensions[0] + 0.5) + \
                        centering_step_2 + 0.5 * dimensions[2] - 0.5

                    for i in range(dimensions[0]):
                        bilinear_interpolation(field, direction_indices_c[0],
                                               position_0, position_1, position_2, dimensions, accumulator)
                        position_0 += 1.0
                        position_1 += step_size_1
                        position_2 += step_size_2

                    for i in range(channels):
                        projection[index, j, k, i] = accumulator[i] * distance_multiplier

    def john_transform_wrapper(field, projection):
        john_transform_inner(field, projection)
        return projection

    return john_transform_wrapper


def john_transform_adjoint(field: NDArray[float], projections: NDArray[float],
                           unit_vector_p: NDArray[float], unit_vector_j: NDArray[float],
                           unit_vector_k: NDArray[float], offsets_j: NDArray[float],
                           offsets_k: NDArray[float], float_type: str = 'float64') -> callable:
    r""" Frontend for performing the adjoint of the John transform with parallel
    CPU computing, using an algorithm akin to :func:`mumott.core.john_transform_cuda`.

    Parameters
    ----------
    field
        The field into which the adjoint is projected, with 4 dimensions. The last index should
        have the same size as the last index of :attr:`projections`.
    projections
        The projections from which the adjoint is calculated.
        The first index runs over the different projection directions.
    unit_vector_p
        The direction of projection in Cartesian coordinates.
    unit_vector_j
        One of the directions for the pixels of :attr:`projections`.
    unit_vector_k
        The other direction for the pixels of :attr:`projections`.
    offsets_j
        Offsets which align projections in the direction of `j`
    offsets_k
        Offsets which align projections in the direction of `k`.
    float_type
        Whether to use 'float64' (default) or 'float32'. The argument should be supplied
        as a string. The types of :attr:`field` and :attr:`projections` must match this type.

    Notes
    -----
    The computation performed by this function may be written as

    .. math::

        V_i(\mathbf{x}) = \sum_{s=0}^{N-1} \cdot \sum_{t = 0}^{4} t_w p_i(s, \mathbf{x} \cdot \mathbf{u} + \Delta_J + t_J, \mathbf{x} \cdot \mathbf{w} + \Delta_K + t_K)

    :math:`N` is the total number of projections.
    :math:`V_i` is ``volume[:, i]``,
    and :math:`\mathbf{v}` is ``projection_vector[s]``. :math:`\mathbf{u}` is ``unit_vector_j[s]``,
    :math:`\mathbf{w}` is ``unit_vector_k[s]``. :math:`\Delta_J` and :math:`\Delta_K` are additional
    offsets based on the unit vectors, shapes, and offsets, which align the centers of the projection and volume,
    so that the intersection of each ray is correctly computed.
    :math:`t_W` are weights for bilinear interpolation between the four pixels nearest to each ray;
    :math:`t_J` and :math:`t_K` are the index offsets necessary to perform this interpolation.
    """ # noqa
    if float_type == 'float64':
        numba_float = float64
    elif float_type == 'float32':
        numba_float = float32
    else:
        raise ValueError('float_type must be either "numba_float" or "float32", '
                         f'but a value of {float_type} was specified!')

    if str(field.dtype) != float_type:
        raise TypeError('The dtype of the argument "field" must be the same '
                        f'as the dtype specified by "float_type" ({float_type}), but '
                        f'field.dtype is {field.dtype}!')

    if str(projections.dtype) != float_type:
        raise TypeError('The dtype of the argument "projections" must be the same '
                        f'as the dtype specified by "float_type" ({float_type}), but '
                        f'projections.dtype is {projections.dtype}!')

    max_j = projections.shape[1]
    max_k = projections.shape[2]

    max_x, max_y, max_z = field.shape[:3]
    max_index = projections.shape[0]

    # Projection vectors. s for positioning the projection.
    p_vectors = unit_vector_p.astype(str(numba_float))
    k_vectors = unit_vector_k.astype(str(numba_float))
    j_vectors = unit_vector_j.astype(str(numba_float))
    s_vectors = (unit_vector_k * (-0.5 * max_k + offsets_k.reshape(-1, 1)) +
                 unit_vector_j * (-0.5 * max_j + offsets_j.reshape(-1, 1))).astype(str(numba_float))

    # Translate volume steps to normalized projection steps. Can add support for non-square voxels.
    vector_norm = np.einsum('...i, ...i', p_vectors, np.cross(j_vectors, k_vectors))
    norm_j = -np.cross(p_vectors, k_vectors) / vector_norm[..., None]
    norm_k = np.cross(p_vectors, j_vectors) / vector_norm[..., None]
    norm_offset_j = -np.einsum('...i, ...i', p_vectors, np.cross(s_vectors, k_vectors)) / vector_norm
    norm_offset_k = np.einsum('...i, ...i', p_vectors, np.cross(s_vectors, j_vectors)) / vector_norm

    channels = field.shape[-1]

    @njit(void(numba_float[:, :, :, ::1], numba_float,
               numba_float, numba_float, numba_float[::1]),
          fastmath=True, cache=True, nogil=True)
    def bilinear_interpolation_projection(projection: NDArray[float],
                                          index: float, fj: float, fk: float,
                                          accumulator: NDArray[float]):
        if not (-1 <= fj < max_j and -1 <= fk < max_k):
            return
        # At edges, use nearest-neighbor interpolation.
        y_weight = numba_float(fj - floor(fj))
        z_weight = numba_float(fk - floor(fk))
        x = int32(index)
        y0 = int32(max(floor(fj), 0))
        y1 = y0 + (y0 < (max_j - 1))
        z0 = int32(max(floor(fk), 0))
        z1 = z0 + (z0 < (max_k - 1))
        t = ((1 - y_weight) * (1 - z_weight) * (fj >= 0) * (fk >= 0),
             ((1 - z_weight) * y_weight) * (fj < (max_j - 1)) * (fk >= 0),
             ((1 - y_weight) * z_weight) * (fk < (max_k - 1)) * (fj >= 0),
             (z_weight * y_weight) * (fj < (max_j - 1)) * (fk < (max_k - 1)))
        for i in range(channels):
            accumulator[i] += (projection[x, y0, z0, i] * t[0] +
                               projection[x, y1, z0, i] * t[1] +
                               projection[x, y0, z1, i] * t[2] +
                               projection[x, y1, z1, i] * t[3])

    @njit(void(numba_float[:, :, :, ::1], numba_float[:, :, :, ::1]),
          fastmath=True, cache=True, nogil=True, parallel=True)
    def john_transform_adjoint_inner(field: NDArray[float], projection: NDArray[float]):
        """ Performs the John transform of a field. Relies on a large number
        of pre-defined constants outside the kernel body. """
        # Indexing of volume coordinates.
        for x in range(max_x):
            fx = x - 0.5 * field.shape[0] + 0.5
            for y in prange(max_y):
                z_acc = np.empty(channels, numba_float)
                fy = y - 0.5 * field.shape[1] + 0.5
                for z in range(max_z):
                    # Center of voxel and coordinate system.
                    fz = z - 0.5 * field.shape[2] + 0.5

                    for j in range(channels):
                        z_acc[j] = 0.0

                    for a in range(max_index):
                        # Center with respect to projection.
                        fj = (norm_offset_j[a] + fx * norm_j[a][0] +
                              fy * norm_j[a][1] + fz * norm_j[a][2] - 0.5)
                        fk = (norm_offset_k[a] + fx * norm_k[a][0] +
                              fy * norm_k[a][1] + fz * norm_k[a][2] - 0.5)
                        bilinear_interpolation_projection(projection,
                                                          a, fj, fk, z_acc)
                    for i in range(channels):
                        field[x, y, z, i] = z_acc[i]

    def john_transform_adjoint_inner_wrapper(field, projection):
        john_transform_adjoint_inner(field, projection)
        return field
    return john_transform_adjoint_inner_wrapper
