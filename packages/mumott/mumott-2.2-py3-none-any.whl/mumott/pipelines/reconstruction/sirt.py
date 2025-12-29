import logging

import numpy as np

from mumott.data_handling import DataContainer
from mumott.data_handling.utilities import get_absorbances
from mumott.methods.basis_sets import TrivialBasis, GaussianKernels
from mumott.methods.residual_calculators import GradientResidualCalculator
from mumott.methods.projectors import SAXSProjectorCUDA, SAXSProjector
from mumott.methods.utilities import get_sirt_weights, get_sirt_preconditioner
from mumott.optimization.loss_functions import SquaredLoss
from mumott.optimization.optimizers import GradientDescent

logger = logging.getLogger(__name__)


def run_sirt(data_container: DataContainer,
             use_absorbances: bool = True,
             use_gpu: bool = False,
             maxiter: int = 20,
             enforce_non_negativity: bool = False,
             **kwargs):
    """A reconstruction pipeline for the :term:`SIRT` algorithm, which uses
    a gradient preconditioner and a set of weights for the projections
    to achieve fast convergence. Generally, one varies the number of iterations
    until a good reconstruction is obtained.

    Advanced users may wish to also modify the ``preconditioner_cutoff`` and
    ``weights_cutoff`` keyword arguments.

    Parameters
    ----------
    data_container
        The :class:`DataContainer <mumott.data_handling.DataContainer>`
        from loading the data set of interest.
    use_absorbances
        If ``True``, the reconstruction will use the absorbances
        calculated from the diode, or absorbances provided via a keyword argument.
        If ``False``, the data in :attr:`data_container.data` will be used.
    use_gpu
        Whether to use GPU resources in computing the projections.
        Default is ``False``. If set to ``True``, the method will use
        :class:`SAXSProjectorCUDA <mumott.methods.projectors.SAXSProjectorCUDA>`.
    maxiter
        Maximum number of iterations for the gradient descent solution.
    enforce_non_negativity
        Enforces strict positivity on all the coefficients. Should only be used
        with local or scalar representations. Default value is ``False``.
    kwargs
        Miscellaneous keyword arguments. See notes for details.

    Notes
    -----
    Many options can be specified through ``kwargs``. These include:

        Projector
            The :ref:`projector class <projectors>` to use.
        preconditioner_cutoff
            The cutoff to use when computing the :term:`SIRT` preconditioner.
            Default value is ``0.1``,
            which will lead to a roughly ellipsoidal mask.
        weights_cutoff
            The cutoff to use when computing the :term:`SIRT` weights.
            Default value is ``0.1``,
            which will clip some projection edges.
        absorbances
            If :attr:`use_absorbances` is set to ``True``, these absorbances
            will be used instead of ones calculated from the diode.
        BasisSet
            The :ref:`basis set class <basis_sets>` to use. If not provided
            :class:`TrivialBasis <mumott.methods.basis_sets.TrivialBasis>`
            will be used for absorbances and
            :class:`GaussianKernels <mumott.methods.basis_sets.GaussianKernels>`
            for other data.
        basis_set_kwargs
            Keyword arguments for :attr:`BasisSet`.
        no_tqdm
            Used to avoid a ``tqdm`` progress bar in the optimizer.
    """
    if 'Projector' in kwargs:
        Projector = kwargs.pop('Projector')
    else:
        if use_gpu:
            Projector = SAXSProjectorCUDA
        else:
            Projector = SAXSProjector
    projector = Projector(data_container.geometry)
    preconditioner_cutoff = kwargs.get('preconditioner_cutoff', 0.1)
    weights_cutoff = kwargs.get('weights_cutoff', 0.1)
    preconditioner = get_sirt_preconditioner(projector, cutoff=preconditioner_cutoff)
    sirt_weights = get_sirt_weights(projector, cutoff=weights_cutoff)
    # Save previous weights to avoid accumulation.
    old_weights = data_container.projections.weights.copy()
    # Respect previous masking in data container
    data_container.projections.weights = sirt_weights * np.ceil(data_container.projections.weights)
    if use_absorbances:
        if 'absorbances' in kwargs:
            absorbances = kwargs.pop('absorbances')
        else:
            abs_dict = get_absorbances(data_container.diode, normalize_per_projection=True)
            absorbances = abs_dict['absorbances']
            transmittivity_cutoff_mask = abs_dict['cutoff_mask']
            data_container.projections.weights *= transmittivity_cutoff_mask
    else:
        absorbances = None
    basis_set_kwargs = kwargs.get('basis_set_kwargs', dict())
    if 'BasisSet' in kwargs:
        BasisSet = kwargs.pop('BasisSet')
    else:
        if use_absorbances:
            BasisSet = TrivialBasis
            if 'channels' not in basis_set_kwargs:
                basis_set_kwargs['channels'] = 1
        else:
            BasisSet = GaussianKernels
            basis_set_kwargs['grid_scale'] = (data_container.projections.data.shape[-1]) // 2 + 1
    basis_set = BasisSet(**basis_set_kwargs)
    residual_calculator_kwargs = dict(use_scalar_projections=use_absorbances,
                                      scalar_projections=absorbances)
    residual_calculator = GradientResidualCalculator(data_container,
                                                     basis_set,
                                                     projector,
                                                     **residual_calculator_kwargs)
    loss_function_kwargs = dict(use_weights=True, preconditioner=preconditioner)
    loss_function = SquaredLoss(residual_calculator,
                                **loss_function_kwargs)

    optimizer_kwargs = dict(maxiter=maxiter)
    optimizer_kwargs['no_tqdm'] = kwargs.get('no_tqdm', False)
    optimizer_kwargs['enforce_non_negativity'] = enforce_non_negativity
    optimizer = GradientDescent(loss_function,
                                **optimizer_kwargs)

    result = optimizer.optimize()
    weights = data_container.projections.weights.copy()
    data_container.projections.weights = old_weights
    return dict(result=result, optimizer=optimizer, loss_function=loss_function,
                residual_calculator=residual_calculator, basis_set=basis_set, projector=projector,
                absorbances=absorbances, weights=weights)
