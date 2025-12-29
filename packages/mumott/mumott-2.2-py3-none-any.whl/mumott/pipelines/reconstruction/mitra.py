import logging

import numpy as np

from mumott.data_handling import DataContainer
from mumott.data_handling.utilities import get_absorbances
from mumott.methods.basis_sets import TrivialBasis, GaussianKernels
from mumott.methods.residual_calculators import GradientResidualCalculator
from mumott.methods.projectors import SAXSProjectorCUDA, SAXSProjector
from mumott.methods.utilities import (get_sirt_weights, get_sirt_preconditioner,
                                      get_tensor_sirt_weights, get_tensor_sirt_preconditioner)
from mumott.optimization.loss_functions import SquaredLoss
from mumott.optimization.optimizers import GradientDescent

logger = logging.getLogger(__name__)


def run_mitra(data_container: DataContainer,
              use_absorbances: bool = True,
              use_sirt_weights: bool = True,
              use_gpu: bool = False,
              maxiter: int = 20,
              ftol: float = None,
              **kwargs):
    """Reconstruction pipeline for the Modular Iterative Tomographic Reconstruction Algorithm (MITRA).
    This is a versatile, configureable interface for tomographic reconstruction that allows for
    various optimizers, projectors, loss functions and regularizers to be supplied.

    This is meant as a convenience interface for intermediate or advanced users to create
    customized reconstruction pipelines.

    Parameters
    ----------
    data_container
        The :class:`DataContainer <mumott.data_handling.DataContainer>`
        from loading the data set of interest.
    use_absorbances
        If ``True``, the reconstruction will use the absorbances
        calculated from the diode, or absorbances provided via a keyword argument.
        If ``False``, the data in :attr:`data_container.data` will be used.
    use_sirt_weights
        If ``True`` (default), SIRT or tensor SIRT weights will be computed
        for use in the reconstruction.
    use_gpu
        Whether to use GPU resources in computing the projections.
        Default is ``False``, which means
        :class:`SAXSProjector <mumott.methods.projectors.SAXSProjector>`.
        If set to ``True``, the method will use
        :class:`SAXSProjectorCUDA <mumott.methods.projectors.SAXSProjectorCUDA>`.
    maxiter
        Maximum number of iterations for the gradient descent solution.
    ftol
        Tolerance for the change in the loss function. Default is ``None``,
        in which case the reconstruction will terminate once the maximum
        number of iterations have been performed.
    kwargs
        Miscellaneous keyword arguments. See notes for details.

    Notes
    -----
    Many options can be specified through ``kwargs``. These include:

        Projector
            The :ref:`projector class <projectors>` to use.
        absorbances
            If :attr:`use_absorbances` is set to ``True``, these absorbances
            will be used instead of ones calculated from the diode.
        preconditioner_cutoff
            The cutoff to use when computing the :term:`SIRT` preconditioner.
            Default value is ``0.1``,
            which will lead to a roughly ellipsoidal mask.
        weights_cutoff
            The cutoff to use when computing the :term:`SIRT` weights.
            Default value is ``0.1``,
            which will clip some projection edges.
        BasisSet
            The :ref:`basis set class <basis_sets>` to use. If not provided
            :class:`TrivialBasis <mumott.methods.basis_sets.TrivialBasis>`
            will be used for absorbances and
            :class:`GaussianKernels <mumott.methods.basis_sets.GaussianKernels>`
            for other data.
        basis_set_kwargs
            Keyword arguments for :attr:`BasisSet`.
        ResidualCalculator
            The :ref:`residual calculator class <residual_calculators>` to use.
            If not provided, then
            :class:`GradientResidualCalculator
            <mumott.methods.residual_calculators.GradientResidualCalculator>`
            will be used.
        residual_calculator_kwargs
            Keyword arguments for :attr:`ResidualCalculator`.
        LossFunction
            The :ref:`loss function class <loss_functions>` to use. If not provided
            :class:`SquaredLoss <mumott.optimization.loss_functions.SquaredLoss>`
            will be used.
        loss_function_kwargs
            Keyword arguments for :attr:`LossFunction`.
        Regularizers
            A list of dictionaries with three entries, a name
            (``str``), a :ref:`regularizer object <regularizers>`, and
            a regularization weight (``float``); used by
            :func:`loss_function.add_regularizer()
            <mumott.optimization.loss_functions.SquaredLoss.add_regularizer>`.
        Optimizer
            The optimizer class to use. If not provided
            :class:`GradientDescent <mumott.optimization.optimizers.GradientDescent>`
            will be used. By default, the keyword argument ``nestorov_weight`` is set to
            ``0.95``, and ``enforce_non_negativity`` is ``True``
        optimizer_kwargs
            Keyword arguments for :attr:`Optimizer`.
    """
    if 'Projector' in kwargs:
        Projector = kwargs.pop('Projector')
    else:
        if use_gpu:
            Projector = SAXSProjectorCUDA
        else:
            Projector = SAXSProjector
    projector = Projector(data_container.geometry)
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
            basis_set_kwargs['grid_scale'] = \
                basis_set_kwargs.get('grid_scale', (data_container.projections.data.shape[-1]) // 2 + 1)

    basis_set = BasisSet(**basis_set_kwargs)

    ResidualCalculator = kwargs.get('ResidualCalculator', GradientResidualCalculator)
    residual_calculator_kwargs = kwargs.get('residual_calculator_kwargs', dict())
    residual_calculator_kwargs['use_scalar_projections'] = residual_calculator_kwargs.get(
        'use_scalar_projections', use_absorbances)
    residual_calculator_kwargs['scalar_projections'] = residual_calculator_kwargs.get(
        'scalar_projections', absorbances)
    residual_calculator = ResidualCalculator(data_container,
                                             basis_set,
                                             projector,
                                             **residual_calculator_kwargs)
    Regularizers = kwargs.get('Regularizers', [])
    LossFunction = kwargs.get('LossFunction', SquaredLoss)
    loss_function_kwargs = kwargs.get('loss_function_kwargs', dict())
    preconditioner_cutoff = kwargs.get('preconditioner_cutoff', 0.1)
    weights_cutoff = kwargs.get('weights_cutoff', 0.1)

    if use_sirt_weights:
        if use_absorbances:
            preconditioner = get_sirt_preconditioner(
                projector, cutoff=preconditioner_cutoff)
            sirt_weights = get_sirt_weights(
                projector, cutoff=weights_cutoff)
        else:
            preconditioner = get_tensor_sirt_preconditioner(
                projector, basis_set, cutoff=preconditioner_cutoff)
            sirt_weights = get_tensor_sirt_weights(
                projector, basis_set, cutoff=weights_cutoff)
        old_weights = data_container.projections.weights.copy()
        weights = sirt_weights * np.round(data_container.projections.weights > 0).astype(float)
        data_container.projections.weights = weights
        loss_function_kwargs['use_weights'] = True
    else:
        # If not using SIRT weights, just fetch identically named arguments as normal from kwargs
        weights = kwargs.get('weights', data_container.projections.weights)
        preconditioner = loss_function_kwargs.get('preconditioner', None)
        loss_function_kwargs['use_weights'] = loss_function_kwargs.get('use_weights', True)

    loss_function_kwargs['preconditioner'] = preconditioner
    loss_function = LossFunction(residual_calculator,
                                 **loss_function_kwargs)

    for reg in Regularizers:
        loss_function.add_regularizer(**reg)
    optimizer_kwargs = kwargs.get('optimizer_kwargs', dict())
    if 'Optimizer' in kwargs:
        Optimizer = kwargs.pop('Optimizer')
    else:
        Optimizer = GradientDescent
        if 'nestorov_weight' not in optimizer_kwargs:
            optimizer_kwargs['nestorov_weight'] = 0.95
    optimizer_kwargs['maxiter'] = optimizer_kwargs.get('maxiter', maxiter)
    optimizer_kwargs['ftol'] = optimizer_kwargs.get('ftol', ftol)
    optimizer_kwargs['enforce_non_negativity'] = optimizer_kwargs.get('enforce_non_negativity', True)
    optimizer_kwargs['no_tqdm'] = kwargs.get('no_tqdm', optimizer_kwargs.get('no_tqdm', False))
    optimizer = Optimizer(loss_function,
                          **optimizer_kwargs)

    result = optimizer.optimize()

    if use_sirt_weights:
        data_container.projections.weights = old_weights

    return dict(result=result, optimizer=optimizer, loss_function=loss_function,
                residual_calculator=residual_calculator, basis_set=basis_set, projector=projector,
                absorbances=absorbances, weights=weights, preconditioner=preconditioner)
