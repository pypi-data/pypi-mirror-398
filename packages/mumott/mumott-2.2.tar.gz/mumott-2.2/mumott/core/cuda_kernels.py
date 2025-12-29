import numba
from numba import cuda


def cuda_weighted_difference(shape: tuple[int]):
    """ Compiles a CUDA kernel for a 'weighted difference', i.e.
    ``a = (a - b) * c``. For example, ``a`` could be an approximation of ``b``,
    and ``c`` could be the weight to assign to the residual of ``a`` and ``b``.

    Parameters
    ----------
    shape
        The shape of ``a``, ``b``, and ``c``.

    Returns
    -------
        A CUDA callable that takes 3 inputs, ``data``, ``value``,
        and ``weights``, and stores the output in ``value``.
        The difference is computed as ``((value * weights) - data * weights)``.
    """
    tpb = (4, 4, 4)
    bpg = (shape[0] // tpb[0] + 1,
           shape[1] // tpb[1] + 1,
           shape[2] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=True),
                         numba.float32[:, :, :, ::1],
                         numba.types.Array(numba.float32, 4, 'C', readonly=True)))
    def weighted_difference(data, value, weights):
        i, j, k = cuda.grid(3)
        if (i < shape[0]) and (j < shape[1]) and (k < shape[2]):
            for h in range(shape[3]):
                # Use intrinsic fused multiply-add
                d = -data[i, j, k, h] * weights[i, j, k, h]
                value[i, j, k, h] = cuda.fma(value[i, j, k, h], weights[i, j, k, h], d)

    return weighted_difference[bpg, tpb]


def cuda_weighted_sign(shape: tuple[int], delta: float = 0.):
    """ Compiles a CUDA kernel for a 'weighted sign', i.e.
    ``a = sgn(a - b) * c``. For example, ``a`` could be an approximation of ``b``,
    and ``c`` could be the weight to assign to the residual of ``a`` and ``b``.

    If ``delta`` is set to be greater than 0, then this function will return
    ``(a - b) * c / (2 * delta)`` if ``abs(a - b) < delta``.

    Parameters
    ----------
    shape
        The shape of ``a``, ``b``, and ``c``.
    delta
        Threshold at which to switch from sign to actual difference.

    Returns
    -------
        A CUDA callable that takes 3 inputs, ``data``, ``value``,
        and ``weights``, and stores the output in ``value``.
    """
    tpb = (4, 4, 4)
    bpg = (shape[0] // tpb[0] + 1,
           shape[1] // tpb[1] + 1,
           shape[2] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=True),
                         numba.float32[:, :, :, ::1],
                         numba.types.Array(numba.float32, 4, 'C', readonly=True)))
    def weighted_difference(data, value, weights):
        i, j, k = cuda.grid(3)
        if (i < shape[0]) and (j < shape[1]) and (k < shape[2]):
            for h in range(shape[3]):
                # Use intrinsic fused multiply-add
                d = value[i, j, k, h] - data[i, j, k, h]
                ad = abs(d)
                if (ad < delta) and (delta > 0):
                    scale = weights[i, j, k, h] * ad / (2 * delta)
                else:
                    scale = weights[i, j, k, h]
                value[i, j, k, h] = cuda.libdevice.copysignf(scale, d)

    return weighted_difference[bpg, tpb]


def cuda_scaled_difference(shape: tuple[int]):
    """ Compiles a CUDA kernel for a 'scaled difference', i.e.,
    ``a -= b * c`` for 3 4-dimensional arrays, e.g. a data, gradient, and preconditioner
    array.

    Parameters
    ----------
    shape
        The shape of ``a`` and ``b`` as a 4-tuple.

    Returns
    -------
        A CUDA callable which takes 3 inputs, a ``gradient``,
        ``value``, and ``scaling``. The output is stored in
        ``value``. All inputs must be 4D arrays with shape ``shape``.
    """
    tpb = (4, 4, 4)
    bpg = (shape[1] // tpb[0] + 1,
           shape[2] // tpb[1] + 1,
           shape[3] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=True),
                         numba.float32[:, :, :, ::1],
                         numba.types.Array(numba.float32, 4, 'C', readonly=True)))
    def scaled_difference(gradient, value, scaling):
        i, j, k = cuda.grid(3)
        if (i < shape[1]) and (j < shape[2]) and (k < shape[3]):
            for h in range(shape[0]):
                value[h, i, j, k] -= gradient[h, i, j, k] * scaling[h, i, j, k]

    return scaled_difference[bpg, tpb]


def cuda_sum(shape: tuple[int]):
    """ Computes a CUDA kernel for the summation of 2 4D arrays,
    e.g. 2 gradients.

    Parameters
    ----------
    shape
        A 4-tuple of the shape of the two gradients.

    Returns
    -------
        A CUDA callable which takes an ``old_gradient`` input/output,
        and a ``new_gradient`` input. The sum is stored in-place in
        ``old_gradient``.

    """
    tpb = (4, 4, 4)
    bpg = (shape[1] // tpb[0] + 1,
           shape[2] // tpb[1] + 1,
           shape[3] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=False),
                         numba.types.Array(numba.float32, 4, 'C', readonly=True)))
    def cuda_sum(old_gradient, new_gradient):
        i, j, k = cuda.grid(3)
        if (i < shape[1]) and (j < shape[2]) and (k < shape[3]):
            for h in range(shape[0]):
                old_gradient[h, i, j, k] += new_gradient[h, i, j, k]

    return cuda_sum[bpg, tpb]


def cuda_difference(shape: tuple[int]):
    """ Computes a CUDA kernel for the difference of 2 4D arrays,
    e.g. a gradient and a value

    Parameters
    ----------
    shape
        A 4-tuple of the shape of the two gradients.

    Returns
    -------
        A CUDA callable which takes an ``old_gradient`` input/output,
        and a ``new_gradient`` input. The sum is stored in-place in
        ``old_gradient``.

    """
    tpb = (4, 4, 4)
    bpg = (shape[1] // tpb[0] + 1,
           shape[2] // tpb[1] + 1,
           shape[3] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=False),
                         numba.types.Array(numba.float32, 4, 'C', readonly=True)))
    def cuda_difference(value, gradient):
        i, j, k = cuda.grid(3)
        if (i < shape[1]) and (j < shape[2]) and (k < shape[3]):
            for h in range(shape[0]):
                value[h, i, j, k] -= gradient[h, i, j, k]

    return cuda_difference[bpg, tpb]


def cuda_framewise_contraction(shape: tuple[int], rows: int, columns: int):
    """ Computes a CUDA kernel for the framewise contraction of a tensor field
    and a matrix stack: ``out[i, j, k, g] = sum_h(field[i, j, k, h], matrix[i, g, h])``.
    In ``numpy.einsum`` notation, this would be ``'ijkh, igh -> ijkg'``.

    Parameters
    ----------
    shape
        A 3-tuple giving the shapes of the first three dimensions of the field (``(i, j, k)`` dimensions).
    rows
        The number of rows in the matrix/output vector length (``g`` dimension).
    columns
        The number of columns in the matrix/input vector length (``h`` dimension).

    Returns
    -------
        A CUDA callable which takes ``field`` and ``matrix`` inputs,
        and ``out`` output.
    """
    tpb = (8, 8)
    bpg = (shape[0] // tpb[0] + 1,
           shape[1] // tpb[1] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=True),
                         numba.types.Array(numba.float32, 3, 'C', readonly=True),
                         numba.types.Array(numba.float32, 4, 'C', readonly=False)))
    def cuda_framewise_contraction(field, matrix, out):
        i, j = cuda.grid(2)
        if (i < shape[0]) and (j < shape[1]):
            temp = cuda.local.array(rows, numba.float32)
            for k in range(shape[2]):
                for g in range(rows):
                    temp[g] = 0.
                for h in range(columns):
                    tf = field[i, j, k, h]
                    for g in range(rows):
                        temp[g] += matrix[i, g, h] * tf
                for g in range(rows):
                    out[i, j, k, g] = temp[g]

    return cuda_framewise_contraction[bpg, tpb]


def cuda_framewise_contraction_adjoint(shape: tuple[int], rows: int, columns: int):
    """ Computes a CUDA kernel for the adjoint of the framewise
    contraction of a tensor field and a matrix stack:
    ``out[i, j, k, h] = sum_h(field[i, j, k, g], matrix[i, g, h])``.
    In ``numpy.einsum`` notation, this would be ``'ijkg, igh -> ijkh'``.

    Parameters
    ----------
    shape
        A 3-tuple giving the shapes of the first three dimensions of the field (``(i, j, k)`` dimensions).
    rows
        The number of rows in the matrix/input vector length (``g`` dimension).
    columns
        The number of columns in the matrix/output vector length (``h`` dimension).

    Returns
    -------
        A CUDA callable which takes ``field`` and ``matrix`` inputs,
        and ``out`` output.
    """
    tpb = (8, 8)
    bpg = (shape[0] // tpb[0] + 1,
           shape[1] // tpb[1] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=True),
                         numba.types.Array(numba.float32, 3, 'C', readonly=True),
                         numba.types.Array(numba.float32, 4, 'C', readonly=False)))
    def cuda_framewise_contraction_adjoint(field, matrix, out):
        i, j = cuda.grid(2)
        if (i < shape[0]) and (j < shape[1]):
            temp = cuda.local.array(columns, numba.float32)
            for k in range(shape[2]):
                for h in range(columns):
                    temp[h] = 0.
                for g in range(rows):
                    tg = field[i, j, k, g]
                    for h in range(columns):
                        temp[h] += matrix[i, g, h] * tg
                for h in range(columns):
                    out[i, j, k, h] = temp[h]

    return cuda_framewise_contraction_adjoint[bpg, tpb]


def cuda_rescale_array(shape: tuple[int]):
    """ Compiles a CUDA kernel for the rescaling of a gradient with a momentum term,
    or similar rescaling of a 4-dimensional array with another 4-dimensional array.

    Parameters
    ----------
    shape
        The shape of the coefficients to which the gradient will ultimately be applied.

    Returns
    -------
        A compiled CUDA callable which takes one array, an input/output
        ``gradient``.
    """

    tpb = (4, 4, 4)
    bpg = (shape[1] // tpb[0] + 1,
           shape[2] // tpb[1] + 1,
           shape[3] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=False),
                         numba.types.Array(numba.float32, 4, 'C', readonly=True)))
    def scale(gradient, scaling):
        i, j, k = cuda.grid(3)
        if (i < shape[1]) and (j < shape[2]) and (k < shape[3]):
            for h in range(shape[0]):
                gradient[h, i, j, k] *= scaling[h, i, j, k]

    return scale[bpg, tpb]


def cuda_lower_bound(shape: tuple[int], lower_bound: float = 0.):
    """ Compiles a CUDA kernel for the enforcement of a lower bound to a 4-dimensional field.
    The computation is ``field[i, j, k, h] = max(field[i, j, k, h], lower_bound)``.

    Parameters
    ----------
    shape
        The shape of the coefficients to threshold with the lower bound.

    Returns
    -------
        A compiled CUDA callable which takes one array, an input/output
        ``field``.
    """

    tpb = (4, 4, 4)
    bpg = (shape[0] // tpb[0] + 1,
           shape[1] // tpb[1] + 1,
           shape[2] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=False)))
    def threshold(field):
        i, j, k = cuda.grid(3)
        lb = numba.float32(lower_bound)
        if (i < shape[0]) and (j < shape[1]) and (k < shape[2]):
            for h in range(shape[3]):
                field[i, j, k, h] = cuda.libdevice.fmax(field[i, j, k, h], lb)

    return threshold[bpg, tpb]


def cuda_rescale(shape: tuple[int], momentum: float = 0.9):
    """ Compiles a CUDA kernel for the rescaling of a gradient with a momentum term,
    or similar rescaling of a 4-dimensional array with a scalar.

    Parameters
    ----------
    shape
        The shape of the coefficients to which the gradient will ultimately be applied.
    momentum
        The momentum weight, from 0 to 1. Default is ``0.9``.

    Returns
    -------
        A compiled CUDA callable which takes one array, an input/output
        ``gradient``.
    """

    tpb = (4, 4, 4)
    bpg = (shape[1] // tpb[0] + 1,
           shape[2] // tpb[1] + 1,
           shape[3] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=False)))
    def scale(gradient):
        i, j, k = cuda.grid(3)
        scaling = numba.float32(momentum)
        if (i < shape[1]) and (j < shape[2]) and (k < shape[3]):
            for h in range(shape[0]):
                gradient[h, i, j, k] *= scaling

    return scale[bpg, tpb]


def cuda_l1_gradient(shape: tuple[int], weight: float = 1e-4):
    """ Compiles a CUDA kernel for the gradient of an L1 regularizer.

    Parameters
    ----------
    shape
        The shape of the coefficients to which the gradient will ultimately be applied.
    weight
        The weight of the L1 gradient.

    Returns
    -------
        A compiled CUDA callable which takes two arrays, an input
        ``coefficients`` array and an output ``gradient`` array, both of
        shape ``shape`` and dtype ``float32``.
    """
    tpb = (4, 4, 4)
    bpg = (shape[0] // tpb[0] + 1,
           shape[1] // tpb[1] + 1,
           shape[2] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=True),
                         numba.types.Array(numba.float32, 4, 'C', readonly=False)))
    def l1_gradient(coefficients, gradient):
        i, j, k = cuda.grid(3)
        scale = numba.float32(weight)
        if (i < shape[0]) and (j < shape[1]) and (k < shape[2]):
            for h in range(shape[3]):
                # Use CUDA intrinsic for scaled sign function.
                gradient[i, j, k, h] += cuda.libdevice.copysignf(scale, coefficients[i, j, k, h])

    return l1_gradient[bpg, tpb]


def cuda_tv_gradient(shape: tuple[int], weight: float = 1e-4):
    """ Compiles a CUDA kernel for the gradient of a Total Variation regularizer.
    Gradient values at edges are sets to 0.

    Parameters
    ----------
    shape
        The shape of the coefficients to which the gradient will ultimately be applied.
    weight
        The weight of the TV gradient.

    Returns
    -------
        A compiled CUDA callable which takes two arrays, an input
        ``coefficients`` array and an output ``gradient`` array, both of
        shape ``shape`` and dtype ``float32``. The ``gradient`` array
        will have the value of the TV gradient added to it.
    """
    tpb = (4, 4, 4)
    bpg = (shape[0] // tpb[0] + 1,
           shape[1] // tpb[1] + 1,
           shape[2] // tpb[2] + 1)

    @cuda.jit(numba.void(numba.types.Array(numba.float32, 4, 'C', readonly=True),
                         numba.types.Array(numba.float32, 4, 'C', readonly=False)))
    def tv_gradient(coefficients, gradient):
        i, j, k = cuda.grid(3)
        scale = numba.float32(weight)
        if (i < shape[0]) and (j < shape[1]) and (k < shape[2]):
            # Zero edges to simplify edge handling while maintaining edge conditions
            if (((i == 0) or (i == shape[0] - 1) or
                 (j == 0) or (j == shape[1] - 1)) or (k == 0) or (k == shape[2] - 1)):
                for h in range(shape[3]):
                    gradient[i, j, k, h] = 0.
                return
            else:
                for h in range(shape[3]):
                    numerator = 6 * coefficients[i, j, k, h]
                    denominator = 0
                    numerator -= coefficients[i - 1, j, k, h]
                    numerator -= coefficients[i + 1, j, k, h]
                    numerator -= coefficients[i, j - 1, k, h]
                    numerator -= coefficients[i, j + 1, k, h]
                    numerator -= coefficients[i, j, k - 1, h]
                    numerator -= coefficients[i, j, k + 1, h]
                    denominator += (coefficients[i, j, k, h] - coefficients[i - 1, j, k, h]) ** 2
                    denominator += (coefficients[i, j, k, h] - coefficients[i + 1, j, k, h]) ** 2
                    denominator += (coefficients[i, j, k, h] - coefficients[i, j - 1, k, h]) ** 2
                    denominator += (coefficients[i, j, k, h] - coefficients[i, j + 1, k, h]) ** 2
                    denominator += (coefficients[i, j, k, h] - coefficients[i, j, k - 1, h]) ** 2
                    denominator += (coefficients[i, j, k, h] - coefficients[i, j, k + 1, h]) ** 2
                    if denominator > 0.:
                        # Use intrinsic for square root
                        gradient[i, j, k, h] += \
                                scale * numerator / cuda.libdevice.fsqrt_rn(denominator)

    return tv_gradient[bpg, tpb]
