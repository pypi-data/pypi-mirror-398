import logging

from typing import Dict, Any

from numpy import float64

from scipy.optimize import minimize

from mumott.core.hashing import list_to_hash
from mumott.optimization.loss_functions.base_loss_function import LossFunction
from .base_optimizer import Optimizer


logger = logging.getLogger(__name__)


class LBFGS(Optimizer):
    """This Optimizer makes the :term:`LBFGS` algorithm from `scipy.optimize
    <https://docs.scipy.org/doc/scipy/reference/optimize.html>`_
    available for usage with a :class:`LossFunction <module-mumott.optimization.loss_functions>`.

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
        bounds
            Used to set the ``bounds`` of the optimization method, see `scipy.optimize.minimize
            <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html>`_
            documentation for details. Defaults to ``None``.
        maxiter
            Maximum number of iterations. Defaults to ``10``.
        disp
            Whether to display output from the optimizer. Defaults to ``False``
        maxcor
            Maximum number of Hessian corrections to the Jacobian. Defaults to ``10``.
        iprint
            If ``disp`` is true, controls output with no output if ``iprint < 0``,
            convergence output only if ``iprint == 0``, iteration-wise output if
            ``0 < iprint <= 99``, and sub-iteration output if ``iprint > 99``.
        maxfun
            Maximum number of function evaluations, including line search evaluations.
            Defaults to ``20``.
        ftol
            Relative change tolerance for objective function. Changes to absolute change tolerance
            if objective function is ``< 1``, see `scipy.optimize.minimize
            <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html>`_
            documentation, which may lead to excessively fast convergence.
            Defaults to ``1e-3``.
        gtol
            Convergence tolerance for gradient. Defaults to ``1e-5``.
    """

    def __init__(self,
                 loss_function: LossFunction,
                 **kwargs: Dict[str, Any]):
        super().__init__(loss_function, **kwargs)
        # This will later be used to reshape the flattened output.
        self._output_shape = None

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
        lbfgs_kwargs = dict(x0=self._loss_function.initial_values,
                            bounds=None)
        misc_options = dict(maxiter=10,
                            disp=False,
                            maxcor=10,
                            iprint=1,
                            maxfun=20,
                            ftol=1e-3,
                            gtol=1e-5)

        for k in lbfgs_kwargs:
            if k in dict(self):
                lbfgs_kwargs[k] = self[k]

        for k in misc_options:
            if k in dict(self):
                misc_options[k] = self[k]

        for k in dict(self):
            if k not in lbfgs_kwargs and k not in misc_options:
                logger.warning(f'Unknown option {k}, with value {self[k]}, has been ignored.')

        if lbfgs_kwargs['x0'] is None:
            lbfgs_kwargs['x0'] = self._loss_function.initial_values
        lbfgs_kwargs['x0'] = lbfgs_kwargs['x0'].ravel()

        with self._tqdm(misc_options['maxiter']) as progress:

            def progress_callback(*args, **kwargs):
                progress.update(1)

            def loss_function_wrapper(coefficients):
                d = self._loss_function.get_loss(coefficients, get_gradient=True)
                # Store gradient shape to reshape flattened output.
                if self._output_shape is None:
                    self._output_shape = d['gradient'].shape
                # LBFGS needs float64
                return d['loss'], d['gradient'].ravel().astype(float64)

            result = minimize(fun=loss_function_wrapper, callback=progress_callback,
                              **lbfgs_kwargs, jac=True, method='L-BFGS-B', options=misc_options)
        result = dict(result)
        result['x'] = result['x'].reshape(self._output_shape)
        return dict(result)

    def __hash__(self) -> int:
        to_hash = [self._options, hash(self._loss_function)]
        return int(list_to_hash(to_hash), 16)
