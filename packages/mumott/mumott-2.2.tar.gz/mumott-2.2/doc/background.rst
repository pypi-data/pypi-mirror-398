.. _background:
.. index:: Background

Background
**********

Tensor tomography refers to a family of methods for probing tensor-valued quantities in a volume-resolved manner.
In traditional tomography, a scalar value (such as the absorptivity of a material) is reconstructed within a volume, from two-dimensional depth-probed images (for simplicity referred to as projections, although the images are not necessarily projections in the mathematical sense) of that volume.
In tensor tomography, a measurement occurs over several channels, _e.g._, with different diffraction gratings, polarizations or scattering directions [Liebi2015]_, [Schaff2015]_.
Thus, the problem of tensor tomography can be understood as the reconstruction of a tensor field from two-dimensional projections of that tensor field [Gao2019]_.

In its most general sense, tensor tomography therefore requires both a tomography component (which contains a mapping between projection space and three-dimensional space) as well as a tensor representation component, which contains some mapping from the measured channels to the reconstructed tensor.
In the simpler cases, this can be written on a linear form [Nielsen2023]_,

.. math ::
    PXA = D

where :math:`P` is a projection matrix, :math:`X` is a matrix containing the coefficients of the three-dimensional tensor field, and :math:`A` is a linear mapping from tensor field space to measurement space.
:math:`D` is the measured data.
The tensor tomography problem then consists in finding an :math:`X` that approximately satisfies this equality, possibly subject to other constraints.
More generally, the equation may be written [Liebi2018]_

.. math ::
    P(A(X), \ldots) = D

In this case, :math:`P` is some kind of transfer function that creates an image from a field, and additional information may need to be provided, _e.g._, at which polarizations a visible light measurement was performed.

:term:`SAXSTT` is an example of a problem which can be written in the simpler linear form, and is currently the main method which is implemented in :program:`mumott`, solvable as a regularized minimization problem.
Here, :math:`A` is a mapping from a function on the unit sphere to the reciprocal space map measured on a detector, and :math:`D` contains scanning :term:`SAXS` measurements.
An example of a potential problem of somewhat greater complexity would be :term:`WAXS` (or x-ray diffraction) tensor tomography, where the projection would also need to take into account the effect of the scattering direction on the transmitted intensity from each point in three-dimensional space.
