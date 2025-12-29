import sys
import numpy as np
import tqdm
from numba import cuda

from mumott.core.john_transform_sparse_cuda import (john_transform_sparse_cuda,
                                                    john_transform_adjoint_sparse_cuda)
from mumott.core.cuda_kernels import (cuda_weighted_difference, cuda_scaled_difference,
                                      cuda_sum, cuda_rescale, cuda_difference,
                                      cuda_rescale_array,
                                      cuda_l1_gradient, cuda_tv_gradient, cuda_weighted_sign,
                                      cuda_lower_bound)
from mumott.data_handling import DataContainer
from mumott.methods.basis_sets import GaussianKernels
from mumott.methods.basis_sets.base_basis_set import BasisSet
from mumott.methods.projectors import SAXSProjectorCUDA
from mumott.methods.utilities import get_tensor_sirt_weights, get_tensor_sirt_preconditioner
from mumott.optimization.regularizers import L1Norm, TotalVariation


def run_stsirt(data_container: DataContainer,
               maxiter: int = 10,
               sparsity_count: int = 3,
               basis_set: BasisSet = None,
               update_frequency: int = 5):
    """A sparse basis implementation of the tensor SIRT algorithm (Sparse Tensor SIRT).
    This approach uses only
    asynchronous, in-place operations on the GPU, and is therefore much faster
    than standard pipelines, as well as more memory-efficient.
    In exchange, it is less modular and requires a relatively sparse basis set.

    Parameters
    ----------
    data_container
        The data.
    maxiter
        Maximum number of iterations.
    sparsity_count
        The maximum number of non-zero matrix elements per detector segment,
        if using the default ``BasisSet``. Not used if a custom ``BasisSet`` is provided.
    basis_set
        A custom ``BasisSet`` instance. By default, a ``GaussianKernels`` with
        ``enforce_sparsity=True`` and ``sparsity_count=sparsity_count`` is used.
    update_frequency
        Synchronization and norm reduction progress printing frequency. If set too small,
        the optimization will be slower due to frequent host-device synchronization. This effect
        can be seen by noting the iterations per second on the progress bar. The printed
        norm does not account for the total variation regularization.

    Returns
    -------
        Dictionary with ``reconstruction``, ``projector``, ``basis_set`` entries.
    """
    # Create projector for simple fetching of parameters
    projector = SAXSProjectorCUDA(data_container.geometry)
    if basis_set is None:
        grid_scale = data_container.data.shape[-1] // 2 + 1
        basis_set = GaussianKernels(grid_scale=grid_scale,
                                    probed_coordinates=data_container.geometry.probed_coordinates,
                                    enforce_sparsity=True,
                                    sparsity_count=sparsity_count)
    # Get weights, etc
    weights = get_tensor_sirt_weights(projector=projector,
                                      basis_set=basis_set)
    weights[data_container.projections.weights <= 0.] = 0.
    weights = cuda.to_device(weights.astype(np.float32))
    preconditioner = cuda.to_device(get_tensor_sirt_preconditioner(
        projector=projector, basis_set=basis_set).astype(np.float32))
    sparse_matrix = basis_set.csr_representation
    # Allocate matricess, compile kernels
    reconstruction = cuda.to_device(
            np.zeros(tuple(data_container.geometry.volume_shape) + (len(basis_set),), dtype=np.float32))
    projections = cuda.to_device(np.zeros_like(data_container.data, dtype=np.float32))
    forward = john_transform_sparse_cuda(reconstruction, projections,
                                         sparse_matrix, *projector.john_transform_parameters)
    adjoint = john_transform_adjoint_sparse_cuda(reconstruction, projections,
                                                 sparse_matrix, *projector.john_transform_parameters)
    weighted_difference = cuda_weighted_difference(projections.shape)
    scaled_difference = cuda_scaled_difference(reconstruction.shape)
    data = cuda.to_device(data_container.data.astype(np.float32))
    gradient = cuda.to_device(np.zeros(reconstruction.shape, dtype=np.float32))
    # Run asynchronous reconstruction
    pbar = tqdm.trange(maxiter, file=sys.stdout)
    pbar.update(0)
    for i in range(maxiter):
        # compute residual gradient
        weighted_difference(data, projections, weights)
        # compute gradient with respect to john transform
        adjoint(gradient, projections)
        # update reconstruction
        scaled_difference(gradient, reconstruction, preconditioner)
        # forward john transform
        forward(reconstruction, projections)
        # update user on progress
        if (i + 1) % update_frequency == 0:
            cuda.synchronize()
            pbar.update(update_frequency)
    return dict(reconstruction=np.array(reconstruction), projector=projector, basis_set=basis_set,
                projection=np.array(projections))


def run_smotr(data_container: DataContainer,
              maxiter: int = 10,
              sparsity_count: int = 3,
              momentum: float = 0.9,
              l1_weight: float = 1e-3,
              tv_weight: float = 1e-3,
              basis_set: BasisSet = None,
              update_frequency: int = 5,
              lower_bound: float = None,
              step_size: float = 1.):
    """ SMOTR (Sparse MOmentum Total variation Reconstruction) pipeline
    that uses asynchronous GPU (device) computations only
    during the reconstruction. This leads to a large speedup compared to standard pipelines
    which synchronize with the CPU several times per iteration. However, this implementation
    is less modular than standard pipelines.

    This pipeline uses Nestorov Momentum in combination with total variation and L1 regularization,
    as well as the Tensor SIRT preconditioner-weight pair.

    This is also a highly efficient implementation with respect to device memory, as all arithmetic
    operations are done in-place.

    Parameters
    ----------
    data_container
        The container for the data.
    maxiter
        Maximum number of iterations.
    sparsity_count
        The maximum number of non-zero matrix elements per detector segment.
    momentum
        Momentum for the Nestorov gradient
    l1_weight
        Weight for L1 regularization.
    tv_weight
        Weight for total variation regularization.
    basis_set
        User-provided basis set to be used, if desired.
        By default, a ``GaussianKernels`` basis set is used.
    update_frequency
        Synchronization and norm reduction progress printing frequency. If set too small,
        the optimization will be slower due to frequent host-device synchronization. This effect
        can be seen by noting the iterations per second on the progress bar. The printed
        norm does not account for the total variation regularization.
    lower_bound
        Lower bound to threshold coefficients at in each iteration. Can be used to
        e.g. enforce non-negativity for local basis sets such as ``GaussianKernels``.
        Not used if set to ``None``, which is the default settingz.
    step_size
        Step size for each iteration in the reconstruction. Default value is ``1.`` which
        should be a suitable value in the vast majority of cases, due to the normalizing
        effect of the weight-preconditioner pair used.

    Returns
    -------
        Dictionary with ``reconstruction``, ``projector``, ``basis_set``, ``loss_curve`` entries.
        ``loss_curve`` is an array with ``maxiter // update_frequency`` rows where the entries
        in each column are ``iteration, loss, residual_norm, tv_norm``.
    """
    projector = SAXSProjectorCUDA(data_container.geometry)
    if basis_set is None:
        grid_scale = data_container.data.shape[-1] // 2 + 1
        basis_set = GaussianKernels(grid_scale=grid_scale,
                                    probed_coordinates=data_container.geometry.probed_coordinates,
                                    enforce_sparsity=True,
                                    sparsity_count=sparsity_count)
    weights = get_tensor_sirt_weights(projector=projector,
                                      basis_set=basis_set)
    weights[data_container.projections.weights <= 0.] = 0.
    host_weights = weights.astype(np.float32)
    weights = cuda.to_device(host_weights)
    step_size = np.float32(step_size)
    preconditioner = cuda.to_device(
            step_size * get_tensor_sirt_preconditioner(
                projector=projector, basis_set=basis_set).astype(np.float32))
    sparse_matrix = basis_set.csr_representation
    reconstruction = cuda.to_device(
            np.zeros(tuple(data_container.geometry.volume_shape) + (len(basis_set),), dtype=np.float32))
    # Compile all CUDA kernels:
    projections = cuda.to_device(np.zeros_like(data_container.data, dtype=np.float32))
    forward = john_transform_sparse_cuda(reconstruction, projections,
                                         sparse_matrix, *projector.john_transform_parameters)
    adjoint = john_transform_adjoint_sparse_cuda(reconstruction, projections,
                                                 sparse_matrix, *projector.john_transform_parameters)
    weighted_difference = cuda_weighted_difference(projections.shape)
    difference = cuda_difference(reconstruction.shape)
    sum_kernel = cuda_sum(reconstruction.shape)
    l1_gradient = cuda_l1_gradient(reconstruction.shape, l1_weight)
    tv_gradient = cuda_tv_gradient(reconstruction.shape, tv_weight)
    scale_array = cuda_rescale_array(reconstruction.shape)
    rescale = cuda_rescale(reconstruction.shape, momentum)
    # Allocate remaining CUDA arrays
    data = cuda.to_device(data_container.data.astype(np.float32))
    host_data = data_container.data.astype(np.float32)
    host_projections = np.array(projections)
    gradient = cuda.to_device(np.zeros(reconstruction.shape, dtype=np.float32))
    total_gradient = cuda.to_device(np.zeros(reconstruction.shape, dtype=np.float32))
    diff = host_projections - host_data
    lf = (host_weights * diff * diff).sum()
    pbar = tqdm.trange(maxiter, file=sys.stdout)
    pbar.set_description(f'Loss: {lf:.2e}')
    pbar.update(0)
    loss_curve = []
    host_l1 = L1Norm()
    host_tv = TotalVariation(None)
    if lower_bound is not None:
        lower_kernel = cuda_lower_bound(reconstruction.shape, lower_bound)
    # Actual reconstruction. This part executes asynchronously.
    for i in range(maxiter):
        # compute residual gradient
        weighted_difference(data, projections, weights)
        # compute gradient with respect to john transform
        adjoint(gradient, projections)
        # apply preconditioner
        scale_array(gradient, preconditioner)
        # apply regularization
        l1_gradient(reconstruction, gradient)
        tv_gradient(reconstruction, gradient)
        # apply gradient (correction term)
        difference(reconstruction, gradient)
        # add to accumulated gradient
        sum_kernel(total_gradient, gradient)
        # scale by momentum coefficient
        rescale(total_gradient)
        # apply gradient (momentum term)
        difference(reconstruction, total_gradient)
        # threshold
        if lower_bound is not None:
            lower_kernel(reconstruction)
        # forward john transform
        forward(reconstruction, projections)
        # compute host-side quantities to update user on progress.
        if (i + 1) % update_frequency == 0:
            # forces synchronization
            host_projections = np.array(projections)
            host_recon = np.array(reconstruction)
            rg1 = host_l1.get_regularization_norm(host_recon)['regularization_norm']
            rg2 = host_tv.get_regularization_norm(host_recon)['regularization_norm']
            diff = host_projections - host_data
            rn = (host_weights * diff * diff).sum()
            lf = rg1 * l1_weight + rg2 * tv_weight + rn
            loss_curve.append((i, lf, rn, rg1, rg2))
            pbar.set_description(f'Loss: {lf:.2e} Res.norm: {rn:.2e} L1 norm: {rg1:.2e} TV norm: {rg2:.2e}')
            pbar.update(update_frequency)
    return dict(reconstruction=np.array(reconstruction), projector=projector, basis_set=basis_set,
                projection=np.array(projections), loss_curve=np.array(loss_curve))


def run_spradtt(data_container: DataContainer,
                maxiter: int = 10,
                sparsity_count: int = 3,
                momentum: float = 0.9,
                step_size: float = 1.,
                delta: float = 1.,
                tv_weight: float = 1e-3,
                basis_set: BasisSet = None,
                lower_bound: float = 0.,
                update_frequency: int = 5):
    """ SPRADTT (SParse Robust And Denoised Tensor Tomography) pipeline
    that uses asynchronous GPU (device) computations only
    during the reconstruction. This leads to a large speedup compared to standard pipelines
    which synchronize with the CPU several times per iteration. However, this is only suitable
    for sparse representations and therefore this implementation
    is less modular than standard pipelines.

    This pipeline uses Nestorov accelerated gradient descent, with a Huber loss function
    and total variation regularization. This reconstruction approach requires a large number
    of iterations, but is robust to outliers in the data.

    This is also a highly efficient implementation with respect to device memory, as all arithmetic
    operations are done in-place.

    Parameters
    ----------
    data_container
        The container for the data.
    maxiter
        Maximum number of iterations.
    sparsity_count
        The maximum number of non-zero matrix elements per detector segment.
    momentum
        Momentum for the Nestorov gradient. Should be in the range ``[0., 1.]``.
    step_size
        Step size for L1 optimization. Step size for
        L2 part of optimization is ``step_size / (2 * delta)``. A good choice
        for the step size is typically around the same order of magnitude
        as each coefficient of the reconstruction.
    delta
        Threshold for transition to L2 optimization. Should be small relative to data.
        Does not affect total variation.
    tv_weight
        Weight for total variation regularization.
    basis_set
        User-provided basis set to be used, if desired.
        By default, a ``GaussianKernels`` basis set is used.
    lower_bound
        Lower bound to threshold coefficients at in each iteration. Can be used to
        e.g. enforce non-negativity for local basis sets such as ``GaussianKernels``.
        Not used if set to ``None``, which is the default settingz.
    update_frequency
        Synchronization and norm reduction progress printing frequency. If set too small,
        the optimization will be slower due to frequent host-device synchronization. This effect
        can be seen by noting the iterations per second on the progress bar. The printed
        norm does not account for the total variation regularization.

    Returns
    -------
        Dictionary with ``reconstruction``, ``projector``, ``basis_set``, ``loss_curve`` entries.
    """
    projector = SAXSProjectorCUDA(data_container.geometry)
    if basis_set is None:
        grid_scale = data_container.data.shape[-1] // 2 + 1
        basis_set = GaussianKernels(grid_scale=grid_scale,
                                    probed_coordinates=data_container.geometry.probed_coordinates,
                                    enforce_sparsity=True,
                                    sparsity_count=sparsity_count)
    weights = get_tensor_sirt_weights(projector=projector,
                                      basis_set=basis_set)
    weights[data_container.projections.weights <= 0.] = 0.
    host_weights = weights.astype(np.float32)
    weights = cuda.to_device(weights.astype(np.float32))
    preconditioner = cuda.to_device(
            (step_size) * get_tensor_sirt_preconditioner(
                projector=projector, basis_set=basis_set).astype(np.float32))
    sparse_matrix = basis_set.csr_representation
    reconstruction = cuda.to_device(
            np.zeros(tuple(data_container.geometry.volume_shape) + (len(basis_set),), dtype=np.float32))
    # Compile all CUDA kernels
    projections = cuda.to_device(np.zeros_like(data_container.data, dtype=np.float32))
    forward = john_transform_sparse_cuda(reconstruction, projections,
                                         sparse_matrix, *projector.john_transform_parameters)
    adjoint = john_transform_adjoint_sparse_cuda(reconstruction, projections,
                                                 sparse_matrix, *projector.john_transform_parameters)
    weighted_sign = cuda_weighted_sign(projections.shape, delta)
    difference = cuda_difference(reconstruction.shape)
    sum_kernel = cuda_sum(reconstruction.shape)
    tv_gradient = cuda_tv_gradient(reconstruction.shape, tv_weight)
    scale_array = cuda_rescale_array(reconstruction.shape)
    rescale = cuda_rescale(reconstruction.shape, momentum)
    if lower_bound is not None:
        threshold_lower = cuda_lower_bound(reconstruction.shape, lower_bound)
    # Allocate remaining CUDA arrays
    host_data = data_container.data.astype(np.float32)
    data = cuda.to_device(data_container.data.astype(np.float32))
    gradient = cuda.to_device(np.zeros(reconstruction.shape, dtype=np.float32))
    total_gradient = cuda.to_device(np.zeros(reconstruction.shape, dtype=np.float32))
    # Create necessary host-side objects for output
    pbar = tqdm.trange(maxiter, file=sys.stdout)
    host_projections = np.array(projections)
    lf = (host_weights * abs(host_projections - host_data)).sum()
    rg = 0.
    pbar.set_description(f'Loss: {lf:.2e} Res.norm: {lf:.2e} TV norm: {rg:.2e}')
    pbar.update(0)
    loss_curve = []
    host_tv = TotalVariation(None)
    # Actual reconstruction. This part executes asynchronously.
    for i in range(maxiter):
        # residual norm gradient
        weighted_sign(data, projections, weights)
        # john transform gradient
        adjoint(gradient, projections)
        # apply preconditioner
        scale_array(gradient, preconditioner)
        # apply total variation regularization
        tv_gradient(reconstruction, gradient)
        # update reconstruction by gradient (correction term)
        difference(reconstruction, gradient)
        # compute updated momentum term
        sum_kernel(total_gradient, gradient)
        # apply momentum decay
        rescale(total_gradient)
        # update reconstruction by gradient (momentum term)
        difference(reconstruction, total_gradient)
        # threshold by lower bound
        if lower_bound is not None:
            threshold_lower(reconstruction)
        # forward john transform
        forward(reconstruction, projections)
        # compute host-side quantities to update user on progress
        if (i + 1) % update_frequency == 0:
            # forces synchronization
            host_projections = np.array(projections)
            host_recon = np.array(reconstruction)
            rg = host_tv.get_regularization_norm(host_recon)['regularization_norm']
            diff = host_projections - host_data
            rn = (host_weights * diff * diff).sum()
            lf = rg * tv_weight + rn
            loss_curve.append((i, lf, rn, rg))
            pbar.set_description(f'Loss: {lf:.2e} Res.norm: {rn:.2e} TV norm: {rg:.2e}')
            pbar.update(update_frequency)
    return dict(reconstruction=np.array(reconstruction), projector=projector,
                basis_set=basis_set, projection=np.array(projections), loss_curve=np.array(loss_curve))
