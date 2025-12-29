import logging
import sys
from typing import Any, Callable, Set

import numpy as np
import tqdm
from skimage.registration import phase_cross_correlation as phase_xcorr
from scipy.ndimage import center_of_mass

from mumott.data_handling import DataContainer
from .reconstruction import run_mitra

logger = logging.getLogger(__name__)
rng = np.random.default_rng()


def _relax_offsets(offsets: np.ndarray[float]) -> np.ndarray[float]:
    """ Internal convenience function for adding a stochastic relaxation factor
    to offsets. """
    diffs = offsets - offsets.mean()
    stds = np.std(diffs)
    relaxations = np.sign(diffs) * \
        np.fmax(0, abs(diffs) - abs(stds * rng.standard_normal(diffs.shape)))
    return relaxations


def _shift_toward_center(center_of_mass_2d: np.ndarray[float],
                         center_of_mass_3d: np.ndarray[float],
                         j_vector: np.ndarray[float],
                         k_vector: np.ndarray[float],
                         j_offset: float,
                         k_offset: float) -> np.ndarray[float]:
    """ Internal convenience function for aligning centers of mass. """
    com_2d_xyz = j_vector * (center_of_mass_2d[0] + j_offset) + \
        k_vector * (center_of_mass_2d[1] + k_offset)
    com_3d_diff = com_2d_xyz - center_of_mass_3d
    shifts = np.array((np.dot(j_vector, com_3d_diff), np.dot(k_vector, com_3d_diff)))
    return shifts


def run_phase_matching_alignment(data_container: DataContainer,
                                 ignored_subset: Set[int] = None,
                                 projection_cropping: tuple[slice, slice] = np.s_[:, :],
                                 reconstruction_pipeline: Callable = run_mitra,
                                 reconstruction_pipeline_kwargs: dict[str, any] = None,
                                 use_gpu: bool = False,
                                 use_absorbances: bool = True,
                                 maxiter: int = 20,
                                 upsampling: int = 1,
                                 shift_tolerance: float = None,
                                 shift_cutoff: float = None,
                                 relative_sample_size: float = 1.0,
                                 relaxation_weight: float = 0.0,
                                 center_of_mass_shift_weight: float = 0.0,
                                 align_j: bool = True,
                                 align_k: bool = True) -> dict[str, Any]:
    r"""A pipeline for alignment using the phase cross-correlation method as implemented
    by `scikit-image <https://scikit-image.org>`_.

    For details on the cross-correlation algorithm, see
    `this article by Guizar-Sicairos et al., (2008) <https://doi.org/10.1364/OL.33.000156>`_.
    Briefly, the algorithm calculates the cross-correlation between a reference image (the data) and the
    corresponding projection of a reconstruction, and finds the shift that would result in
    maximal correlation between the two. It supports large upsampling factors with
    very little computational overhead.

    This implementation applies this algorithm to a randomly sampled subset of the projections in each
    iteration, and adds to this two smoothing terms – a stochastic relaxation term, and a
    shift toward the center of mass of the reconstruction. These terms are added partly to reduce the
    determinism in the algorithm, and partly to improve the performance when no
    upsampling is used.

    The relaxation term is given by

    .. math::
        d(x_i) = \text{sgn}(x_i) \cdot \text{max}
            (0, \vert x_i \vert - \vert \mathcal{N}(\overline{\mu}(x), \sigma(x)) \vert)

    where :math:`x_i` is a given offset and :math:`\mathcal{N}(\mu, \sigma)` is a random variable
    from a normal distribution with mean :math:`\mu` and standard deviation :math:`\sigma`.
    :math:`x_i` is then updated by

    .. math::
        x_i \leftarrow x_i + \lambda \cdot \text{sign}(d(x_i)) \cdot \text{max}(1, \vert d(x_i) \vert)

    where :math:`\lambda` is the :attr:`relaxation_weight`.

    The shift toward the center of mass is given by

    .. math::
        t(x_i) = \mathbf{v_i} \cdot (\mathbf{v_i}(\text{CoM}(P_i) + x_i)_j - \text{CoM}(R))

    where :math:`\mathbf{v_i}` is the three-dimensional basis vector that maps out :math:`x_i`.
    This expression assumes that the basis vectors of the two shift directions are orthogonal,
    but the general expression is similar. The term :math:`t(x_i)` is then used to update
    :math:`x_i` similarly to :math:`d(x_i)`.


    Parameters
    ----------
    data_container
        The data container from loading the data set of interest. Note that the offset
        factors in :class:`data_container.geometry <mumott.core.geometry.Geometry>` will be
        modified during the alignment.
    ignored_subset
        A subset of projection numbers which will not have their alignment modified.
        The subset is still used in the reconstruction.
    projection_cropping
        A tuple of two slices (``slice``), which specify the cropping of the
        ``projection`` and ``data``. For example, to clip the first and last 5
        pixels in each direction, set this parameter to ``(slice(5, -5), slice(5, -5))``.
    reconstruction_pipeline
        A ``callable``, typically from the :ref:`reconstruction pipelines <reconstruction_pipelines>`,
        that performs the reconstruction at each alignment iteration. Must return a dictionary with a
        entry labelled ``'result'``, which has an entry labelled ``'x'`` containing the
        reconstruction. Additionally, it must expose a ``'weights'`` entry containing the
        weights used during the reconstruction as well as a :ref:`Projector object <projectors>`
        under the keyword ``'projector'``.
        If the pipeline supports the :attr:`use_absorbances` keyword argument, then an
        ``absorbances`` entry must also be exposed. If the pipeline supports using multi-channel data,
        absorbances, then a :ref:`basis set object <basis_sets>` must be
        available under ``'basis_set'``.
    reconstruction_pipeline_kwargs
        Keyword arguments to pass to :attr:`reconstruction_pipeline`. If ``'data_container'`` or
        ``'use_gpu'`` are set as keys, they will override :attr:`data_container` and :attr:`use_gpu`
    use_gpu
        Whether to use GPU resources in computing the reconstruction.
        Default is ``False``. Will be overridden if set in :attr:`reconstruction_pipeline_kwargs`.
    use_absorbances
        Whether to use the absorbances to compute the reconstruction and align the projections.
        Default is ``True``. Will be overridden if set in :attr:`reconstruction_pipeline_kwargs`.
    maxiter
        Maximum number of iterations for the alignment.
    upsampling
        Upsampling factor during alignment. If used, any masking in :attr:`data_container.weights` will
        be ignored, but :attr:`projection_clipping` will still be used. The suggested range of use
        is ``[1, 20]``.
    shift_tolerance
        Tolerance for the the maximal shift distance of each iteration of the alignment.
        The alignment will terminate when the maximal shift falls below this value.
        The maximal shift is the largest Euclidean distance any one projection is shifted by.
        Default value is ``1 / upsampling``.
    shift_cutoff
        Largest permissible shift due to cross-correlation in each iteration, as measured by the
        Euclidean distance. Larger shifts will be rescaled so as to not exceed this value.
        Default value is ``5 / upsampling``.
    relative_sample_size
        Fraction of projections to align in each iteration. At each alignment iteration,
        ``ceil(number_of_projections * relative_sample_size)`` will be randomly selected for alignment.
        If set to ``1``, all projections will be aligned at each iteration.
    relaxation_weight
        A relaxation parameter for stochastic relaxation; the larger this weight is, the more shifts will tend
        toward the mean shift in each direction. The relaxation step size in each direction at each iteration
        cannot be larger than this weight. This is :math:`\lambda` in the expression given above.
    center_of_mass_shift_weight
        A parameter that controls the tendency for the projection center of mass
        to be shifted toward the reconstruction center of mass. The relaxation step size in each direction
        at each iteration
        cannot be larger than this weight.
    align_j
        Whether to align in the ``j`` direction. Default is ``True``.
    align_k
        Whether to align in the ``k`` direction. Default is ``True``.

    Returns
    -------
        A dictionary with three entries for inspection:
            reconstruction
                The reconstruction used in the last alignment step.
            projections
                Projections of the ``reconstruction``.
            reference
                The reference image derived from the data used to align the ``projections``.
    """
    # This is not strictly needed since we don't modify the list, but having a mutable default is bad.
    if ignored_subset is None:
        ignored_subset = set()
    if not isinstance(ignored_subset, set):
        raise TypeError(f'ignored_subset must be a set, but a {type(ignored_subset).__name__} was given!')

    # Allow user to override arguments given to this function with pipeline kwargs.
    if reconstruction_pipeline_kwargs is None:
        reconstruction_pipeline_kwargs = dict()
    reconstruction_pipeline_kwargs['data_container'] = \
        reconstruction_pipeline_kwargs.get('data_container', data_container)
    reconstruction_pipeline_kwargs['use_gpu'] = reconstruction_pipeline_kwargs.get('use_gpu', use_gpu)
    reconstruction_pipeline_kwargs['use_absorbances'] = \
        reconstruction_pipeline_kwargs.get('use_absorbances', use_absorbances)
    reconstruction_pipeline_kwargs['no_tqdm'] = True

    if shift_tolerance is None:
        shift_tolerance = 1. / upsampling
    if shift_cutoff is None:
        shift_cutoff = 5. / upsampling

    if not (align_j or align_k):
        raise ValueError('At least one of align_j and align_k must be set to True,'
                         ' but both are set to False.')

    number_of_samples = int(
        (np.ceil(len(data_container.geometry) - len(ignored_subset)) * relative_sample_size))

    j_vectors = np.einsum(
            'kij,i->kj',
            data_container.geometry.rotations_as_array,
            data_container.geometry.j_direction_0)
    k_vectors = np.einsum(
            'kij,i->kj',
            data_container.geometry.rotations_as_array,
            data_container.geometry.k_direction_0)

    for i in tqdm.tqdm(range(maxiter), file=sys.stdout):
        pipeline = reconstruction_pipeline(**reconstruction_pipeline_kwargs)
        if upsampling == 1:
            # Mask is boolean and has no "channel" index
            mask = np.all(pipeline['weights'] > 0, -1)

        # Project reconstruction into 2D
        reconstruction = pipeline['result']['x']
        com_3d = np.array(center_of_mass(reconstruction[..., 0]))
        projector = pipeline['projector']
        projections = projector.forward(reconstruction)

        # Reinitialize shifts since we apply them at the end of each iteration
        shifts = np.zeros((len(projections), 2), dtype=np.float64)

        if reconstruction_pipeline_kwargs['use_absorbances'] is True:
            reference = pipeline['absorbances']
        else:
            # If not absorbances, use mean of detector segments.
            reference = np.mean(data_container.data, -1)
            reference = reference.reshape(*reference.shape, 1)
            projections = pipeline['basis_set'].forward(projections).mean(-1)
            projections = projections.reshape(*projections.shape, 1)

        valid_indices = list(set(range(len(projections))) - ignored_subset)
        sampled_subset = rng.choice(valid_indices, number_of_samples, replace=False)
        for i in sampled_subset:
            p = projections[i, ..., 0][projection_cropping]
            r = reference[i, ..., 0][projection_cropping]
            if upsampling == 1:
                m = mask[i][projection_cropping]
            else:
                m = None

            shifts[i, :] = phase_xcorr(
                           p, r,
                           upsample_factor=upsampling,
                           reference_mask=m,
                           moving_mask=m)[0]

        # The cross-correlation function is not always totally stable.
        shifts = np.nan_to_num(shifts, posinf=0, neginf=0, nan=0)

        # Rescale shifts that are too large.
        shift_size = np.sqrt(shifts[:, 0] ** 2 + shifts[:, 1] ** 2)
        shifts[shift_size > 0, :] *= (shift_size[shift_size > 0].clip(None, shift_cutoff) /
                                      shift_size[shift_size > 0]).reshape(-1, 1)

        # Add stochastic relaxation factor, tending to move shifts toward the mean.
        shifts[sampled_subset, 0] -= _relax_offsets(
            data_container.geometry.j_offsets_as_array)[sampled_subset].clip(-1, 1) * relaxation_weight
        shifts[sampled_subset, 1] -= _relax_offsets(
            data_container.geometry.k_offsets_as_array)[sampled_subset].clip(-1, 1) * relaxation_weight

        # Add movement of projection center of mass toward reconstruction center of mass.
        for i in sampled_subset:
            com_2d = np.array(center_of_mass(projections[i, ..., 0]))
            com_shifts = _shift_toward_center(com_2d,
                                              com_3d,
                                              j_vectors[i],
                                              k_vectors[i],
                                              data_container.geometry.j_offsets[i],
                                              data_container.geometry.k_offsets[i])
            shifts[i, 0] += com_shifts[0].clip(-1, 1) * center_of_mass_shift_weight
            shifts[i, 1] += com_shifts[1].clip(-1, 1) * center_of_mass_shift_weight

        if not align_j:
            shifts[:, 0] = 0
        if not align_k:
            shifts[:, 1] = 0.

        data_container.geometry.j_offsets = data_container.geometry.j_offsets_as_array + shifts[:, 0]
        data_container.geometry.k_offsets = data_container.geometry.k_offsets_as_array + shifts[:, 1]

        if np.max(shift_size) < shift_tolerance:
            logger.info(f'Maximal shift is {np.max(shift_size):.2f}, which is less than'
                        f' the specified tolerance {shift_tolerance:.2f}. Alignment completed.')
            break
    else:
        logger.info('Maximal number of iterations reached. Alignment completed.')
    return dict(reconstruction=reconstruction, projections=projections, reference=reference)
