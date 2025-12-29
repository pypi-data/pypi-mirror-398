import logging

from typing import Dict, Any

import numpy as np

from mumott.core.hashing import list_to_hash
from mumott.optimization.loss_functions.base_loss_function import LossFunction
from .base_optimizer import Optimizer


logger = logging.getLogger(__name__)


class GradientDescent(Optimizer):
    r"""This Optimizer is a gradient descent (sometimes called steepest descent)
    solver, which can be set to terminate based on the loss function and/or the maximum
    number of iterations.

    It also supports the use of Nestorov accelerated momentum, which features a look-ahead
    momentum term based on the gradient of the previous iterations.

    The update sequence may be written

    .. math::
        x &\leftarrow x - (p + \alpha(\nabla(x - p) + \Lambda)) \\
        p &\leftarrow \beta(p + \alpha(\nabla(x - p) + \Lambda))

    where :math:`x` are the optimization coefficients, :math:`p` is the momentum,
    and :math:`\Lambda` is the regularization term. :math:`\alpha` is the step size
    and :math:`\beta` is the Nestorov momentum weight.

    Parameters
    ----------
    loss_function : LossFunction
        The :ref:`loss function <loss_functions>` to be minimized using this algorithm.
    kwargs : Dict[str, Any]
        Miscellaneous options. See notes for valid entries.

    Notes
    -----
    Valid entries in :attr:`kwargs` are
        x0
            Initial guess for solution vector. Must be the same size as
            :attr:`residual_calculator.coefficients`. Defaults to :attr:`loss_function.initial_values`.
        step_size : float
            Step size for the gradient, labelled :math:`\alpha` above. Default value is 1.
            Must be strictly positive.
        nestorov_weight : float
            The size of the look-ahead term in each iteration, labelled :math:`\beta` above.
            Must be in the range ``[0, 1]``, including the endpoints.
            The default value is ``0``, which implies that the momentum term is not active.
        maxiter : int
            Maximum number of iterations. Default value is ``5``.
        ftol : float
            The tolerance for relative change in the loss function before
            termination. A termination can only be induced after at least 5 iterations.
            If ``None``, termination only occurs once :attr:`maxiter` iterations
            have been performed. Default value is ``None``.
        display_loss : bool
            If `True`, displays the change in loss at every iteration. Default is `False`.
        enforce_non_negativity : bool
            Enforces strict positivity on all the coefficients. Should only be used
            with local or scalar representations. Default value is ``False``.
    """

    def __init__(self,
                 loss_function: LossFunction,
                 **kwargs: Dict[str, Any]):
        super().__init__(loss_function, **kwargs)

    def optimize(self) -> Dict:
        """ Executes the optimization using the options stored in this class
        instance. The optimization will continue until convergence,
        or until the maximum number of iterations (:attr:`maxiter`) is exceeded.

        Returns
        -------
            A ``dict`` of optimization results. See `scipy.optimize.OptimizeResult
            <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.OptimizeResult.html>`_
            for details. The entry ``'x'``, which contains the result, will be reshaped using
            the shape of the gradient from :attr:`loss_function`.
        """
        opt_kwargs = dict(x0=self._loss_function.initial_values,
                          ftol=None,
                          maxiter=5,
                          enforce_non_negativity=False,
                          display_loss=False,
                          step_size=1.,
                          nestorov_weight=0.)

        for k in opt_kwargs:
            if k in dict(self):
                opt_kwargs[k] = self[k]

        for k in dict(self):
            if k not in opt_kwargs:
                logger.warning(f'Unknown option {k}, with value {self[k]}, has been ignored.')

        if opt_kwargs['x0'] is None:
            coefficients = self._loss_function.initial_values
        else:
            coefficients = opt_kwargs['x0']

        if opt_kwargs['ftol'] is None:
            ftol = -np.inf
        else:
            ftol = opt_kwargs['ftol']

        if opt_kwargs['step_size'] < 0:
            raise ValueError(f'step_size must be greater than 0, but its value is {opt_kwargs["step_size"]}!')

        if not 0 <= opt_kwargs['nestorov_weight'] <= 1:
            raise ValueError('nestorov_weight must be in the range [0, 1] inclusive,'
                             f' but its value is {opt_kwargs["nestorov_weight"]}!')

        previous_loss = -1
        previous_gradient = np.zeros_like(coefficients)
        for i in self._tqdm(opt_kwargs['maxiter']):
            d = self._loss_function.get_loss(coefficients - previous_gradient, get_gradient=True)
            relative_change = (previous_loss - d['loss']) / d['loss']
            if opt_kwargs['display_loss']:
                logger.info(f'Iteration: {i} Loss function: {d["loss"]:.2e}'
                            f' Relative change: {relative_change:.2e}')
            d['gradient'] *= opt_kwargs['step_size']
            previous_gradient += d['gradient']
            coefficients -= previous_gradient
            previous_loss = d['loss']
            previous_gradient *= opt_kwargs['nestorov_weight']
            if opt_kwargs['enforce_non_negativity']:
                np.clip(coefficients, 0, None, out=coefficients)
            if i > 5 and relative_change < ftol:
                logger.info(f'Relative change ({relative_change}) is less than ftol ({ftol})!'
                            ' Optimization finished.')
                break

        result = dict(x=coefficients, loss=d['loss'], nit=i+1)
        return dict(result)

    def __hash__(self) -> int:
        to_hash = [self._options, hash(self._loss_function)]
        return int(list_to_hash(to_hash), 16)
