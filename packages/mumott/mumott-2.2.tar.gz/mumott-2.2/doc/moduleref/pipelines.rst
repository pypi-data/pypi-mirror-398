Pipelines
=========

A number of pipelines are included in ``mumott``, which pre-define common workflows.

The standard reconstruction pipelines include:

- Filtered back-projection (FBP):
  Standard implementation of the inverse Radon formula for reconstruction of absorptivity from diode data.
- Modular Iterative Tomographic Reconstruction Algorithm (MITRA):
  Reliable tensor-tomographic reconstruction algorithm which uses Gaussian kernels, normalizing weights and preconditioners, and momentum-accelerated gradient descent.
  Highly configurable.
- Simultaneous Iterative Reconstruction Tomography (SIRT):
  Standard tomographic algorithm which reconstructs through preconditioned gradient descent.
  Configured mainly by modifying the maximum number of iterations.
- Spherical Integral Geometric Tensor Tomography (SIGTT):
  Tensor tomography using a spherical harmonic representation, a quasi-Newton solver, and Laplacian regularization.
  Highly configurable.
- Discrete Directions (DD). Bins reciprocal space directions on the reciprocal space sphere and solves for each of them separately using SIRT. Easy to get started with.

The asynchronous pipelines include:

- Tensor SIRT:
  Asynchronous implementation of SIRT for tensor tomography, using weights and a preconditioner which account for the representation used.
- Momentum Total variation Reconstruction (MOTR):
  Similar to Tensor SIRT, but uses Nestorov momentum, and optionally an L1 and :term:`total variation <TV>` regularizer.
- Robust And Denoised Tensor Tomography (RADTT):
  Uses a Huber norm for robust regression, which makes it less sensitive to outliers and noise than other pipelines.
  Includes :term:`total variation <TV>` regularization.

The asynchronous pipelines have sparse counterparts, which function similarly, but are more efficient with respect to memory at the expense of only optimizing a few basis functions for each projection.

The alignment pipelines are:

- Phase matching alignment:
  An alignment pipeline that uses cross-correlation to align data.
- Optical flow alignment:
  Uses the optical flow algorithm described in [Odstrcil2019]_ to align data in multiple steps.

.. _reconstruction_pipelines:

Reconstruction
--------------

.. autofunction:: mumott.pipelines.filtered_back_projection.run_fbp

.. autofunction:: mumott.pipelines.reconstruction.run_mitra

.. autofunction:: mumott.pipelines.reconstruction.run_sirt

.. autofunction:: mumott.pipelines.reconstruction.run_sigtt

.. autofunction:: mumott.pipelines.reconstruction.run_discrete_directions

.. autofunction:: mumott.pipelines.reconstruction.run_group_lasso

.. _async_pipelines:

.. autofunction:: mumott.pipelines.async_pipelines.run_tensor_sirt

.. autofunction:: mumott.pipelines.async_pipelines.run_motr

.. autofunction:: mumott.pipelines.async_pipelines.run_radtt

.. _sparse_pipelines:

.. autofunction:: mumott.pipelines.sparse_pipelines.run_stsirt

.. autofunction:: mumott.pipelines.sparse_pipelines.run_smotr

.. autofunction:: mumott.pipelines.sparse_pipelines.run_spradtt

.. _alignment_pipelines:

Alignment
---------

.. graphviz:: ../_static/alignment_pipelines.dot

This diagram shows an overview of how the alignment pipelines work.
Dashed-outline steps are exclusive to the optical flow alignment. 

.. autofunction:: mumott.pipelines.phase_matching_alignment.run_phase_matching_alignment

.. autofunction:: mumott.pipelines.optical_flow_alignment.run_optical_flow_alignment

.. _alignment_utilities:

Utilities
---------

.. autofunction:: mumott.pipelines.fbp_utilities.get_filtered_projections

.. autofunction:: mumott.pipelines.utilities.alignment_geometry.get_alignment_geometry

.. autofunction:: mumott.pipelines.utilities.alignment_geometry.shift_center_of_reconstruction
