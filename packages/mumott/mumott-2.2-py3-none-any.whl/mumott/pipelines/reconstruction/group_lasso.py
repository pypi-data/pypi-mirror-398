import numpy as np
import tqdm
import logging

from mumott import DataContainer
from mumott.optimization.optimizers.base_optimizer import Optimizer
from mumott.optimization.loss_functions.base_loss_function import LossFunction
from mumott.methods.basis_sets.base_basis_set import BasisSet
from numpy.typing import NDArray

from mumott.methods.residual_calculators import GradientResidualCalculator
from mumott.optimization.loss_functions import SquaredLoss
from mumott.optimization.regularizers.group_lasso import GroupLasso

from mumott.methods.utilities.preconditioning import get_largest_eigenvalue
from mumott.methods.projectors import SAXSProjectorCUDA, SAXSProjector
from mumott.methods.basis_sets import SphericalHarmonics

logger = logging.getLogger(__name__)


def run_group_lasso(data_container: DataContainer,
                    regularization_parameter: float,
                    step_size_parameter: float = None,
                    x0: NDArray[float] = None,
                    basis_set: BasisSet = None,
                    ell_max: int = 8,
                    use_gpu: bool = False,
                    maxiter: int = 100,
                    enforce_non_negativity: bool = False,
                    no_tqdm: bool = False,
                    ):

    """A reconstruction pipeline to do least squares reconstructions regularized with the group-lasso
    regularizer and solved with the Iterative Soft-Thresholding Algorithm (ISTA), a proximal gradient
    decent method. This reconstruction automatically masks out voxels with zero scattering but
    needs the regularization weight as input.

    Parameters
    ----------
    data_container
        The :class:`DataContainer <mumott.data_handling.DataContainer>`
        containing the data set of interest.
    regularization_parameter
        Scalar weight of the regularization term. Should be optimized by performing reconstructions
        for a range of possible values.
    step_size_parameter
        Step size parameter of the reconstruction. If no value is given, a largest-safe
        value is estimated.
    x0
        Starting guess for the solution. By default (``None``) the coefficients are initialized with
        zeros.
    basis_set
        Optionally a basis set can be specified. By default (``None``)
        :class:`SphericalHarmonics <mumott.methods.basis_sets.SphericalHarmonics>` is used.
    ell_max
        If no basis set is given, this is the maximum spherical harmonics order used in the
        generated basis set.
    use_gpu
        Whether to use GPU resources in computing the projections.
        Default is ``False``. If set to ``True``, the method will use
        :class:`SAXSProjectorCUDA <mumott.methods.projectors.SAXSProjectorCUDA>`.
    maxiter
        Number of iterations for the ISTA optimization. No stopping rules are implemented.
    enforce_non_negativity
        Whether or not to enforce non-negativitu of the solution coefficients.
    no_tqdm:
        Flag whether ot not to print a progress bar for the reconstruction.
    """

    if use_gpu:
        Projector = SAXSProjectorCUDA
    else:
        Projector = SAXSProjector
    projector = Projector(data_container.geometry)

    if basis_set is None:
        basis_set = SphericalHarmonics(ell_max=ell_max)

    if step_size_parameter is None:
        logger.info('Calculating step size parameter.')
        matrix_norm = get_largest_eigenvalue(basis_set, projector)
        step_size_parameter = 0.5 / matrix_norm

    loss_function = SquaredLoss(GradientResidualCalculator(data_container, basis_set, projector))
    reg_term = GroupLasso(regularization_parameter, step_size_parameter)
    optimizer = _ISTA(loss_function, reg_term, step_size_parameter, x0=x0, maxiter=maxiter,
                      enforce_non_negativity=enforce_non_negativity, no_tqdm=no_tqdm)

    opt_coeffs = optimizer.optimize()

    result = dict(result={'x': opt_coeffs}, optimizer=optimizer, loss_function=loss_function,
                  regularizer=reg_term, basis_set=basis_set, projector=projector)
    return result


class _ISTA(Optimizer):
    """Internal optimizer class for the group lasso pipeline. Implements
    <mumott.optimization.optimizers.base_optimizer.Optimizer>.

    Parameters
    ----------
    loss_function : LossFunction
        The differentiable part of the :ref:`loss function <loss_functions>`
        to be minimized using this algorithm.
    reg_term : GroupLasso
        Non-differentiable regularization term to be applied in every iteration.
        Must have a `proximal_operator` method.
    step_size_parameter : float
        Step size for the differentiable part of the optimization.
    maxiter : int
        Maximum number of iterations. Default value is `50`.
    enforce_non_negativity : bool
        If `True`, forces all coefficients to be greater than `0` at the end of every iteration.
        Default value is `False`.

    Notes
    -----
    Valid entries in :attr:`kwargs` are
        x0
            Initial guess for solution vector. Must be the same size as
            :attr:`residual_calculator.coefficients`. Defaults to :attr:`loss_function.initial_values`.
    """

    def __init__(self, loss_function: LossFunction, reg_term: GroupLasso, step_size_parameter: float,
                 maxiter: int = 50, enforce_non_negativity: bool = False, **kwargs):

        super().__init__(loss_function, **kwargs)
        self._maxiter = maxiter
        self._reg_term = reg_term
        self._step_size_parameter = step_size_parameter
        self.error_function_history = []
        self._enforce_non_negativity = enforce_non_negativity

    def ISTA_step(self, coefficients):

        d = self._loss_function.get_loss(coefficients, get_gradient=True)
        gradient = d['gradient']
        total_loss = d['loss'] +\
            self._reg_term.get_regularization_norm(coefficients)['regularization_norm']
        coefficients = coefficients - self._step_size_parameter * gradient
        coefficients = self._reg_term.proximal_operator(coefficients)
        if self._enforce_non_negativity:
            np.clip(coefficients, 0, None, out=coefficients)

        return coefficients, total_loss

    def optimize(self):

        coefficients = self._loss_function.initial_values
        if 'x0' in self._options.keys():
            if self['x0'] is not None:
                coefficients = self['x0']

        # Calculate total loss
        loss_function_output = self._loss_function.get_loss(coefficients)
        reg_term_output = self._reg_term.get_regularization_norm(coefficients)
        total_loss = loss_function_output['loss'] + reg_term_output['regularization_norm']

        #  Toggle between printing an error bar or not
        if not self._no_tqdm:
            iterator = tqdm.tqdm(range(self._maxiter))
            iterator.set_description(f'Loss = {total_loss:.2E}')
        elif self._no_tqdm:
            iterator = range(self._maxiter)

        for ii in iterator:
            # Do step
            coefficients, total_loss = self.ISTA_step(coefficients)
            # Update progress bar
            self.error_function_history.append(total_loss)
            if not self._no_tqdm:
                iterator.set_description(f'Loss = {total_loss:.2E}')

        return np.array(coefficients)
