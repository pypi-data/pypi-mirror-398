.. _projectors:

Projectors
==========

:program:`mumott` provides two different implementations of projectors suitable for :term:`SAXS` tomography.
While they should yield nearly equivalent results, they differ with respect to the resources they require.

:class:`SAXSProjectorCUDA <mumott.methods.projectors.SAXSProjectorCUDA>` and :class:`SAXSProjector <mumott.methods.projectors.SAXSProjector>` implement an equivalent algorithm for GPU and CPU resources, respectively.

.. autoclass:: mumott.methods.projectors.SAXSProjector
   :members:
   :inherited-members:

.. autoclass:: mumott.methods.projectors.SAXSProjectorCUDA
   :members:
   :inherited-members:
