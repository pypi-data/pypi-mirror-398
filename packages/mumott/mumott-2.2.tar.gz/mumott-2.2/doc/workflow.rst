.. _workflow:
.. index:: Workflow

.. raw:: html

    <style> .orange {color:orange} </style>
    <style> .blue {color:CornflowerBlue} </style>
    <style> .green {color:darkgreen} </style>

.. role:: orange
.. role:: blue
.. role:: green


Workflow
********

There are two main levels of access to :program:`mumott`.
Most routine tasks with regard to alignment of reconstruction can be accomplished via **pipelines**, which are provided in the form of **functions**.

Internally the pipelines are constructed using **objects**.
The latter provide more fine-grained control over alignment or reconstruction, and can be used to construct custom pipelines.

Pipelines
=========

Reconstruction workflows are most easily accessed via :ref:`reconstruction pipelines <reconstruction_pipelines>`.
A pipeline represents a series of subtasks, which are represented via :ref:`objects <object_structure>`.
This structure makes it possible to replace some of the components in the pipeline with others preferred by the user.

.. graphviz:: _static/pipeline.dot

The user interaction with the pipeline can be understood as follows:

#. A :class:`DataContainer <mumott.data_handling.DataContainer>` instance is created from input.

#. The :class:`DataContainer <mumott.data_handling.DataContainer>` is passed to a :ref:`pipeline <reconstruction_pipelines>` function, e.g., the :func:`MITRA pipeline function <mumott.pipelines.reconstruction.run_mitra>`, along with user-specified parameters as keyword arguments.

#. For example, one might want to add a :class:`Total Variation <mumott.optimization.regularization.total_variation.TotalVariation>` regularizer, which requires submitting a list with a dictionary containing the regularizer, its name, and weight.
   In addition, the user will probably pass values for the arguments ``use_gpu`` (depending on whether they have a CUDA-capable GPU) and ``use_absorbances`` (``True`` if they want to reconstruct the absorbances from the diode measurement, ``False`` if they want to carry out tensor tomography).

#. The :func:`MITRA pipeline <mumott.pipelines.reconstruction.run_mitra>` executes, and returns a ``dict`` which contains the entry ``'result'`` with the optimization coefficients.
   In addition, it contains the entries ``optimizer``, ``loss_function``, ``residual_calculator``, ``basis_set``, and ``projector``, all containing the instances of the respective objects used in the pipeline.

#. The optimized coefficients can then be processed via the :ref:`basis set object <basis_sets>` function :func:`get_output`
   to generate :green:`tensor field properties` such as the anisotropy or the orientation distribution returned as a ``dict``.

#. The function :func:`dict_to_h5 <mumott.output_handling.dict_to_h5>` can be used to convert this dictionary of properties into an ``h5`` file to be further processed or visualized.

Alignment workflow can be accessed via :ref:`alignment pipelines <alignment_pipelines>`.
They are used similarly to reconstruction pipelines, but their output is instead the parameters needed to align the projections of the data set.

.. graphviz:: _static/alignment.dot

The interaction is similar to that of the reconstruction pipelines:

#. A :class:`DataContainer <mumott.data_handling.DataContainer>` instance is created from input.

#. The :class:`DataContainer <mumott.data_handling.DataContainer>` is passed to a :ref:`pipeline <alignment_pipelines>` function, e.g., the :func:`phase matching alignment <mumott.pipelines.alignment.phase_matching_alignment.run_phase_matching_alignment>`, along with some user-specified parameters.

#. For example, the user might want to reduce the initial number of iterations, or increase the upsampling rate. It is also possible to pass a specific reconstruction pipeline, e.g., the :func:`filtered back-projection <mumott.pipelines.filtered_back_projection.run_fbp>` pipeline.

#. The alignment executes, and returns a dictionary of aligned reconstructions. For the phase-matching alignment, the parameters are automatically saved in the :class:`Geometry <mumott.core.geometry.Geometry>` atteched to the :class:`DataContainer <mumott.data_handling.DataContainer>`. For the :func:`optical flow alignemnt <mumott.pipelines.alignment.optical_flow_alignmnent.run_optical_flow_alignment>`, they are returned as a tuple in three-dimensional space that must be translated into projection space; see the documentation string for the optical flow pipeline for more details.


.. _object_structure:

Object structure
================

The following figure illustrates the :program:`mumott` object structure.
Here, classes are shown in :blue:`blue`, input parameters and data in :orange:`orange`, and output data in :green:`green`.

.. graphviz:: _static/workflow.dot

A typical workflow involves the following steps:

#. First the :orange:`measured data along with its metadata` is loaded into a :class:`DataContainer <mumott.data_handling.DataContainer>` object.
   The latter allows one to access, inspect, and modify the data in various ways as shown in the
   `tutorial on loading and inspecting data tutorial <tutorials/inspect_data.html>`_.
   Note that it is possible to skip the full data when instantiating a :class:`DataContainer <mumott.data_handling.DataContainer>` object.
   In that case only geometry and diode data are read, which is much faster and sufficient for alignment.

#. The :class:`DataContainer <mumott.data_handling.DataContainer>` object holds the information pertaining to the geometry of the data.
   The latter is stored in the :attr:`geometry <mumott.data_handling.DataContainer.geometry>` property of the
   :class:`DataContainer <mumott.data_handling.DataContainer>` object in the form of a :class:`Geometry <mumott.core.geometry.Geometry>` object.

#. The geometry information is then used to set up a :ref:`projector object <projectors>`,
   e.g., :attr:`SAXSProjector <mumott.methods.projectors.SAXSProjector>`.
   Projector objects allow one to transform tensor fields from three-dimensional space to projection space.

#. Next a :ref:`basis set object <basis_sets>` such as, e.g., :class:`SphericalHarmonics <mumott.methods.basis_sets.SphericalHarmonics>`, is set up.

#. One can then combine the :ref:`projector object <projectors>`, the :ref:`basis set <basis_sets>`, and the data from
   the :class:`DataContainer <mumott.data_handling.DataContainer>` object to set up a :ref:`residual calculator object <residual_calculators>`.
   :ref:`Residual calculator objects <residual_calculators>` hold the coefficients that need to be optimized and allow one to compute the residuals of the current representation.

#. To find the optimal coefficients a :ref:`loss function object <loss_functions>` is set up, using, e.g., the :class:`SquaredLoss <mumott.optimization.loss_functions.SquaredLoss>` or :class:`HuberLoss <mumott.optimization.loss_functions.HuberLoss>` classes.
   The :ref:`loss function <loss_functions>` can include one or several regularization terms, which are defined by :ref:`regularizer objects <regularizers>` such as :class:`L1Norm <mumott.optimization.regularizers.L1Norm>`, :class:`L2Norm <mumott.optimization.regularizers.L2Norm>` or :class:`TotalVariation <mumott.optimization.regularizers.TotalVariation>`.

#. The :ref:`loss function object <loss_functions>` is then handed over to an :ref:`optimizer object <optimizers>`,
   such as :class:`LBFGS <mumott.optimization.optimizers.LBFGS>` or :class:`GradientDescent <mumott.optimization.optimizers.GradientDescent>`,
   which updates the coefficients of the :ref:`residual calculator object <residual_calculators>`.

#. The :func:`get_output` method of the :ref:`basis set <basis_sets>` can then be used to generate tensor field properties, as in the pipeline workflow.


Asynchronous reconstruction
===========================


The regular object-oriented structure and pipelines can leverage the GPU to carry out some computations for increased efficiency, but still operate synchronously.
This means the CPU synchronizes with the GPU twice or more per iteration, which can cause a large computational overhead.

A more computationally efficient approach is to carry out all computations using the GPU.
This is made possible through the use of :ref:`CUDA kernels <cuda_kernels>` not only for the :ref:`John transform <john_transform>` but for all arithmetic and linear-algebraic computations necessary for an optimization.

Using specialized kernels allows us to not only carry out asynchronous operations (meaning the CPU sends instructions to the GPU ahead-of-time, and only waits for these instructions to be carried out at relatively long intervals), but also to optimize memory usage by pre-allocating arrays and exploiting in-place operations.
However, much of the standard object structure cannot be used any more - functions for, e.g., calculating regularization gradients and loss functions must be re-written in CUDA.
Additionally, asynchronous optimizers cannot make heavy use of conditional behavior (such as if-statements which lead to different branches) in each iteration, since this typically requires a synchronization.
Instead, it is most straightforward to use gradient descent-like methods terminated by selecting the maximum number of iterations.

Asynchronous pipelines use some functions and properties of standard objects, like :ref:`basis set objects <basis_sets>` and :ref:`projectors <projectors>`, to generate the necessary kernels, but do not use object methods in the actual optimization.
Therefore, each pipeline uses a predefined set of features such as regularizers, a maximum number of iterations, and so on, which are directly configurable via keyword arguments.

#. A :class:`DataContainer <mumott.data_handling.DataContainer>` instance is created from input.

#. The :class:`DataContainer <mumott.data_handling.DataContainer>` is passed to an asynchronous :ref:`pipeline <async_pipelines>`, along with optional arguments such as the number of iterations, and how often the optimization should be synchronized to update the user on its progress.

#. The pipeline carries out all of the allocations of device-side (GPU) arrays, and the computation is carried out asynchronously on the GPU.

#. The pipeline returns a dictionary with the reconstruction and some additional properties, such as the evolution of the loss function.
   The reconstructed coefficients can be processed similarly to the result of any other reconstruction.

Expert users may wish to construct their own asynchronous pipelines by following the structure of the asynchronous pipelines and making use of :ref:`CUDA kernels <cuda_kernels>`.
