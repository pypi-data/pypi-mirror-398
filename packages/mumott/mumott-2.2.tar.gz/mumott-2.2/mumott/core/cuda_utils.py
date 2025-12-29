import logging

from typing import Tuple

from numba import cuda
from numpy.typing import DTypeLike, NDArray

from numpy import float32, float64

logger = logging.getLogger(__name__)


def cuda_calloc(shape: Tuple, dtype: DTypeLike = float32) -> NDArray:
    """ Function for creating a zero-initialized
    device array using ``numba.cuda``, as it provides no
    native method for doing so.

    Paramters
    ---------
    shape
        A ``tuple`` with the shape of the desired
        device array.
    dtype
        A ``numba`` or ``numpy`` dtype. ``float64``
        is turned into ``float32``.
    """
    if dtype == float64:
        dtype = float32
    array = cuda.device_array(shape, dtype=dtype)

    size = array.size

    @cuda.jit
    def _calloc(array: NDArray):
        """ Initializes the given array. Depends on
        `size` being predefined.

        Parameters
        ----------
        array
            A device array which is initialized with zeros.
        """
        x = cuda.grid(1)
        if x < size:
            array[x] = 0

    # Use 512 threads per block, and blocks per grid based on array size.
    tpb = 512
    bpg = (size + tpb - 1) // tpb
    _calloc[bpg, tpb](array.ravel())
    return array
