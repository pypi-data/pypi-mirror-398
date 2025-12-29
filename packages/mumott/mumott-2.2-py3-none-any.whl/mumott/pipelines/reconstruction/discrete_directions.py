import logging
import sys

import numpy as np
from numpy.typing import NDArray
import tqdm
from types import SimpleNamespace

from mumott.data_handling import DataContainer
from mumott.methods.basis_sets import NearestNeighbor
from mumott.pipelines.reconstruction.sirt import run_sirt

logger = logging.getLogger(__name__)


def run_discrete_directions(data_container: DataContainer,
                            directions: NDArray[float],
                            use_gpu: bool = False,
                            maxiter: int = 20,
                            no_tqdm: bool = False,
                            ):
    """A reconstruction pipeline for the :term:`discrete directions <DD>` algorithm, which is
    similar the the algorithms first descibed in [Schaff2015]_.

    Parameters
    ----------
    data_container
        The :class:`DataContainer <mumott.data_handling.DataContainer>`
        from loading the data set of interest.
    directions
        A N by 3 Numpy array of unit-vectors descibing a grid covering the half unit sphere.
    use_gpu
        Whether to use GPU resources in computing the projections.
        Default is ``False``. If set to ``True``, the method will use
        :class:`SAXSProjectorCUDA <mumott.methods.projectors.SAXSProjectorCUDA>`.
    maxiter
        Maximum number of iterations for the gradient descent solution.
    no_tqdm:
        Flag whether ot not to print a progress bar for the reconstruction.
    """
    basis_set = NearestNeighbor(directions)
    basis_set.integration_mode = 'midpoint'
    output_coefficients = np.zeros((*data_container.geometry.volume_shape, len(basis_set)))

    if no_tqdm:
        iterator = range(len(basis_set))
    else:
        iterator = tqdm.tqdm(range(len(basis_set)), file=sys.stdout)

    for ii in iterator:
        sub_geometry, data_tuple = basis_set.get_sub_geometry(ii, data_container.geometry, data_container)

        if data_tuple is None:
            continue

        fake_data_container = SimpleNamespace(
            projections=SimpleNamespace(weights=data_tuple[1][..., np.newaxis]),
            geometry=sub_geometry,
            weights=data_tuple[1][..., np.newaxis])

        result = run_sirt(fake_data_container,
                          maxiter=maxiter,
                          enforce_non_negativity=True,
                          use_gpu=use_gpu,
                          use_absorbances=True,
                          absorbances=data_tuple[0][..., np.newaxis],
                          no_tqdm=True)
        output_coefficients[..., ii] = result['result']['x'][..., 0]

    return dict(result={'x' : output_coefficients}, basis_set=basis_set)
