import logging

from mumott import DataContainer
from mumott.methods.projectors import SAXSProjector, SAXSProjectorCUDA
from .fbp_utilities import get_filtered_projections

logger = logging.getLogger(__name__)


def run_fbp(data_container: DataContainer,
            use_gpu: bool = False,
            fbp_axis: str = 'inner',
            filter_type: str = 'Ram-Lak',
            **kwargs) -> dict:
    """
    This pipeline is used to compute the filtered back projection of the
    absorbances calculated from the diode. This allows for a quick, one-step
    solution to the problem of scalar tomography.

    Parameters
    ----------
    data_container
        The :class:`DataContainer <mumott.data_handling.DataContainer>`
        holding the data set of interest.
    use_gpu
        Whether to use GPU resources in computing the projections.
        Default is ``False``. If set to ``True``, the method will use
        :class:`SAXSProjectorCUDA <mumott.methods.projectors.SAXSProjectorCUDA>`.
    fbp_axis
        Default is ``'inner'``, the value depends on how the sample is mounted to the holder. Typically,
        the inner axis is the rotation axis while the ``'outer'`` axis refers to the tilt axis.
    filter_type
        Default is ``'Ram-Lak'``, a high-pass filter. Other options are ``'Hamming'``, ``'Hann'``,
        ``'Shepp-Logan'`` and ``'cosine'``.
    kwargs
        Miscellaneous keyword arguments. See notes for details.

    Notes
    -----
    Three possible :attr:`kwargs` can be provided:

        Projector
            The :ref:`projector class <projectors>` to use.
        normalization_percentile
            The normalization percentile to use for the transmittivity calculation. See
            :func:`get_transmittivities <mumott.data_handling.utilities.get_transmittivities>` for details.
        transmittivity_cutoff
            The cutoffs to use for the transmittivity calculation. See
            :func:`get_transmittivities <mumott.data_handling.utilities.get_transmittivities>` for details.


    Returns
    -------
        A dictionary with the entry ``'result'``, with an entry ``'x'``, containing
        a filtered back projection reconstruction of the absorptivity calculated
        from the ``diode``.
    """
    if 'Projector' in kwargs:
        Projector = kwargs.pop('Projector')
    else:
        if use_gpu:
            Projector = SAXSProjectorCUDA
        else:
            Projector = SAXSProjector
    projector = Projector(data_container.geometry)
    filtered_projections, indices = get_filtered_projections(data_container.projections,
                                                             axis_string=fbp_axis,
                                                             filter_type=filter_type,
                                                             **kwargs)
    filtered_projections = filtered_projections.astype(projector.dtype)
    fbp_reconstruction = projector.adjoint(filtered_projections, indices)
    return dict(result=dict(x=fbp_reconstruction), projector=projector, fbp_indices=indices)
