import logging

from mumott.data_handling import DataContainer
from mumott.methods.basis_sets import SphericalHarmonics
from mumott.methods.residual_calculators import GradientResidualCalculator
from mumott.methods.projectors import SAXSProjectorCUDA, SAXSProjector
from mumott.optimization.loss_functions import SquaredLoss
from mumott.optimization.optimizers import LBFGS
from mumott.optimization.regularizers import Laplacian

logger = logging.getLogger(__name__)


def run_sigtt(data_container: DataContainer,
              use_gpu: bool = False,
              maxiter: int = 20,
              ftol: float = 1e-2,
              regularization_weight: float = 1e-4,
              **kwargs):
    """A reconstruction pipeline for the :term:`SIGTT` algorithm, which uses
    a gradient and a regularizer to accomplish reconstruction.

    Parameters
    ----------
    data_container
        The :class:`DataContainer <mumott.data_handling.DataContainer>`
        from loading the data set of interest.
    use_gpu
        Whether to use GPU resources in computing the projections.
        Default is ``False``. If set to ``True``, the method will use
        :class:`SAXSProjectorCUDA <mumott.methods.projectors.SAXSProjectorCUDA>`.
    maxiter
        Maximum number of iterations for the gradient descent solution.
    ftol
        Tolerance for the change in the loss function. Default is ``None``,
        in which case the reconstruction will terminate once the maximum
        number of iterations have been performed.
    regularization_weight
        Regularization weight for the default
        :class:`Laplacian <mumott.optimization.regularizers.Laplacian>` regularizer.
        Ignored if a loss function is provided.
    kwargs
        Miscellaneous keyword arguments. See notes for details.

    Notes
    -----
    Many options can be specified through :attr:`kwargs`. Miscellaneous ones are passed to the optimizer.
    Specific keywords include:

        Projector
            The :ref:`projector class <projectors>` to use.
        BasisSet
            The :ref:`basis set class <basis_sets>` to use. If not provided
            :class:`SphericalHarmonics <mumott.methods.basis_sets.SphericalHarmonics>`
            will be used.
        basis_set_kwargs
            Keyword arguments for :attr:`BasisSet`.
        ResidualCalculator
            The :ref:`residual_calculator class <residual_calculators>` to use. If not provided
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
            By default, a :class:`Laplacian
            <mumott.optimization.regularizers.Laplacian>` with the
            weight :attr:`regularization_weight` will be used. If
            other regularizers are specified, this will be overridden.
        Optimizer
            The :ref:`optimizer class <optimizers>` to use. If not provided
            :class:`LBFGS <mumott.optimization.optimizers.LBFGS>` will be used.
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
    basis_set_kwargs = kwargs.get('basis_set_kwargs', dict())
    if 'BasisSet' in kwargs:
        BasisSet = kwargs.pop('BasisSet')
    else:
        if 'ell_max' not in basis_set_kwargs:
            basis_set_kwargs['ell_max'] = 2 * ((data_container.data.shape[-1] - 1) // 2)
        BasisSet = SphericalHarmonics
    basis_set = BasisSet(**basis_set_kwargs)
    ResidualCalculator = kwargs.get('ResidualCalculator', GradientResidualCalculator)
    residual_calculator_kwargs = kwargs.get('residual_calculator_kwargs', dict())
    residual_calculator = ResidualCalculator(data_container,
                                             basis_set,
                                             projector,
                                             **residual_calculator_kwargs)

    Regularizers = kwargs.get('Regularizers',
                              [dict(name='laplacian',
                               regularizer=Laplacian(),
                               regularization_weight=regularization_weight)])
    LossFunction = kwargs.get('LossFunction', SquaredLoss)
    loss_function_kwargs = kwargs.get('loss_function_kwargs', dict())
    loss_function = LossFunction(residual_calculator,
                                 **loss_function_kwargs)
    for reg in Regularizers:
        loss_function.add_regularizer(**reg)
    Optimizer = kwargs.get('Optimizer', LBFGS)
    optimizer_kwargs = kwargs.get('optimizer_kwargs', dict())
    optimizer_kwargs['maxiter'] = optimizer_kwargs.get('maxiter', maxiter)
    optimizer_kwargs['ftol'] = optimizer_kwargs.get('ftol', ftol)
    optimizer = Optimizer(loss_function,
                          **optimizer_kwargs)
    result = optimizer.optimize()
    return dict(result=result, optimizer=optimizer, loss_function=loss_function,
                residual_calculator=residual_calculator, basis_set=basis_set, projector=projector)
