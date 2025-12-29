.. _data_handling:

Data handling
=============

The :mod:`data_handling` module provides functionality for loading and inspecting data.
Instances (objects) of the class :class:`DataContainer <mumott.data_handling.DataContainer>` are created by loading data from file.
Afterwards one can access, e.g., the geometry via the :attr:`DataContainer.geometry <mumott.data_handling.DataContainer.geometry>` property, which is a :class:`Geometry <mumott.core.geometry.Geometry>` object.
The series of measurements (if available) is accessible via the :attr:`DataContainer.projections <mumott.data_handling.DataContainer.projections>` property, which is a :class:`ProjectionStack <mumott.core.projection_stack.ProjectionStack>` object.
The latter acts as a list of individual measurements, which are provided as :class:`Projection <mumott.core.projection_stack.Projection>` objects.
The :mod:`mumott.data_handling.utilities` module provides convenience function for the calculation of transmittivities and absorbances from diode data.

.. autoclass:: mumott.data_handling.DataContainer
   :members:

Utilities
---------
.. automodule:: mumott.data_handling.utilities
   :members:
