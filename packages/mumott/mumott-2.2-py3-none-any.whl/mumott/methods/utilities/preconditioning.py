import logging

import numpy as np
from numpy.typing import NDArray

from mumott.methods.projectors.base_projector import Projector
from mumott.methods.basis_sets.base_basis_set import BasisSet

logger = logging.getLogger(__name__)


def get_largest_eigenvalue(basis_set: BasisSet,
                           projector: Projector,
                           weights: NDArray[float] = None,
                           preconditioner: NDArray[float] = None,
                           niter: int = 5,
                           seed: int = None) -> float:
    r"""
    Calculate the largest eigenvalue of the matrix :math:`A^{T}*A` using the power method.
    Here, :math:`A` is the linear forward model defined be the input
    :class:`Projector <mumott.method.projectors.base_projector.Projector>` and
    :class:`BasisSet <mumott.method.bais_sets.base_basis_set.BasisSet>`.
    The largest eigenvalue can be used to set a safe step size for various optimizers.

    Parameters
    ----------
    basis_set
       basis set object
    projector
       projector object
    weights
        Weights which will be applied to the residual.
        Default is ``None``.
    preconditioner
        A preconditioner which will be applied to the gradient.
        Default is ``None``.
    niter
        number of iterations. Default is 5
    seed
        Seed for random generation as starting state. Used for testing.

    Returns.
    -------
        An estimate of the matrix norm (largest singular value)
    """
    shape = (*projector.volume_shape, len(basis_set))

    if seed is not None:
        np.random.seed(seed)
    if weights is None:
        weights = 1
    if preconditioner is None:
        preconditioner = 1

    x = np.random.normal(loc=0.0, scale=1.0, size=shape).astype(projector.dtype)

    for _ in range(niter):
        x = x / np.sqrt(np.sum(x**2))
        y = basis_set.forward(projector.forward(x)) * weights
        x = projector.adjoint(basis_set.gradient(y).astype(projector.dtype)) * \
            preconditioner

    return np.sqrt(np.sum(x**2))


def get_tensor_sirt_preconditioner(projector: Projector,
                                   basis_set: BasisSet,
                                   cutoff: float = 0.1) -> NDArray[float]:
    r""" Retrieves the :term:`SIRT` `preconditioner <https://en.wikipedia.org/wiki/Preconditioner>`_
    for tensor representations, which can be used together
    with the tensor :term:`SIRT` weights to condition the
    gradient of tensor tomographic calculations for faster convergence and scaling of the
    step size for gradient descent.

    Notes
    -----
    The preconditioner is computed similarly as in the scalar case, except the underlying
    system of equations is

    .. math::
        P_{ij} X_{jk} U_{kl} = Y_{il}

    where :math:`X_{jk}` is a vector of tensor-valued voxels, and :math:`Y_{il}`
    is the projection into measurement space. The preconditioner then corresponds to

    .. math::
        C_{jjkk} = \frac{I(n_j) \otimes I(n_k)}{\sum_{i,l} P_{ij} U_{kl}},

    where :math:`I(n_j)` is the identity matrix of the same size as :math:`X_j`. Similarly,
    the weights (of :func:`~.get_tensor_sirt_weights`) are computed as

    .. math::
        W_{iill} = \frac{I(n_j) \otimes I(n_k)}{\sum_{j, k} P_{ij} U_{kl}}.

    Here, any singularities in the system (e.g., where :math:`\sum_j P_{ij} = 0`) can be masked out
    by setting the corresponding weight to zero.
    We thus end up with a weighted least-squares system

    .. math::
        \text{argmin}_X(\Vert W_{iill}(P_{ij} X_{jk} U_{kl} - D_{il})\Vert^2_2),

    where :math:`D_{il}` is some data.
    This problem can be solved iteratively by preconditioned gradient descent,

    .. math::
        X_j^{k + 1} = X_j^k - C_{jjkk}P_{ji}^TW_{iill}(P_ij X_{jk}^k U_{kl} - D_{il}).

    Parameters
    ----------
    projector
        A :ref:`projector <projectors>` object which is used to calculate the weights.
        The computation of the weights is based on the geometry attached to the projector.
    basis_set
        A :ref:`basis set <basis_sets>` object which is used to calculate the weights.
        The tensor-space-to-detector-space transform uses the basis set.
        Should use a local representation.
    cutoff
        The minimal number of rays that need to map to a voxel for it
        to be considered valid. Default is ``0.1``. Invalid voxels will
        be masked from the preconditioner.
    """
    sirt_projections = np.ones((projector.number_of_projections,) +
                               projector.projection_shape +
                               (basis_set.probed_coordinates.vector.shape[1],),
                               dtype=projector.dtype)
    inverse_preconditioner = projector.adjoint(basis_set.gradient(sirt_projections).astype(projector.dtype))
    mask = np.ceil(inverse_preconditioner > projector.dtype(cutoff)).astype(projector.dtype)
    return mask * np.reciprocal(np.fmax(inverse_preconditioner, cutoff))


def get_sirt_preconditioner(projector: Projector, cutoff: float = 0.1) -> NDArray[float]:
    r""" Retrieves the :term:`SIRT` `preconditioner <https://en.wikipedia.org/wiki/Preconditioner>`_,
    which can be used together
    with the :term:`SIRT` weights to condition the
    gradient of tomographic calculations for faster convergence and scaling of the
    step size for gradient descent.

    Notes
    -----
    The preconditioner normalizes the gradient according to the number
    of data points that map to each voxel in the computation of
    the projection adjoint. This preconditioner scales and conditions
    the gradient for better convergence. It is best combined with the :term:`SIRT`
    weights, which normalize the residual for the number of voxels.
    When used together, they condition the reconstruction sufficiently
    well that a gradient descent optimizer with step size unity can arrive
    at a good solution. Other gradient-based solvers can also benefit from this
    preconditioning.

    In addition, the calculation of these preconditioning terms makes it easy to identify
    regions of the volume or projections that are rarely probed, allowing them to be
    masked from the solution altogether.

    If the projection operation is written in sparse matrix form as

    .. math::
        P_{ij} X_{j} = Y_i

    where :math:`P_{ij}` is the projection matrix, :math:`X_j` is a vector of voxels, and :math:`Y_i`
    is the projection, then the preconditioner can be understood as

    .. math::
        C_{jj} = \frac{I(n_j)}{\sum_i P_{ij}}

    where :math:`I(n_j)` is the identity matrix of the same size as :math:`X_j`. Similarly,
    the weights (of :func:`~.get_sirt_weights`) are computed as

    .. math::
        W_{ii} = \frac{I(n_i)}{\sum_j P_{ij}}.

    Here, any singularities in the system (e.g., where :math:`\sum_j P_{ij} = 0`) can be masked out
    by setting the corresponding weight to zero.
    We thus end up with a weighted least-squares system

    .. math::
        \text{argmin}_X(\Vert W_{ii}(P_{ij}X_{j} - D_{i})\Vert^2_2)

    where :math:`D_{i}` is some data, which we can solve iteratively by preconditioned gradient descent,

    .. math::
        X_j^{k + 1} = X_j^k - C_{jj}P_{ji}^TW_{ii}(P_ij X_j^k - D_i)

    As mentioned, we can add additional regularization terms, and because the preconditioning
    scales the problem appropriately, computing an optimal step size is not a requirement,
    although it can speed up the solution. This establishes a very flexible system, where
    quasi-Newton solvers such as :term:`LBFGS` can be seamlessly combined with less restrictive
    gradient descent methods.

    A good discussion of the algorithmic properties of :term:`SIRT` can be found in
    `this article by Gregor et al. <https://doi.org/10.1109%2FTCI.2015.2442511>`_,
    while `this article by van der Sluis et al. <https://doi.org/10.1016/0024-3795(90)90215-X>`_
    discusses :term:`SIRT` as a least-squares solver in comparison to the
    conjugate gradient (:term:`CG`) method.

    Parameters
    ----------
    projector
        A :ref:`projector <projectors>` object which is used to calculate the weights.
        The computation of the weights is based on the geometry attached to the projector.
    cutoff
        The minimal number of rays that need to map to a voxel for it
        to be considered valid. Default is ``0.1``. Invalid voxels will
        be masked from the preconditioner.
    """
    sirt_projections = np.ones((projector.number_of_projections,) +
                               projector.projection_shape +
                               (1,), dtype=projector.dtype)
    inverse_preconditioner = projector.adjoint(sirt_projections)
    mask = np.ceil(inverse_preconditioner > projector.dtype(cutoff)).astype(projector.dtype)
    return mask * np.reciprocal(np.fmax(inverse_preconditioner, cutoff))


def get_tensor_sirt_weights(projector: Projector, basis_set: BasisSet, cutoff: float = 0.1) -> NDArray[float]:
    """ Retrieves the tensor :term:`SIRT` weights, which can be used together with the
    :term:`SIRT` preconditioner to weight the
    residual of tensor tomographic calculations for faster convergence and
    scaling of the step size for gradient descent.

    Notes
    -----
    See :func:`~.get_tensor_sirt_preconditioner` for theoretical details.

    Parameters
    ----------
    projector
        A :ref:`projector <projectors>` object which is used to calculate the weights.
        The computation of the weights is based on the geometry attached to the projector.
    basis_set
        A :ref:`basis set <basis_sets>` object which is used to calculate the weights.
        The tensor-space-to-detector-space transform uses the basis set.
        Should use a local representation.
    cutoff
        The minimal number of voxels that need to map to a point for it
        to be considered valid. Default is ``0.1``. Invalid pixels will be
        masked.
    """
    sirt_field = np.ones(projector.volume_shape +
                         (len(basis_set),), dtype=projector.dtype)
    inverse_weights = projector.forward(sirt_field)
    inverse_weights = basis_set.forward(inverse_weights)
    mask = np.ceil(inverse_weights > projector.dtype(cutoff)).astype(projector.dtype)
    return mask * np.reciprocal(np.fmax(inverse_weights, cutoff))


def get_sirt_weights(projector: Projector, cutoff: float = 0.1) -> NDArray[float]:
    """ Retrieves the :term:`SIRT` weights, which can be used together with the
    :term:`SIRT` preconditioner to weight the
    residual of tomographic calculations for faster convergence and
    scaling of the step size for gradient descent.

    Notes
    -----
    See :func:`~.get_sirt_preconditioner` for theoretical details.

    Parameters
    ----------
    projector
        A :ref:`projector <projectors>` object which is used to calculate the weights.
        The computation of the weights is based on the geometry attached to the projector.
    cutoff
        The minimal number of voxels that need to map to a point for it
        to be considered valid. Default is ``0.1``. Invalid pixels will be
        masked.
    """
    sirt_field = np.ones(projector.volume_shape +
                         (1,), dtype=projector.dtype)
    inverse_weights = projector.forward(sirt_field)
    mask = np.ceil(inverse_weights > projector.dtype(cutoff)).astype(projector.dtype)
    return mask * np.reciprocal(np.fmax(inverse_weights, cutoff))
