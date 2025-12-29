import logging

import numpy as np
from numpy.typing import NDArray
from typing import Any, Dict, Tuple


logger = logging.getLogger(__name__)


def get_transmittivities(diode: NDArray,
                         normalize_per_projection: bool = False,
                         normalization_percentile: float = 99.9,
                         cutoff_values: Tuple[float, float] = (1e-4, 1.0)) -> Dict[str, Any]:
    r""" Calculates the transmittivity from the diode, i.e., the fraction of transmitted
    intensity relative to a high percentile.

    Notes
    -----

    Diode readouts may be given in various formats such as a count or a current.
    When doing absorption tomography, one is generally interested in the fraction of
    transmitted intensity. Since we do not generally have access to the incoming flux,
    or its theoretical readout at complete transmission, we can instead normalize
    the diode readout based on the largest values, where the beam has only passed through
    some air. We thus want to compute

    .. math::
        T(i, j, k) = \frac{I_T(i, j, k)}{I_0}

    where :math:`I_T(i, j, k)` is the diode readout value at projection :math:`i`, and pixel :math:`(j, k)`
    with the approximation :math:`I_0 \approx \text{max}(I_T(i, j, k))`.

    To avoid routine normalization based on individual spurious readouts
    (from, e.g., hot pixels), by default the normalization is done based on the
    99.9th percentile rather than the strict maximum.
    The normalized values are then clipped to the interval specified
    by :attr:`cutoff_values`, by default ``(1e-4, 1.0)``. A mask is returned which masks out
    any values outside this range, which can be useful to mask out spurious readouts.

    If the transmittivities are to be used to normalize :term:`SAXS` data, one should
    leave the :attr:`normalize_per_projection` option at ``False``, because the :term:`SAXS` data
    also scales with the incoming flux, and thus we want any variations in flux between
    projections to be preserved in the transmittivities.

    However, if the transmittivities are to be used for transmission (or absorption) tomography,
    then the :attr:`normalize_per_projection`
    option should be set to ``True``. Since we are interested in the transmittivity
    of the sample irrespective of the incoming flux, we are therefore better off assuming
    the flux is constant over each projection. This corresponds to the slightly modified computation

    .. math::
        T(i, j, k) = \frac{I_T(i, j, k)}{I_0(i)}

    with the approximation :math:`I_0(i) \approx \text{max}_{j, k}(I_T(i, j, k))`,
    with the understanding that we take the maximum value for each projection :math:`i`.

    Parameters
    ----------
    diode
        An array of diode readouts.
    normalize_per_projection
        If ``True``, the diode will be normalized projection-wise.
        This is the appropriate choice for absorption tomography.
        For :term:`SAXS`, it is preferable to normalize the diode across the entire set
        of diode measurements in order to account for possible variations in flux.
        Default value is ``False``.
    normalization_percentile
        The percentile of values in either the entire set of diode measurements or each projection
        (depending on :attr:`normalize_per_projection`) to use for normalization.
        The default value is ``99.9``. Values above this range will be clipped. If you are
        certain that you do not have spuriously large diode readout values, you can specify
        ``100.`` as the percentile instead.
    cutoff_values
        The cutoffs to use for the transmittivity calculation. Default value is
        ``(1e-4, 1.0)``, i.e., one part in ten thousand for the lower bound, and
        a hundred percent for the upper bound. For values outside of this range, it may
        be desirable to mask them out during *any* calculation. For this purpose,
        a ``cutoff_mask`` is included in the return dictionary with the same shape as
        the weights in :attr:`projections`.
        In some cases, you may wish to specify other bounds. For example, if you know that
        your sample is embedded in a substrate which reduces the maximum possible transmittivity,
        you may wish to lower the upper bound. If you know that your sample has extremely low
        transmittivity (perhaps compensated with a very long exposure time), then you can set
        the lower cutoff even lower.
        The cutoffs must lie within the open interval ``(0, 1]``. A lower bound of ``0``
        is not permitted since this would lead to an invalid absorbance.

    Returns
    -------
        A dictionary with three entries, ``transmittivity``, ``cutoff_mask_lower``,
        and ``cutoff_mask_upper``.
    """
    if cutoff_values[0] <= 0 or cutoff_values[1] > 1:
        raise ValueError('cutoff_values must lie in the open interval (0, 1], but'
                         f' cutoff values of {cutoff_values} were specified!')
    # These should already be copies, but for future-proofing.
    transmittivity = diode.copy()
    cutoff_mask_lower = np.ones_like(diode)[..., None]
    cutoff_mask_upper = np.ones_like(diode)[..., None]
    if normalize_per_projection:
        for i, t in enumerate(transmittivity):
            # Normalize each projection's maximum value to 1, cutting off values outside the range.
            normalization_value = np.percentile(t, normalization_percentile)
            transmittivity[i] = t * np.reciprocal(normalization_value)
            cutoff_mask_lower[i] = (transmittivity[i, ..., None] >= cutoff_values[0])
            cutoff_mask_upper[i] = (transmittivity[i, ..., None] <= cutoff_values[1])
            np.clip(transmittivity[i], *cutoff_values, out=transmittivity[i])
    else:
        # Normalize the maximum value of all projections to 1, cutting off values outside the range.
        normalization_value = np.percentile(transmittivity, normalization_percentile)
        transmittivity *= np.reciprocal(normalization_value)
        cutoff_mask_lower = (transmittivity[..., None] >= cutoff_values[0])
        cutoff_mask_upper = (transmittivity[..., None] <= cutoff_values[1])
        np.clip(transmittivity, *cutoff_values, out=transmittivity)

    return dict(transmittivity=transmittivity, cutoff_mask_lower=cutoff_mask_lower,
                cutoff_mask_upper=cutoff_mask_upper)


def get_absorbances(diode: NDArray, **kwargs) -> Dict[str, Any]:
    r""" Calculates the absorbance based on the transmittivity of the diode data.

    Notes
    -----
    The absorbance is defined as the negative base-10 logarithm of the transmittivity.
    Specifically,

    .. math::
        A(i, j, k) = -\log_{10}(T(i, j, k))

    where :math:`T` is the transmittivity, normalized to the open interval :math:`(0, 1]`.
    It can be inferred from this formula why :math:`T(i, j, k)` must not have values which
    are equal to or smaller than :math:`0`, as that would give a non-finite absorbance.
    Similarly, values greater than :math:`1` would result in physically impossible negative
    absorbances.

    The transmittivity is calculated directly from diode readouts, which may or may not already
    be normalized and clipped. When using already normalized diode values, it is best
    to set the keyword argument :attr:`normalization_percentile` to ``100``, and the
    argument :attr:`cutoff_values` to whatever cutoff your normalization used.

    See :func:`get_transmittivities` for more details on the transmittivity calculation.

    Parameters
    ----------
    diode
        An array of diode readouts.
    kwargs
        Keyword arguments which are passed on to :func:`get_transmittivities`.

    Returns
    -------
        A dictionary with the absorbance, and the union of the cutoff masks from
        :func:`get_transmittivities`.
    """

    transmittivity_dictionary = get_transmittivities(diode, **kwargs)
    transmittivity = transmittivity_dictionary['transmittivity']
    absorbances = -np.log10(transmittivity)
    assert np.all(np.isfinite(absorbances))
    return dict(absorbances=absorbances[..., None],
                cutoff_mask=(transmittivity_dictionary['cutoff_mask_lower'] *
                             transmittivity_dictionary['cutoff_mask_upper']))
