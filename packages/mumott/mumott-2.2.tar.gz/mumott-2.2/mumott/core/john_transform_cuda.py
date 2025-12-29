from typing import Any

from math import floor
from numba import config, cuda, int32, float32, float64, void, from_dtype
import numpy as np


def _is_cuda_array(item: Any):
    """ Internal method which assists in debugging. """
    if config.ENABLE_CUDASIM:
        return False
    else:
        return cuda.is_cuda_array(item)


def john_transform_cuda(field: np.ndarray[float], projections: np.ndarray[float],
                        unit_vector_p: np.ndarray[float], unit_vector_j: np.ndarray[float],
                        unit_vector_k: np.ndarray[float], offsets_j: np.ndarray[float],
                        offsets_k: np.ndarray[float]):
    """ Frontend for performing the John transform with parallel
    GPU computing.

    Parameters
    ----------
    field
        The field to be projected, with 4 dimensions. The last index should
        have the same size as the last index of ``projections``. Can be either
        a `numpy.ndarray`, or a device array that implements the CUDA array
        interface. If a device array is given, no copying to device is needed.
    projections
        A 4-dimensional numpy array where the projections are stored.
        The first index runs over the different projection directions. Can be either
        a `numpy.ndarray`, or a device array that implements the CUDA array
        interface. If a device array is given, no copying or synchronization is needed.
    unit_vector_p
        The direction of projection in Cartesian coordinates.
    unit_vector_j
        One of the directions for the pixels of ``projection``.
    unit_vector_k
        The other direction for the pixels of ``projection``.
    offsets_j
        Offsets which align projections in the direction of `j`
    offsets_k
        Offsets which align projections in the direction of `k`.

    Notes
    -----
    For mathematical details, see :func:`~.john_transform.john_transform`.
    """
    # Always false for now as we are sticking to ``float32``.
    if False:
        cuda_float = float64
        numpy_float = np.float64
        cuda_x4_type = cuda.float64x4
    else:
        cuda_float = float32
        numpy_float = np.float32
        cuda_x4_type = cuda.float32x4

    # Find zeroth, first and second directions for indexing. Zeroth is the maximal projection direction.

    # (x, y, z), (y, x, z), (z, x, y)
    direction_0_index = np.argmax(abs(unit_vector_p), axis=1).reshape(-1, 1).astype(np.int32)
    direction_1_index = 1 * (direction_0_index == 0).astype(np.int32).reshape(-1, 1).astype(np.int32)
    direction_2_index = (2 - (direction_0_index == 2)).astype(np.int32).reshape(-1, 1).astype(np.int32)

    # Step size for direction 1 and 2.
    step_sizes_1 = (np.take_along_axis(unit_vector_p, direction_1_index, 1) /
                    np.take_along_axis(unit_vector_p, direction_0_index, 1)).astype(numpy_float).ravel()
    step_sizes_2 = (np.take_along_axis(unit_vector_p, direction_2_index, 1) /
                    np.take_along_axis(unit_vector_p, direction_0_index, 1)).astype(numpy_float).ravel()

    # Shape in each of the three directions.
    dimensions_0 = np.array(field.shape, dtype=numpy_float)[direction_0_index.ravel()]
    dimensions_1 = np.array(field.shape, dtype=numpy_float)[direction_1_index.ravel()]
    dimensions_2 = np.array(field.shape, dtype=numpy_float)[direction_2_index.ravel()]

    # Correction factor for length of line when taking a one-slice step.
    distance_multipliers = np.sqrt(1.0 + step_sizes_1 ** 2 + step_sizes_2 ** 2).astype(numpy_float)

    # Not strictly necessary break these out, it just makes code easier to follow
    max_x, max_y, max_z, channels = field.shape
    number_of_projections, max_j, max_k = projections.shape[:3]

    # These constants control the number of threads/lanes in each kernel in order to
    # optimize memory access patterns. They are partly set from principles
    # such as "sequential threads should access sequential data", and partly set
    # through trial and error and profiling results. Ultimately the goal is
    # to minimize repetetive computations while also optimizing cache access.
    # Note that this differs from optimal access patterns for CPU threads,
    # because CUDA threads are analogous to SIMD lanes, not CPU threads.
    # For cases up to 8 channels, threads_j and threads_kc are used.
    # For cases with larger number of channels, accessing sequential channels
    # dominates performance, and so j and k are lumped together while the
    # channels are separated out.
    # TODO: Make this configurable by the user to allow for autotuning of
    # these parameters.

    # Few channels
    threads_j = int(32 // channels)
    threads_kc = int(8 * channels)
    # Many channels
    CH_CHUNKSIZE = int(min(max(2 ** floor(np.log2(channels)), 1), 8))
    threads_channel = int(min(max(2 ** floor(np.log2(channels / CH_CHUNKSIZE)), 1), 32))
    threads_jk = int(32 // threads_channel)
    JK_CHUNKSIZE = int(1)
    # Check the maximum amount of local memory needed by each thread and resize accordingly
    channel_blocks = (channels + threads_channel * CH_CHUNKSIZE - 1) // (CH_CHUNKSIZE * threads_channel)
    all_threads = np.arange(threads_channel).reshape(-1, 1)
    all_blocks = np.arange(channel_blocks).reshape(1, -1)
    min_channels = all_threads + all_blocks * threads_channel
    channel_strides = channel_blocks * threads_channel
    max_steps = (channels - min_channels + channel_strides - 1) // channel_strides
    # Some numba versions can be a bit dumb with respect to integer types,
    # but python int should always work for e.g. dimension arguments
    ch_max_memory = int(min(CH_CHUNKSIZE, max(max_steps.ravel())))

    # Indices to navigate each projection. s is the surface positioning.
    k_vectors = unit_vector_k.astype(numpy_float)
    j_vectors = unit_vector_j.astype(numpy_float)
    s_vectors = (unit_vector_k * (-0.5 * max_k + offsets_k.reshape(-1, 1)) +
                 unit_vector_j * (-0.5 * max_j + offsets_j.reshape(-1, 1))).astype(numpy_float)

    # (0, 1, 2) if x main, (1, 0, 2) if y main, (2, 0, 1) if z main.
    direction_indices = np.stack((direction_0_index.ravel(),
                                  direction_1_index.ravel(),
                                  direction_2_index.ravel()), axis=1)

    # This record array is functionally a dictionary of lists of parameters for each projection.
    # Note that the list of dictionaries approach did not seem to be supported in numba-CUDA.
    # It is possible to use constants defined outside the kernel instead of such a
    # record array, which can be more efficient, but the amount of
    # global constant storage on the chip is limited, and this leads to hard-to-read implementations.
    # Therefore global constants are only used for simple constants like the maximum dimensions of each
    # array, not for per-projection parameters.
    extra_parameters = np.recarray(
        1,
        dtype=[
            ('step_size', 'f4', (len(projections), 3,)),
            ('k_vector', 'f4', (len(projections), 3,)),
            ('j_vector', 'f4', (len(projections), 3,)),
            ('s_vector', 'f4', (len(projections), 3,)),
            ('dimensions', 'int32', (len(projections), 3,)),
            ('direction_indices', 'int32', (len(projections), 3,)),
            ('distance_multiplier', 'f4', (len(projections),)),
        ])

    extra_parameters[0].step_size[:, 0] = 1.
    extra_parameters[0].step_size[:, 1] = step_sizes_1
    extra_parameters[0].step_size[:, 2] = step_sizes_2
    extra_parameters[0].k_vector[:] = k_vectors
    extra_parameters[0].j_vector[:] = j_vectors
    extra_parameters[0].s_vector[:] = s_vectors
    extra_parameters[0].dimensions[:, 0] = dimensions_0
    extra_parameters[0].dimensions[:, 1] = dimensions_1
    extra_parameters[0].dimensions[:, 2] = dimensions_2
    extra_parameters[0].direction_indices[:] = direction_indices
    extra_parameters[0].distance_multiplier[:] = distance_multipliers
    # Fetch dtype of parameters to enable eager compilation.
    record_type = from_dtype(extra_parameters.dtype)
    extra_parameters = cuda.to_device(extra_parameters[0])

    @cuda.jit(device=True, lineinfo=True, fastmath=True, cache=True)
    def bilinear_interpolation(field: np.ndarray[float],
                               directions,
                               positions,
                               dimensions,
                               coordinate_directions,
                               accumulator: np.ndarray[float],
                               min_channel,
                               channel_count,
                               channel_stride):
        """ Kernel for bilinear interpolation. Replaces texture interpolation."""
        # Precompute booleans to ensure control over dtypes, sometimes CUDA makes
        # strange casting decisions unless one is very explicit.
        p1_max_index = dimensions[1] - 1
        p2_max_index = dimensions[2] - 1
        p1_ge_0 = positions[1] >= cuda_float(0)
        p2_ge_0 = positions[2] >= cuda_float(0)
        p1_lt_max_index = positions[1] < cuda_float(p1_max_index)
        p2_lt_max_index = positions[2] < cuda_float(p2_max_index)
        weight_1 = positions[1] - floor(positions[1])
        weight_2 = positions[2] - floor(positions[2])
        weight_1_comp = cuda_float(1) - weight_1
        weight_2_comp = cuda_float(1) - weight_2
        # Bilinear interpolation weights. Uses
        # texture-style edge handling where everything out of bounds is 0.
        t = cuda_x4_type(weight_1_comp * weight_2_comp * cuda_float(p1_ge_0 * p2_ge_0),
                         weight_2_comp * weight_1 * cuda_float(p1_lt_max_index * p2_ge_0),
                         weight_1_comp * weight_2 * cuda_float(p2_lt_max_index * p1_ge_0),
                         weight_1 * weight_2 * cuda_float(p1_lt_max_index * p2_lt_max_index))

        # x0 = x1 if and only if x is the main direction of interation.
        x0 = max(int32(floor(positions[coordinate_directions.x])), 0)
        x1 = x0 + (directions.x != 0) * (x0 < (max_x - 1))

        # y3 is different from y0 when y is not the main direction,
        # but y1 and y2 depend on whether the main direction is
        # x or z.
        y0 = max(int32(floor(positions[coordinate_directions.y])), 0)
        y0_lt_max_index = y0 < (max_y - 1)
        y1 = y0 + (directions.x == 0) * y0_lt_max_index
        y2 = y0 + (directions.x == 2) * y0_lt_max_index
        y3 = y0 + (directions.x != 1) * y0_lt_max_index

        # z0 and z1 work like x0. This is because in the direction tuples
        # (x, y, z), (y, x, z), (z, x, y), y can have any position,
        # but x and z can only be in the positions (0, 1) and (0, 2), respectively.
        z0 = max(int32(floor(positions[coordinate_directions.z])), 0)
        z1 = z0 + (directions.x != 2) * (z0 < (max_z - 1))

        # Bounds checking not required, already taken care of.
        # Explicit bounds checking is marginally more efficient for moderate
        # channel numbers, less efficient for large channel numbers.
        for i in range(channel_count):
            ci = min_channel + i * channel_stride
            accumulator[i] += field[x0, y0, z0, ci] * t.x
            accumulator[i] += field[x1, y1, z0, ci] * t.y
            accumulator[i] += field[x0, y2, z1, ci] * t.z
            accumulator[i] += field[x1, y3, z1, ci] * t.w

    @cuda.jit(void(cuda_float[:, :, :, ::1], cuda_float[:, :, :, ::1], record_type, int32[::1]),
              lineinfo=True, fastmath=True, cache=True)
    def john_transform_inner(field: np.ndarray[float],
                             projection: np.ndarray[float],
                             parameters: np.ndarray,
                             frames):
        """ Performs the John transform of a field. Relies on some
        of pre-defined constants outside the kernel body. """

        # The strided access to channels is complicated.
        # Each thread reads at most ch_max_memory channels, separated by
        # n_threads * n_blocks.
        # For example, for 150 channels, calculation rules would give
        # chunksize 8, 16 threads, and thus 2 blocks.
        # Thread 0 in block 0 then reads channels 0, 32, 64, 96, and 128. (channel_count 5)
        # Thread 1 in block 0 reads 1, 33, 65, 97, and 129. (channel_count 5)
        # Thread 0 in block 1 reads 16, 48, 80, 112, 144. (channel_count 5)
        # Thread 5 in block 1 reads 22, 54, 86, 118. (channel_count 4)
        # In the end we can optimize away 3 CH_CHUNKSIZE when storing memory.
        # 8 - 3 = 5 equals the smallest chunksize that would yield the same number of blocks,
        # this is ch_max_memory.
        min_channel = cuda.threadIdx.x + cuda.blockIdx.x * cuda.blockDim.x
        channel_stride = cuda.gridDim.x * cuda.blockDim.x
        max_steps = (channels - min_channel + channel_stride - 1) // channel_stride
        channel_count = min(ch_max_memory, max_steps)
        if min_channel >= channels:
            return

        # We split the frames into groups with the same main direction, so we need an index array.
        frame_index = cuda.threadIdx.z + cuda.blockDim.z * cuda.blockIdx.z
        frame = frames[frame_index]

        # These are all constants but passed as arguments.
        step_size_1 = parameters['step_size'][frame, 1]
        step_size_2 = parameters['step_size'][frame, 2]
        dimensions = parameters['dimensions'][frame]
        direction_indices = cuda.uint32x3(
            parameters['direction_indices'][frame][0],
            parameters['direction_indices'][frame][1],
            parameters['direction_indices'][frame][2])
        distance_multiplier = parameters['distance_multiplier'][frame]
        coordinate_directions = cuda.uint32x3(
            direction_indices.x != 0,
            (direction_indices.x == 0) + int32(2) * (direction_indices.x == 2),
            int32(2) * (direction_indices.x != 2))
        positions = cuda.local.array(3, cuda_float)

        # It could be advantageous to chunk in the projection direction but
        # this complicates writing to the output by adding race conditions.
        start_slice = int32(0)
        end_slice = start_slice + dimensions[0]
        accumulator = cuda.local.array(ch_max_memory, cuda_float)

        # Channel dimension can be small, k may be near-contiguous, so aim for colaesced reading
        jk = cuda.threadIdx.y + cuda.blockDim.y * cuda.blockIdx.y
        jk_stride = cuda.blockDim.y * cuda.gridDim.y
        total_elements = max_j * max_k
        # JK_CHUNKSIZE = 1 so this is not actually iterated over currently.
        for group_id in range(JK_CHUNKSIZE):
            element_id = jk + group_id * jk_stride
            if element_id >= total_elements:
                break
            k = element_id % max_k
            j = element_id // max_k

            # No need to check k since a % max_k < max_k
            if j >= max_j:
                break

            for i in range(ch_max_memory):
                accumulator[i] = cuda_float(0.)

            # A lot of explicit casting is necessary to avoid float64 and similar
            fj = cuda_float(j) + cuda_float(0.5)
            fk = cuda_float(k) + cuda_float(0.5)

            # Initial coordinates using alignment etc.
            start_position_0 = cuda_float(parameters['s_vector'][frame, direction_indices.x] +
                                          fj * parameters['j_vector'][frame, direction_indices.x] +
                                          fk * parameters['k_vector'][frame, direction_indices.x])
            start_position_1 = cuda_float(parameters['s_vector'][frame, direction_indices.y] +
                                          fj * parameters['j_vector'][frame, direction_indices.y] +
                                          fk * parameters['k_vector'][frame, direction_indices.y])
            start_position_2 = cuda_float(parameters['s_vector'][frame, direction_indices.z] +
                                          fj * parameters['j_vector'][frame, direction_indices.z] +
                                          fk * parameters['k_vector'][frame, direction_indices.z])

            # Centering of coordinate system w.r.t volume and direction.
            # Again explicit casting is needed.
            positions[0] = cuda_float(start_slice) + cuda_float(0.5)
            positions[1] = cuda_float(step_size_1 * (cuda_float(start_slice) -
                                                     cuda_float(0.5) * cuda_float(dimensions[0]) -
                                                     start_position_0 + cuda_float(0.5)) +
                                      start_position_1 + cuda_float(0.5) * cuda_float(dimensions[1]) -
                                      cuda_float(0.5))
            positions[2] = cuda_float(step_size_2 * (cuda_float(start_slice) -
                                                     cuda_float(0.5) * cuda_float(dimensions[0]) -
                                                     start_position_0 + cuda_float(0.5)) +
                                      start_position_2 + cuda_float(0.5) * cuda_float(dimensions[2]) -
                                      cuda_float(0.5))

            for i in range(start_slice, end_slice):
                if ((cuda_float(-1) < positions[1] < cuda_float(dimensions[1])) and
                        (cuda_float(-1) < positions[2] < cuda_float(dimensions[2]))):
                    bilinear_interpolation(field, direction_indices,
                                           positions, dimensions,
                                           coordinate_directions,
                                           accumulator, min_channel,
                                           channel_count,
                                           channel_stride)
                positions[0] += cuda_float(1.0)
                positions[1] += step_size_1
                positions[2] += step_size_2

            for i in range(channel_count):
                ci = min_channel + i * channel_stride
                projection[frame, j, k, ci] = accumulator[i] * distance_multiplier

    @cuda.jit(device=True, lineinfo=True, fastmath=True, cache=True)
    def bilinear_interpolation_few_channels(field: np.ndarray[float],
                                            directions,
                                            positions,
                                            dimensions,
                                            coordinate_directions,
                                            channel_index):
        """ Kernel for bilinear interpolation. Replaces texture interpolation."""
        # See many-channels version for explanation.
        p1_max_index = dimensions[1] - 1
        p2_max_index = dimensions[2] - 1
        p1_ge_0 = positions[1] >= cuda_float(0)
        p2_ge_0 = positions[2] >= cuda_float(0)
        p1_lt_max_index = positions[1] < cuda_float(p1_max_index)
        p2_lt_max_index = positions[2] < cuda_float(p2_max_index)
        weight_1 = positions[1] - floor(positions[1])
        weight_2 = positions[2] - floor(positions[2])
        weight_1_comp = cuda_float(1) - weight_1
        weight_2_comp = cuda_float(1) - weight_2
        t = cuda_x4_type(weight_1_comp * weight_2_comp * cuda_float(p1_ge_0 * p2_ge_0),
                         weight_2_comp * weight_1 * cuda_float(p1_lt_max_index * p2_ge_0),
                         weight_1_comp * weight_2 * cuda_float(p2_lt_max_index * p1_ge_0),
                         weight_1 * weight_2 * cuda_float(p1_lt_max_index * p2_lt_max_index))

        x0 = max(int32(floor(positions[coordinate_directions.x])), 0)
        x1 = x0 + (directions.x != 0) * (x0 < (max_x - 1))

        y0 = max(int32(floor(positions[coordinate_directions.y])), 0)
        y0_lt_max_index = y0 < (max_y - 1)
        y1 = y0 + (directions.x == 0) * y0_lt_max_index
        y2 = y0 + (directions.x == 2) * y0_lt_max_index
        y3 = y0 + (directions.x != 1) * y0_lt_max_index

        z0 = max(int32(floor(positions[coordinate_directions.z])), 0)
        z1 = z0 + (directions.x != 2) * (z0 < (max_z - 1))
        # Bounds checking not required, already taken care of
        return (field[x0, y0, z0, channel_index] * t.x + field[x1, y1, z0, channel_index] * t.y +
                field[x0, y2, z1, channel_index] * t.z + field[x1, y3, z1, channel_index] * t.w)

    @cuda.jit(void(cuda_float[:, :, :, ::1], cuda_float[:, :, :, ::1], record_type, int32[::1]),
              lineinfo=True, fastmath=True, cache=True)
    def john_transform_inner_few_channels(field: np.ndarray[float],
                                          projection: np.ndarray[float],
                                          parameters: np.ndarray,
                                          frames):
        """ Performs the John transform of a field. Relies on a large number
        of pre-defined constants outside the kernel body. """
        # First block similar to multi-channel version.
        frame_index = cuda.threadIdx.z + cuda.blockDim.z * cuda.blockIdx.z
        frame = frames[frame_index]
        step_size_1 = parameters['step_size'][frame, 1]
        step_size_2 = parameters['step_size'][frame, 2]
        dimensions = parameters['dimensions'][frame]
        direction_indices = cuda.uint32x3(
            parameters['direction_indices'][frame][0],
            parameters['direction_indices'][frame][1],
            parameters['direction_indices'][frame][2])
        distance_multiplier = parameters['distance_multiplier'][frame]
        coordinate_directions = cuda.uint32x3(
            direction_indices.x != 0,
            (direction_indices.x == 0) + 2 * (direction_indices.x == 2),
            2 * (direction_indices.x != 2))
        positions = cuda.local.array(3, cuda_float)
        start_slice = 0
        end_slice = start_slice + dimensions[0]
        # Use a common index for channels and k to pack thread reads/writes densely.
        j = cuda.threadIdx.y + cuda.blockDim.y * cuda.blockIdx.y
        kc = cuda.threadIdx.x + cuda.blockDim.x * cuda.blockIdx.x
        channel_index = kc % channels
        k = kc // channels
        if (j >= max_j) or (k >= max_k):
            return

        # See many-channels version
        fj = cuda_float(j) + cuda_float(0.5)
        fk = cuda_float(k) + cuda_float(0.5)

        # Initial coordinates of projection.
        start_position_0 = cuda_float(parameters['s_vector'][frame, direction_indices.x] +
                                      fj * parameters['j_vector'][frame, direction_indices.x] +
                                      fk * parameters['k_vector'][frame, direction_indices.x])
        start_position_1 = cuda_float(parameters['s_vector'][frame, direction_indices.y] +
                                      fj * parameters['j_vector'][frame, direction_indices.y] +
                                      fk * parameters['k_vector'][frame, direction_indices.y])
        start_position_2 = cuda_float(parameters['s_vector'][frame, direction_indices.z] +
                                      fj * parameters['j_vector'][frame, direction_indices.z] +
                                      fk * parameters['k_vector'][frame, direction_indices.z])

        # Centering w.r.t volume.
        positions[0] = cuda_float(start_slice) + cuda_float(0.5)
        positions[1] = cuda_float(step_size_1 * (cuda_float(start_slice) -
                                                 cuda_float(0.5) * cuda_float(dimensions[0]) -
                                                 start_position_0 + cuda_float(0.5)) +
                                  start_position_1 + cuda_float(0.5) * cuda_float(dimensions[1]) -
                                  cuda_float(0.5))
        positions[2] = cuda_float(step_size_2 * (cuda_float(start_slice) -
                                                 cuda_float(0.5) * cuda_float(dimensions[0]) -
                                                 start_position_0 + cuda_float(0.5)) +
                                  start_position_2 + cuda_float(0.5) * cuda_float(dimensions[2]) -
                                  cuda_float(0.5))
        accumulator = cuda_float(0)
        for i in range(start_slice, end_slice):
            if ((cuda_float(-1) < positions[1] < cuda_float(dimensions[1])) and
                    (cuda_float(-1) < positions[2] < cuda_float(dimensions[2]))):
                accumulator += bilinear_interpolation_few_channels(
                    field, direction_indices,
                    positions, dimensions,
                    coordinate_directions,
                    channel_index)
            positions[0] += cuda_float(1.0)
            positions[1] += step_size_1
            positions[2] += step_size_2

        projection[frame, j, k, channel_index] = accumulator * distance_multiplier

    # Divide all projections according to main direction
    frames = list(range(number_of_projections))
    frame_sets = [
        np.array(
            list(filter(lambda x: direction_0_index[x] == i, frames)), dtype=np.int32)
        for i in range(3)]

    john_transform_list = []
    for ii in range(3):
        if len(frame_sets[ii]) == 0:
            john_transform_list.append(None)
            continue
        # Calculate number of blocks based on number of frames
        if channels <= 8:
            tpb = (threads_kc, threads_j, 1)
            bpg = ((max_k * channels + threads_kc - 1) // (threads_kc),
                   (max_j + threads_j - 1) // threads_j,
                   len(frame_sets[ii]))
            john_transform_list.append(john_transform_inner_few_channels[bpg, tpb])
        else:
            tpb = (threads_channel, threads_jk, 1)
            bpg = (((channels + (CH_CHUNKSIZE * threads_channel) - 1) //
                   (threads_channel * CH_CHUNKSIZE)),
                   (max_j * max_k + threads_jk * JK_CHUNKSIZE - 1) // (JK_CHUNKSIZE * threads_jk),
                   len(frame_sets[ii]))
            john_transform_list.append(john_transform_inner[bpg, tpb])

    def transform_with_transfer(field: np.ndarray[float],
                                projections: np.ndarray[float]) -> np.ndarray[float]:
        if _is_cuda_array(field):
            assert field.dtype == 'float32'
            device_field = cuda.as_cuda_array(field)
            transfer_projections = False
        else:
            assert field.dtype == np.float32
            device_field = cuda.to_device(field)
            transfer_projections = True

        if _is_cuda_array(projections):
            assert projections.dtype == 'float32'
            device_projections = cuda.as_cuda_array(projections)
        else:
            assert projections.dtype == np.float32
            device_projections = cuda.to_device(projections)

        for ii in range(3):
            if john_transform_list[ii] is not None:
                john_transform_list[ii](device_field,
                                        device_projections,
                                        extra_parameters,
                                        frame_sets[ii])
        if transfer_projections:
            return device_projections.copy_to_host()
        return device_projections
    return transform_with_transfer


def john_transform_adjoint_cuda(field: np.ndarray[float], projections: np.ndarray[float],
                                unit_vector_p: np.ndarray[float], unit_vector_j: np.ndarray[float],
                                unit_vector_k: np.ndarray[float], offsets_j: np.ndarray[float],
                                offsets_k: np.ndarray[float]):
    """ Frontend for performing the adjoint of the John transform with parallel
    GPU computing.

    Parameters
    ----------
    field
        The field into which the adjoint is projected, with 4 dimensions. The last index should
        have the same size as the last index of ``projections``. Can be either
        a `numpy.ndarray`, or a device array that implements the CUDA array
        interface. If a device array is given, no copying to device is needed.
    projections
        The projections from which the adjoint is calculated.
        The first index runs over the different projection directions. Can be either
        a `numpy.ndarray`, or a device array that implements the CUDA array
        interface. If a device array is given, no copying or synchronization is needed.
    unit_vector_p
        The direction of projection in Cartesian coordinates.
    unit_vector_j
        One of the directions for the pixels of ``projection``.
    unit_vector_k
        The other direction for the pixels of ``projection``.
    offsets_j
        Offsets which align projections in the direction of `j`
    offsets_k
        Offsets which align projections in the direction of `k`.

    Notes
    -----
    For mathematical details, see :func:`~.john_transform.john_transform_adjoint`.
    """
    # Always false as we are sticking to float32
    if False:
        cuda_float = float64
        numpy_float = np.float64
        cuda_x4_type = cuda.float64x4
    else:
        cuda_float = float32
        numpy_float = np.float32
        cuda_x4_type = cuda.float32x4

    max_x, max_y, max_z, channels = field.shape
    number_of_projections, max_j, max_k = projections.shape[:3]

    # CUDA chunking and memory size constants. See non-adjoint for general explanation.
    # Here the single-channel version has a storage vector and strides in Z, whereas
    # the multi-channel version strides in channels.
    if channels == 1:
        threads_channel = int(1)
        threads_z = int(16)
        threads_xy = int(4)
        X_CHUNKSIZE = int(1)
        Y_CHUNKSIZE = int(1)
        Z_CHUNKSIZE = int(4)
        CH_CHUNKSIZE = int(1)
        ch_max_memory = int(1)
    else:
        CH_CHUNKSIZE = min(max(2 ** floor(np.log2(channels // 2)), 1), 8)
        threads_channel = int(min(max(2 ** floor(np.log2(channels / CH_CHUNKSIZE)), 1), 32))
        threads_z = int(max(32 // threads_channel, 4))
        threads_xy = int(1)
        X_CHUNKSIZE = int(1)
        Y_CHUNKSIZE = int(1)
        Z_CHUNKSIZE = int(2)
        channel_blocks = (channels + threads_channel * CH_CHUNKSIZE - 1) // (CH_CHUNKSIZE * threads_channel)
        all_threads = np.arange(threads_channel).reshape(-1, 1)
        all_blocks = np.arange(channel_blocks).reshape(1, -1)
        min_channels = all_threads + all_blocks * threads_channel
        channel_strides = channel_blocks * threads_channel
        max_steps = (channels - min_channels + channel_strides - 1) // channel_strides
        # Some numba versions can be a bit dumb with respect to integer types,
        # but python int should always work for e.g. dimension arguments
        ch_max_memory = int(min(CH_CHUNKSIZE, max(max_steps.ravel())))
    # Projection vectors. s for positioning the projection.
    p_vectors = unit_vector_p.astype(numpy_float)
    k_vectors = unit_vector_k.astype(numpy_float)
    j_vectors = unit_vector_j.astype(numpy_float)
    s_vectors = (unit_vector_k * (-0.5 * max_k + offsets_k.reshape(-1, 1)) +
                 unit_vector_j * (-0.5 * max_j + offsets_j.reshape(-1, 1))).astype(numpy_float)

    # Translate volume steps to normalized projection steps. Can add support for non-square voxels.
    vector_norm = np.einsum('...i, ...i', p_vectors, np.cross(j_vectors, k_vectors))
    norm_j = -np.cross(p_vectors, k_vectors) / vector_norm[..., None]
    norm_k = np.cross(p_vectors, j_vectors) / vector_norm[..., None]
    norm_offset_j = -np.einsum('...i, ...i', p_vectors, np.cross(s_vectors, k_vectors)) / vector_norm
    norm_offset_k = np.einsum('...i, ...i', p_vectors, np.cross(s_vectors, j_vectors)) / vector_norm

    # See forward version for explanation. Adjoint faces bigger issues with global constants since
    # each kernel can potentially end up copying all of the frame-wise values.
    extra_parameters = np.recarray(
        1,
        dtype=[
            ('norm_j', 'f4', (len(projections), 3,)),
            ('norm_k', 'f4', (len(projections), 3,)),
            ('norm_offset_j', 'f4', (len(projections),)),
            ('norm_offset_k', 'f4', (len(projections),)),])

    extra_parameters[0].norm_j = norm_j
    extra_parameters[0].norm_k = norm_k
    extra_parameters[0].norm_offset_j = norm_offset_j
    extra_parameters[0].norm_offset_k = norm_offset_k
    record_type = from_dtype(extra_parameters.dtype)
    extra_parameters = cuda.to_device(extra_parameters[0])

    @cuda.jit(device=True,
              lineinfo=True, fastmath=True, cache=True)
    def bilinear_interpolation_projection(projection: np.ndarray[float],
                                          index, fj, fk,
                                          accumulator: np.ndarray[float],
                                          min_channel, channel_stride, channel_count):
        """ Bilinearly interpolates between 4 neighbouring pixels on each projection.
        """
        # Functions similar to forward bilinear interpolation, but is simpler
        # since we do not need to consider directions of integration, as the
        # integral is always over all projections.
        j_max_ind = max_j - 1
        k_max_ind = max_k - 1
        fj_ge_0 = fj >= cuda_float(0)
        fk_ge_0 = fk >= cuda_float(0)
        fj_lt_max_ind = fj < cuda_float(j_max_ind)
        fk_lt_max_ind = fk < cuda_float(k_max_ind)
        y_weight = fj - floor(fj)
        z_weight = fk - floor(fk)
        y0 = max(int32(floor(fj)), 0)
        y1 = y0 + (y0 < j_max_ind)
        z0 = max(int32(floor(fk)), 0)
        z1 = z0 + (z0 < k_max_ind)
        y_weight_complement = cuda_float(1) - y_weight
        z_weight_complement = cuda_float(1) - z_weight
        t = cuda_x4_type(
            y_weight_complement * z_weight_complement * cuda_float(fj_ge_0 * fk_ge_0),
            z_weight_complement * y_weight * cuda_float(fj_lt_max_ind * fk_ge_0),
            y_weight_complement * z_weight * cuda_float(fk_lt_max_ind * fj_ge_0),
            z_weight * y_weight * cuda_float(fj_lt_max_ind * fk_lt_max_ind))
        for i in range(channel_count):
            ci = min_channel + i * channel_stride
            accumulator[i] += (projection[index, y0, z0, ci] * t.x +
                               projection[index, y1, z0, ci] * t.y +
                               projection[index, y0, z1, ci] * t.z +
                               projection[index, y1, z1, ci] * t.w)

    @cuda.jit(void(cuda_float[:, :, :, ::1], cuda_float[:, :, :, ::1], record_type),
              lineinfo=True, fastmath=True, cache=True)
    def john_transform_adjoint_inner(field: np.ndarray[float],
                                     projection: np.ndarray[float],
                                     parameters: np.ndarray):
        """ Performs the John transform of a field. Relies some pre-defined
        constants outside the kernel body. """
        # See forward version for explanation.
        min_channel = cuda.threadIdx.x + cuda.blockIdx.x * cuda.blockDim.x
        channel_stride = cuda.gridDim.x * cuda.blockDim.x
        max_steps = (channels - min_channel + channel_stride - 1) // channel_stride
        channel_count = min(ch_max_memory, max_steps)
        if min_channel >= channels:
            return
        # x and y are not contiguous, no need to do fancy indexing
        xy = (cuda.blockIdx.z * cuda.blockDim.z + cuda.threadIdx.z)
        y_num_chunks = (max_y + Y_CHUNKSIZE - 1) // Y_CHUNKSIZE
        start_y = (xy % y_num_chunks) * Y_CHUNKSIZE
        end_y = min(start_y + Y_CHUNKSIZE, max_y)
        if start_y >= max_y:
            return
        start_x = (xy // y_num_chunks) * X_CHUNKSIZE
        end_x = min(start_x + X_CHUNKSIZE, max_x)
        if start_x >= max_x:
            return
        # There are tradeoffs between read-write access and amount of local memory needed
        # in structuring this array. Since moving between projections requires a
        # lot of computation it seems that accumulating values for several Z is helpful.
        # Could try out shared memory and 1 block per frame, but probably not better.
        z_acc = cuda.local.array((Z_CHUNKSIZE, ch_max_memory), cuda_float)
        z = cuda.threadIdx.y + cuda.blockDim.y * cuda.blockIdx.y
        z_stride = cuda.gridDim.y * cuda.blockDim.y
        if z >= max_z:
            return

        start_index = 0
        stop_index = number_of_projections
        # Coordinates in projection space relative to xyz-space.
        norm_j = parameters['norm_j'][start_index:stop_index]
        norm_k = parameters['norm_k'][start_index:stop_index]
        norm_offset_j = parameters['norm_offset_j'][start_index:stop_index]
        norm_offset_k = parameters['norm_offset_k'][start_index:stop_index]
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                # Center volume.
                fx = cuda_float(x) - cuda_float(0.5) * cuda_float(max_x) + cuda_float(0.5)
                fy = cuda_float(y) - cuda_float(0.5) * cuda_float(max_y) + cuda_float(0.5)
                fz = cuda_float(z) - cuda_float(0.5) * cuda_float(max_z) + cuda_float(0.5)
                for j in range(Z_CHUNKSIZE):
                    for k in range(channel_count):
                        z_acc[j, k] = cuda_float(0.0)

                for a in range(start_index, stop_index):
                    # Center with respect to each projection direction and alignment.
                    fj = (norm_offset_j[a] + fx * norm_j[a][0] +
                          fy * norm_j[a][1] + fz * norm_j[a][2] - cuda_float(0.5))
                    fk = (norm_offset_k[a] + fx * norm_k[a][0] +
                          fy * norm_k[a][1] + fz * norm_k[a][2] - cuda_float(0.5))
                    for j in range(Z_CHUNKSIZE):
                        # Striding in z is cheaper than striding across projections
                        if (cuda_float(-1) < fj < cuda_float(max_j) and
                                cuda_float(-1) < fk < cuda_float(max_k)):
                            bilinear_interpolation_projection(projection,
                                                              a, fj, fk, z_acc[j],
                                                              min_channel, channel_stride, channel_count)
                        fj += norm_j[a][2] * cuda_float(z_stride)
                        fk += norm_k[a][2] * cuda_float(z_stride)
                for j in range(Z_CHUNKSIZE):
                    # Some threads might be at the very edge.
                    if z + j * z_stride >= max_z:
                        break
                    for k in range(channel_count):
                        field[x, y, z + j * z_stride, min_channel + k * channel_stride] = z_acc[j, k]

    @cuda.jit(device=True,
              lineinfo=True, fastmath=True, cache=True)
    def bilinear_interpolation_projection_one_channel(projection: np.ndarray[float],
                                                      index, fj, fk,
                                                      accumulator: np.ndarray[float],
                                                      i: int):
        # See many-channel and forward versions.
        j_max_ind = max_j - 1
        k_max_ind = max_k - 1
        fj_ge_0 = fj >= cuda_float(0)
        fk_ge_0 = fk >= cuda_float(0)
        fj_lt_max_ind = fj < cuda_float(j_max_ind)
        fk_lt_max_ind = fk < cuda_float(k_max_ind)
        y_weight = fj - floor(fj)
        z_weight = fk - floor(fk)
        y0 = max(int32(floor(fj)), 0)
        y1 = y0 + (y0 < j_max_ind)
        z0 = max(int32(floor(fk)), 0)
        z1 = z0 + (z0 < k_max_ind)
        y_weight_complement = cuda_float(1) - y_weight
        z_weight_complement = cuda_float(1) - z_weight
        t = cuda_x4_type(
            y_weight_complement * z_weight_complement * cuda_float(fj_ge_0 * fk_ge_0),
            z_weight_complement * y_weight * cuda_float(fj_lt_max_ind * fk_ge_0),
            y_weight_complement * z_weight * cuda_float(fk_lt_max_ind * fj_ge_0),
            z_weight * y_weight * cuda_float(fj_lt_max_ind * fk_lt_max_ind))
        accumulator[i] += (projection[index, y0, z0, 0] * t.x +
                           projection[index, y1, z0, 0] * t.y +
                           projection[index, y0, z1, 0] * t.z +
                           projection[index, y1, z1, 0] * t.w)

    @cuda.jit(void(cuda_float[:, :, :, ::1], cuda_float[:, :, :, ::1], record_type),
              lineinfo=True, fastmath=True, cache=True)
    def john_transform_adjoint_one_channel(field: np.ndarray[float],
                                           projection: np.ndarray[float],
                                           parameters: np.ndarray):
        """ Performs the John transform of a single-channel field."""

        # This entire function is very similar to the multi-channel one, except that
        # striding happens only in Z.
        z = cuda.threadIdx.y + cuda.blockDim.y * cuda.blockIdx.y
        z_stride = cuda.gridDim.y * cuda.blockDim.y
        xy = (cuda.blockIdx.z * cuda.blockDim.z + cuda.threadIdx.z)
        y_num_chunks = (max_y + Y_CHUNKSIZE - 1) // Y_CHUNKSIZE
        start_y = (xy % y_num_chunks) * Y_CHUNKSIZE
        end_y = min(start_y + Y_CHUNKSIZE, max_y)
        if start_y >= max_y:
            return
        start_x = (xy // y_num_chunks) * X_CHUNKSIZE
        end_x = min(start_x + X_CHUNKSIZE, max_x)
        if start_x >= max_x:
            return
        # Stride in z.
        z_acc = cuda.local.array(Z_CHUNKSIZE, cuda_float)
        start_index = 0
        stop_index = number_of_projections
        norm_j = parameters['norm_j'][start_index:stop_index]
        norm_k = parameters['norm_k'][start_index:stop_index]
        norm_offset_j = parameters['norm_offset_j'][start_index:stop_index]
        norm_offset_k = parameters['norm_offset_k'][start_index:stop_index]
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                # Center of voxel and coordinate system.
                fx = cuda_float(x) - cuda_float(0.5) * cuda_float(max_x) + cuda_float(0.5)
                fy = cuda_float(y) - cuda_float(0.5) * cuda_float(max_y) + cuda_float(0.5)
                fz = cuda_float(z) - cuda_float(0.5) * cuda_float(max_z) + cuda_float(0.5)
                for j in range(Z_CHUNKSIZE):
                    z_acc[j] = 0.0
                for a in range(start_index, stop_index):
                    # Center with respect to projection.
                    fj = (norm_offset_j[a] + fx * norm_j[a][0] + fy *
                          norm_j[a][1] + fz * norm_j[a][2] - cuda_float(0.5))
                    fk = (norm_offset_k[a] + fx * norm_k[a][0] + fy *
                          norm_k[a][1] + fz * norm_k[a][2] - cuda_float(0.5))
                    for i in range(Z_CHUNKSIZE):
                        if (cuda_float(-1) < fj < cuda_float(max_j) and
                                cuda_float(-1) < fk < cuda_float(max_k)):
                            bilinear_interpolation_projection_one_channel(
                                projection,
                                a, fj, fk,
                                z_acc, i)
                        fj += norm_j[a][2] * cuda_float(z_stride)
                        fk += norm_k[a][2] * cuda_float(z_stride)
                for i in range(Z_CHUNKSIZE):
                    if z + i * z_stride < max_z:
                        field[x, y, z + i * z_stride, 0] = z_acc[i]
    num_chunks_x = (max_x + X_CHUNKSIZE - 1) // X_CHUNKSIZE
    num_chunks_y = (max_y + Y_CHUNKSIZE - 1) // Y_CHUNKSIZE
    xy_chunks = num_chunks_x * num_chunks_y
    bpg = ((channels + threads_channel * CH_CHUNKSIZE - 1) // (CH_CHUNKSIZE * threads_channel),
           (max_z + Z_CHUNKSIZE * threads_z - 1) // (threads_z * Z_CHUNKSIZE),
           (xy_chunks + threads_xy - 1) // threads_xy,
           )
    tpb = (threads_channel, threads_z, threads_xy)
    if channels > 1:
        john_transform_adjoint_grid = john_transform_adjoint_inner[bpg, tpb]
    else:
        john_transform_adjoint_grid = john_transform_adjoint_one_channel[bpg, tpb]

    def transform_with_transfer(field: np.ndarray[float],
                                projections: np.ndarray[float]) -> np.ndarray[float]:
        if _is_cuda_array(field):
            assert field.dtype == 'float32'
            device_field = cuda.as_cuda_array(field)
        else:
            assert field.dtype == np.float32
            device_field = cuda.to_device(field)

        if _is_cuda_array(projections):
            assert projections.dtype == 'float32'
            device_projections = cuda.as_cuda_array(projections)
            transfer_field = False
        else:
            assert projections.dtype == np.float32
            device_projections = cuda.to_device(projections)
            transfer_field = True
        john_transform_adjoint_grid(device_field,
                                    device_projections,
                                    extra_parameters)
        if transfer_field:
            return device_field.copy_to_host()
        return device_field

    return transform_with_transfer
