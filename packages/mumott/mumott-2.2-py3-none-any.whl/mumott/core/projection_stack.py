""" Container for class ProjectionStack. """
import numpy as np
from numpy.typing import NDArray
from .geometry import Geometry, GeometryTuple
from mumott.core.hashing import list_to_hash


class Projection:
    """Instances of this class contain data and metadata from a single measurement.
    Typically they are appended to a
    :class:`ProjectionStack <mumott.core.projection_stack.ProjectionStack>` object.

    Parameters
    ----------
    data
        Data from measurement, structured into 3 dimensions representing
        the two scanning directions and the detector angle.
    diode
        Diode or transmission data from measurement, structured into
        2 dimensions representing the two scanning directions.
    weights
        Weights or masking information, represented as a number
        between ``0`` and ``1``. ``0`` means mask, ``1`` means
        do not mask. Structured the same way as :attr:`data`.
    rotation
        3-by-3 rotation matrix, representing the rotation of the sample in the
        laboratory coordinate system.
    j_offset
        The offset needed to align the projection in the j-direction.
    k_offset
        The offset needed to align the projection in the k-direction.
    inner_angle
        Angle of rotation about :attr:`inner_axis` in radians.
    outer_angle
        Angle of rotation about :attr:`outer_axis` in radians.
    inner_axis
        Inner rotation axis.
    outer_axis
        Outer rotation axis.
    """
    def __init__(self,
                 data: NDArray[float] = None,
                 diode: NDArray[float] = None,
                 weights: NDArray[float] = None,
                 rotation: NDArray[float] = np.eye(3, dtype=float),
                 j_offset: float = float(0),
                 k_offset: float = float(0),
                 inner_angle: float = None,
                 outer_angle: float = None,
                 inner_axis: NDArray[float] = None,
                 outer_axis: NDArray[float] = None):
        self._key = None
        self._projection_stack = None
        self.data = data
        self.diode = diode
        self.weights = weights
        self.j_offset = j_offset
        self.k_offset = k_offset
        self.rotation = rotation
        self.inner_angle = inner_angle
        self.outer_angle = outer_angle
        self.inner_axis = inner_axis
        self.outer_axis = outer_axis

    @property
    def j_offset(self) -> np.float64:
        """ The offset needed to align the projection in the j-direction."""
        if self._projection_stack is None:
            return self._j_offset
        else:
            k = self._projection_stack.index_by_key(self._key)
            return self._projection_stack.geometry.j_offsets[k]

    @j_offset.setter
    def j_offset(self, value) -> None:
        self._j_offset = value
        if self._projection_stack is not None:
            k = self._projection_stack.index_by_key(self._key)
            self._projection_stack.geometry.j_offsets[k] = value

    @property
    def k_offset(self) -> np.float64:
        """ The offset needed to align the projection in the k-direction."""
        if self._projection_stack is None:
            return self._k_offset
        else:
            k = self._projection_stack.index_by_key(self._key)
            return self._projection_stack.geometry.k_offsets[k]

    @k_offset.setter
    def k_offset(self, value) -> None:
        self._k_offset = value
        if self._projection_stack is not None:
            k = self._projection_stack.index_by_key(self._key)
            self._projection_stack.geometry.k_offsets[k] = value

    @property
    def rotation(self) -> NDArray[np.float64]:
        """ 3-by-3 rotation matrix, representing the rotation of the sample in the
        laboratory coordinate system. """
        if self._projection_stack is None:
            return self._rotation
        else:
            k = self._projection_stack.index_by_key(self._key)
            return self._projection_stack.geometry.rotations[k]

    @rotation.setter
    def rotation(self, value) -> None:
        self._rotation = value
        if self._projection_stack is not None:
            k = self._projection_stack.index_by_key(self._key)
            self._projection_stack.geometry.rotations[k] = value

    @property
    def inner_angle(self) -> float:
        """ Rotation angle about inner axis. """
        if self._projection_stack is None:
            return self._inner_angle
        else:
            k = self._projection_stack.index_by_key(self._key)
            return self._projection_stack.geometry.inner_angles[k]

    @inner_angle.setter
    def inner_angle(self, value: float) -> None:
        self._inner_angle = value
        if self._projection_stack is not None:
            k = self._projection_stack.index_by_key(self._key)
            self._projection_stack.geometry.inner_angles[k] = value

    @property
    def outer_angle(self) -> float:
        """ Rotation angle about inner axis. """
        if self._projection_stack is None:
            return self._outer_angle
        else:
            k = self._projection_stack.index_by_key(self._key)
            return self._projection_stack.geometry.outer_angles[k]

    @outer_angle.setter
    def outer_angle(self, value: float) -> None:
        self._outer_angle = value
        if self._projection_stack is not None:
            k = self._projection_stack.index_by_key(self._key)
            self._projection_stack.geometry.outer_angles[k] = value

    @property
    def inner_axis(self) -> NDArray[float]:
        """ Rotation angle about inner axis. """
        if self._projection_stack is None:
            return self._inner_axis
        else:
            k = self._projection_stack.index_by_key(self._key)
            return self._projection_stack.geometry.inner_axes[k]

    @inner_axis.setter
    def inner_axis(self, value: NDArray[float]) -> None:
        self._inner_axis = value
        if self._projection_stack is not None:
            k = self._projection_stack.index_by_key(self._key)
            self._projection_stack.geometry.inner_axes[k] = value

    @property
    def outer_axis(self) -> NDArray[float]:
        """ Rotation angle about inner axis. """
        if self._projection_stack is None:
            return self._outer_axis
        else:
            k = self._projection_stack.index_by_key(self._key)
            return self._projection_stack.geometry.outer_axes[k]

    @outer_axis.setter
    def outer_axis(self, value: NDArray[float]) -> None:
        self._outer_axis = value
        if self._projection_stack is not None:
            k = self._projection_stack.index_by_key(self._key)
            self._projection_stack.geometry.outer_axes[k] = value

    @property
    def data(self) -> NDArray:
        """ Scattering data, structured ``(j, k, w)``, where ``j`` is the pixel in the j-direction,
        ``k`` is the pixel in the k-direction, and ``w`` is the detector segment.
        Before the reconstruction, the data should be normalized by the diode.
        This may already have been done prior to loading the data.
        """
        return np.array([]).reshape(0, 0) if self._data is None else self._data

    @data.setter
    def data(self, val) -> None:
        self._data = val

    @property
    def diode(self) -> NDArray[np.float64]:
        """ The diode readout, used to normalize the data. Can be blank if data is already normalized.
        """
        return np.array([]).reshape(0, 0) if self._diode is None else self._diode

    @diode.setter
    def diode(self, val) -> None:
        self._diode = val

    @property
    def weights(self) -> NDArray:
        """ Weights to be applied multiplicatively during optimization. A value of ``0``
        means mask, a value of ``1`` means no weighting, and other values means weighting
        each data point either less (``weights < 1``) or more (``weights > 1``) than a weight of ``1``.
        """
        return np.array([]).reshape(0, 0) if self._weights is None else self._weights

    @weights.setter
    def weights(self, val) -> None:
        self._weights = val

    @property
    def attached(self):
        """ Returns true if projection is attached to a :class:`ProjectionStack <ProjectionStack>` object. """
        return self._projection_stack is not None

    def attach_to_stack(self, projection_stack, index):
        """ Used to attach the projection to a projection_stack.
        *This method should not be called by users.*
        """
        if self.attached:
            raise ValueError('This projection is already attached to a projection_stack')
        self._projection_stack = projection_stack
        self._key = index

    @property
    def geometry(self) -> GeometryTuple:
        """ Returns geometry information as a named tuple. """
        return GeometryTuple(rotation=self.rotation,
                             j_offset=self.j_offset,
                             k_offset=self.k_offset,
                             inner_angle=self.inner_angle,
                             outer_angle=self.outer_angle,
                             inner_axis=self.inner_axis,
                             outer_axis=self.outer_axis)

    @geometry.setter
    def geometry(self, value: GeometryTuple) -> None:
        self.rotation = value.rotation
        self.j_offset = value.j_offset
        self.k_offset = value.k_offset
        self.inner_angle = value.inner_angle
        self.outer_angle = value.outer_angle
        self.inner_axis = value.inner_axis
        self.outer_axis = value.outer_axis

    def detach_from_stack(self):
        """ Used to detach the projection from a projection stack.
        *This method should not be called by users.*
        """
        k = self._projection_stack.index_by_key(self._key)
        g = self._projection_stack.geometry[k]
        self._rotation = g.rotation
        self._j_offset = g.j_offset
        self._k_offset = g.k_offset
        self._inner_angle = g.inner_angle
        self._outer_angle = g.outer_angle
        self._inner_axis = g.inner_axis
        self._outer_axis = g.outer_axis
        self._projection_stack = None
        self._key = None

    @property
    def hash_data(self) -> str:
        """ A hash of :attr:`data`."""
        # np.array wrapper in case data is None
        return list_to_hash([np.array(self.data)])

    @property
    def hash_diode(self) -> str:
        """ A sha1 hash of :attr:`diode`."""
        return list_to_hash([np.array(self.diode)])

    @property
    def hash_weights(self) -> str:
        """ A sha1 hash of :attr:`weights`."""
        return list_to_hash([np.array(self.weights)])

    def __str__(self) -> str:
        wdt = 74
        s = []
        s += ['-' * wdt]
        s += ['Projection'.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, precision=5, linewidth=60, edgeitems=2):
            s += ['{:18} : {}'.format('hash_data', self.hash_data[:6])]
            s += ['{:18} : {}'.format('hash_diode', self.hash_diode[:6])]
            s += ['{:18} : {}'.format('hash_weights', self.hash_weights[:6])]
            ss = ', '.join([f'{r}' for r in self.rotation])
            s += ['{:18} : {}'.format('rotation', ss)]
            s += ['{:18} : {}'.format('j_offset', self.j_offset)]
            s += ['{:18} : {}'.format('k_offset', self.k_offset)]
            s += ['{:18} : {}'.format('inner_angle', self.inner_angle)]
            s += ['{:18} : {}'.format('outer_angle', self.outer_angle)]
            ss = ', '.join([f'{r}' for r in np.array(self.inner_axis).ravel()])
            s += ['{:18} : {}'.format('inner_axis', ss)]
            ss = ', '.join([f'{r}' for r in np.array(self.outer_axis).ravel()])
            s += ['{:18} : {}'.format('outer_axis', ss)]
        s += ['-' * wdt]
        return '\n'.join(s)

    def _repr_html_(self) -> str:
        s = []
        s += ['<h3>Projection</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th><th>Data</th></tr></thead>']
        s += ['<tbody>']
        with np.printoptions(threshold=4, precision=5, linewidth=40, edgeitems=2):
            s += ['<tr><td style="text-align: left;">data</td>']
            s += [f'<td>{self.data.shape}</td><td>{self.hash_data[:6]} (hash)</td></tr>']
            s += [f'<tr><td style="text-align: left;">diode</td>'
                  f'<td>{self.diode.shape}</td>']
            s += [f'<td>{self.hash_diode[:6]} (hash)</td></tr>']
            s += [f'<tr><td style="text-align: left;">weights</td>'
                  f'<td>{self.weights.shape}</td>']
            s += [f'<td>{self.hash_weights[:6]} (hash)</td></tr>']
            s += [f'<tr><td style="text-align: left;">rotation</td><td>{self.rotation.shape}</td>']
            s += [f'<td>{self.rotation}</td></tr>']
            s += ['<tr><td style="text-align: left;">j_offset</td><td>1</td>']
            s += [f'<td>{self.j_offset}</td></tr>']
            s += ['<tr><td style="text-align: left;">k_offset</td><td>1</td>']
            s += [f'<td>{self.k_offset}</td></tr>']
            s += ['<tr><td style="text-align: left;">inner_angle</td><td>1</td>']
            s += [f'<td>{self.inner_angle}</td>']
            s += ['<tr><td style="text-align: left;">outer_angle</td><td>1</td>']
            s += [f'<td>{self.outer_angle}</td>']
            s += [f'<tr><td style="text-align: left;">inner_axis</td><td>{self.inner_axis.shape}</td>']
            s += [f'<td>{self.inner_axis}</td></tr>']
            s += [f'<tr><td style="text-align: left;">outer_axis</td><td>{self.outer_axis.shape}</td>']
            s += [f'<td>{self.outer_axis}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)


class ProjectionStack:
    """Instances of this class contain data, geometry and other pertinent information
    for a series of measurements.
    The individual measurements are stored as
    :class:`Projection <mumott.core.projection_stack.Projection>` objects.
    The latter are accessible via list-like operations, which enables, for example, iteration over
    measurements but also retrieval of individual measurements by index, in-place modification or deletion.

    The geometry information (i.e., rotations and offsets for each projection)
    is accessible via the :attr:`geometry` attribute.
    Data, diode readouts, and weights can be retrieved as contiguous arrays
    via the properties :attr:`data`, :attr:`diode`, and :attr:`weights`, respectively.

    Example
    -------
    The following code snippet illustrates how individual measurements can be accessed via list operations.
    For demonstration, here, we use default ("empty") projections.
    In practice the individual measurements are read from a data file via the
    :class:`DataContainer <mumott.data_handling.DataContainer>` class, which makes
    them available via the
    :attr:`DataContainer.projections <mumott.data_handling.DataContainer.projections>` attribute.

    First we create an empty projection stack.

    >>> from mumott.core.projection_stack import Projection, ProjectionStack
    >>> projection_stack = ProjectionStack()

    Next we create a projection and attach it to the projection stack.
    In order to be able to distinguish this projection during this example,
    we assign it a :attr:`Projection.j_offset` of ``0.5``.

    >>> projection = Projection(j_offset=0.5)
    >>> projection_stack.append(projection)

    The geometry information can now be accessed via the projection stack
    in several different but equivalent ways, including via the original projection object,

    >>> print(projection.j_offset)

    via indexing `projection_stack`

    >>> print(projection_stack[0].geometry.j_offset)

    or by indexing the respective geometry property of the projection stack itself.

    >>> print(projection_stack.geometry.j_offsets[0])

    We can modify the geometry parameters via any of these properties with identical outcome.
    For example,

    >>> projection_stack[0].j_offset = -0.2
    >>> print(projection.j_offset,
              projection_stack[0].geometry.j_offset,
              projection_stack.geometry.j_offsets[0])
    -0.2 -0.2 -0.2

    Next consider a situation where several projections are included in the projection stack.

    >>> projection_stack.append(Projection(j_offset=0.1))
    >>> projection_stack.append(Projection(j_offset=-0.34))
    >>> projection_stack.append(Projection(j_offset=0.23))
    >>> projection_stack.append(Projection(j_offset=0.78))
    >>> print(projection_stack.geometry.j_offsets)
    [-0.2, 0.1, -0.34, 0.23, 0.78]

    The summary of the projection stack includes hashes for the data, the diode readout, and the weights.
    This allows one to get a quick indication for whether the content of these fields has changed.

    >>> print(projection_stack)
    --------------------------------------------------------------------------
                                      ProjectionStack
    --------------------------------------------------------------------------
    hash_data          : ...

    We could, for example, decide to remove an individual projection as we might
    have realized that the data from that measurement was corrupted.

    >>> del projection_stack[1]
    >>> print(projection_stack)
    --------------------------------------------------------------------------
                                      ProjectionStack
    --------------------------------------------------------------------------
    hash_data          : ...

    From the output it is readily apparent that the content of the data field
    has changed as a result of this operation.

    Finally, note that we can also loop over the projection stack, for example, to print the projections.

    >>> for projection in projection_stack:
    >>>     print(projection)
    ...
    """

    def __init__(self) -> None:
        self._projections = []
        self._keys = []
        self._geometry = Geometry()

    def __delitem__(self, k: int) -> None:
        """ Removes a projection from the projection_stack. """
        if abs(k) > len(self) - int(k >= 0):
            raise IndexError(f'Index {k} is out of bounds for ProjectionStack of length {len(self)}.')
        self._projections[k].detach_from_stack()
        del self._projections[k]
        del self._geometry[k]
        del self._keys[k]

    def append(self, projection: Projection) -> None:
        """
        Appends a measurement in the form of a
        :class:`Projection <mumott.core.projection_stack.Projection>` object.
        Once a projection is attached to a projection_stack, the geometry information of the
        projection will be synchronized
        with the geometry information of the projection_stack (see :attr:`geometry`).

        Parameters
        ----------
        projection
            :class:`Projection <mumott.core.projection_stack.Projection>` object to be appended.
        """
        if projection.attached:
            raise ValueError('The projection is already attached to a projection stack')
        assert len(self._projections) == len(self._geometry)
        if len(self) == 0:
            self._geometry.projection_shape = np.array(projection.diode.shape)
        elif not np.allclose(self.diode.shape[1:], projection.diode.shape):
            raise ValueError('Appended projection diode must have the same shape as other projections,'
                             f' but its shape is {projection.diode.shape} while other projections'
                             f' have shape {self.diode.shape[1:]}.')
        self._projections.append(projection)
        self._geometry.append(GeometryTuple(rotation=projection.rotation,
                                            j_offset=projection.j_offset,
                                            k_offset=projection.k_offset,
                                            inner_angle=projection.inner_angle,
                                            outer_angle=projection.outer_angle,
                                            inner_axis=projection.inner_axis,
                                            outer_axis=projection.outer_axis))

        projection_key = hash(projection)
        self._keys.append(projection_key)
        projection.attach_to_stack(self, projection_key)

    def __setitem__(self, k: int, projection: Projection) -> None:
        """
        This allows each projection of the projection stack to be safely modified.
        """
        assert len(self._projections) == len(self._geometry)
        if abs(k) > len(self) - int(k >= 0):
            raise IndexError(f'Index {k} is out of bounds for projection stack of length {len(self)}.')

        if projection.attached:
            raise ValueError('The projection is already attached to a projection stack')
        if not np.allclose(self.diode.shape[1:], projection.diode.shape):
            raise ValueError('New projection diode must have the same shape as other projections,'
                             f' but its shape is {projection.diode.shape} while other projections'
                             f' have shape {self.diode.shape[1:]}.')

        # detach and delete previous projection
        del self[k]

        # attach new projection
        self._projections.insert(k, projection)
        self._geometry.insert(k, GeometryTuple(rotation=projection.rotation,
                                               j_offset=projection.j_offset,
                                               k_offset=projection.k_offset,
                                               inner_angle=projection.inner_angle,
                                               outer_angle=projection.outer_angle,
                                               inner_axis=projection.inner_axis,
                                               outer_axis=projection.outer_axis))

        projection_key = hash(projection)
        self._keys.insert(k, projection_key)
        projection.attach_to_stack(self, projection_key)

    def insert(self, k: int, projection: Projection) -> None:
        """ Inserts a projection at a particular index, increasing the indices
        of all subsequent projections by 1. """
        assert len(self._projections) == len(self._geometry)
        if abs(k) > len(self) - int(k >= 0):
            raise IndexError(f'Index {k} is out of bounds for projection stack of length {len(self)}.')

        if projection.attached:
            raise ValueError('The projection is already attached to a projection stack.')
        if not np.allclose(self.diode.shape[1:], projection.diode.shape):
            raise ValueError('Inserted projection diode must have the same shape as other projections,'
                             f' but its shape is {projection.diode.shape} while other projections'
                             f' have shape {self.diode.shape[1:]}.')

        self._projections.insert(k, projection)
        self._geometry.insert(k, GeometryTuple(rotation=projection.rotation,
                                               j_offset=projection.j_offset,
                                               k_offset=projection.k_offset))
        self._geometry.projection_shape = np.array(projection.diode.shape)
        projection_key = hash(projection)
        self._keys.insert(k, projection_key)
        projection.attach_to_stack(self, projection_key)

    def __getitem__(self, k: int) -> Projection:
        """
        This allows indexing of and iteration over the projection stack.
        """
        assert len(self._projections) == len(self._geometry)
        if abs(k) > len(self) - round(float(k >= 0)):
            raise IndexError(f'Index {k} is out of bounds for projection stack of length {len(self)}.')
        return self._projections[k]

    def __len__(self) -> int:
        return len(self._projections)

    @property
    def data(self) -> NDArray:
        """ Scattering data, structured ``(n, j, k, w)``, where ``n`` is the projection number,
        ``j`` is the pixel in the j-direction, ``k`` is the pixel in the k-direction,
        and ``w`` is the detector segment. Before the reconstruction, this should
        be normalized by the diode. This may already have been done prior to loading the data.
        """
        if len(self) == 0:
            return np.array([]).reshape(0, 0, 0)
        return np.stack([f.data for f in self._projections], axis=0)

    @property
    def diode(self) -> NDArray:
        """ The diode readout, used to normalize the data. Can be blank if data is already normalized.
        The diode value should not be normalized per projection, i.e., it is distinct from the
        transmission value used in standard tomography."""
        if len(self) == 0:
            return np.array([]).reshape(0, 0, 0)
        return np.stack([f.diode for f in self._projections], axis=0)

    @diode.setter
    def diode(self, val) -> None:
        assert len(self) == len(val)
        for i, projection in enumerate(self._projections):
            projection.diode[...] = val[i]

    @property
    def weights(self) -> NDArray:
        """ Weights applied multiplicatively during optimization. A value of ``0``
        means mask, a value of ``1`` means no weighting, and other values means weighting
        each data point either less (``weights < 1``) or more (``weights > 1``) than a weight of ``1``.
        """
        if len(self) == 0:
            return np.array([]).reshape(0, 0, 0)
        return np.stack([f.weights for f in self._projections], axis=0)

    @weights.setter
    def weights(self, val) -> None:
        assert len(self) == len(val)
        for i, projection in enumerate(self._projections):
            projection.weights[...] = val[i]

    def _get_str_representation(self, max_lines: int = 25) -> str:
        """ Retrieves a string representation of the object with the specified
        maximum number of lines.

        Parameters
        ----------
        max_lines
            The maximum number of lines to return.
        """
        s = []
        wdt = 74
        s = []
        s += ['-' * wdt]
        s += ['ProjectionStack'.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=3, edgeitems=1, precision=3, linewidth=60):
            s += ['{:18} : {}'.format('hash_data', self.hash_data[:6])]
            s += ['{:18} : {}'.format('hash_diode', self.hash_diode[:6])]
            s += ['{:18} : {}'.format('hash_weights', self.hash_weights[:6])]
            s += ['{:18} : {}'.format('Number of projections', len(self))]
            s += ['{:18} : {}'.format('Number of pixels j', self.diode.shape[1])]
            s += ['{:18} : {}'.format('Number of pixels k', self.diode.shape[2])]
        truncated_s = []
        leave_loop = False
        while not leave_loop:
            line = s.pop(0).split('\n')
            for split_line in line:
                if split_line != '':
                    truncated_s += [split_line]
                if len(truncated_s) > max_lines - 2:
                    if split_line != '...':
                        truncated_s += ['...']
                    if split_line != ('=' * wdt):
                        truncated_s += ['=' * wdt]
                    leave_loop = True
                    break
            if len(s) == 0:
                leave_loop = True
        truncated_s += ['-' * wdt]
        return '\n'.join(truncated_s)

    def __str__(self) -> str:
        return self._get_str_representation()

    @property
    def hash_data(self) -> str:
        """ A hash of :attr:`data`."""
        # np.array wrapper in case data is None
        return list_to_hash([np.array(self.data)])

    @property
    def hash_diode(self) -> str:
        """ A sha1 hash of :attr:`diode`."""
        return list_to_hash([np.array(self.diode)])

    @property
    def hash_weights(self) -> str:
        """ A sha1 hash of :attr:`weights`."""
        return list_to_hash([np.array(self.weights)])

    def _get_html_representation(self, max_lines: int = 25) -> str:
        """ Retrieves an html representation of the object with the specified
        maximum number of lines.

        Parameters
        ----------
        max_lines
            The maximum number of lines to return.
        """
        s = []
        s += ['<h3>ProjectionStack</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th><th>Data</th></tr></thead>']
        s += ['<tbody>']
        with np.printoptions(threshold=3, edgeitems=1, precision=2, linewidth=40):
            s += ['<tr><td style="text-align: left;">data</td>']
            s += [f'<td>{self.data.shape}</td><td>{self.hash_data[:6]} (hash)</td></tr>']
            s += ['<tr><td style="text-align: left;">diode</td>']
            s += [f'<td>{self.diode.shape}</td><td>{self.hash_diode[:6]} (hash)</td></tr>']
            s += ['<tr><td style="text-align: left;">weights</td>']
            s += [f'<td>{self.weights.shape}</td><td>{self.hash_weights[:6]} (hash)</td></tr>']
            s += ['<tr><td style="text-align: left;">Number of pixels j</td>']
            s += ['<td>1</td>']
            s += [f'<td>{self.diode.shape[1]}</td></tr>']
            s += ['<tr><td style="text-align: left;">Number of pixels k</td>']
            s += ['<td>1</td>']
            s += [f'<td>{self.diode.shape[2]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        truncated_s = []
        line_count = 0
        leave_loop = False
        while not leave_loop:
            line = s.pop(0).split('\n')
            for split_line in line:
                truncated_s += [split_line]
                if '</tr>' in split_line:
                    line_count += 1
                    # Catch if last line had ellipses
                    last_tr = split_line
                if line_count > max_lines - 1:
                    if last_tr != '<tr><td style="text-align: left;">...</td></tr>':
                        truncated_s += ['<tr><td style="text-align: left;">...</td></tr>']
                    truncated_s += ['</tbody>']
                    truncated_s += ['</table>']
                    leave_loop = True
                    break
            if len(s) == 0:
                leave_loop = True
        return '\n'.join(truncated_s)

    def _repr_html_(self) -> str:
        return self._get_html_representation()

    @property
    def geometry(self) -> Geometry:
        """ Contains geometry information for each projection as well
        as information about the geometry of the whole system. """
        return self._geometry

    def index_by_key(self, key):
        """ Returns an index from a key. """
        return self._keys.index(key)
