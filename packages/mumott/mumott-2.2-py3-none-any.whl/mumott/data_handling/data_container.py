import logging

import h5py as h5
import numpy as np
import os

from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from mumott.core.deprecation_warning import print_deprecation_warning
from mumott.core.geometry import Geometry
from mumott.core.projection_stack import ProjectionStack, Projection

logger = logging.getLogger(__name__)

# used to easily keep track of preferred keys
_preferred_keys = dict(rotations='inner_angle',
                       tilts='outer_angle',
                       offset_j='j_offset',
                       offset_k='k_offset',
                       rot_mat='rotation_matrix')


def _deprecated_key_warning(deprecated_key: str):
    """Internal method for deprecation warnings of keys."""
    if deprecated_key in _preferred_keys:
        # Only print once.
        preferred_key = _preferred_keys.pop(deprecated_key)
        print_deprecation_warning(
            f'Entry name {deprecated_key} is deprecated. Use {preferred_key} instead.')


class DataContainer:

    """
    Instances of this class represent data read from an input file in a format suitable for further analysis.
    The two core components are :attr:`geometry` and :attr:`projections`.
    The latter comprises a list of :class:`Projection <mumott.core.projection_stack.Projection>`
    instances, each of which corresponds to a single measurement.

    By default all data is read, which can be rather time consuming and unnecessary in some cases,
    e.g., when aligning data.
    In those cases, one can skip loading the actual measurements by setting :attr:`skip_data` to ``True``.
    The geometry information and supplementary information such as the diode data will still be read.

    Example
    -------
    The following code snippet illustrates the basic use of the :class:`DataContainer` class.

    First we create a :class:`DataContainer` instance, providing the path to the data file to be read.

    >>> from mumott.data_handling import DataContainer
    >>> dc = DataContainer('tests/test_full_circle.h5')

    One can then print a short summary of the content of the :class:`DataContainer` instance.

    >>> print(dc)
    ==========================================================================
                                  DataContainer
    --------------------------------------------------------------------------
    Corrected for transmission : False
    ...

    To access individual measurements we can use the :attr:`projections` attribute.
    The latter behaves like a list, where the elements of the list are
    :class:`Projection <mumott.core.projection_stack.Projection>` objects,
    each of which represents an individual measurement.
    We can print a summary of the content of the first projection.

    >>> print(dc.projections[0])
    --------------------------------------------------------------------------
                                    Projection
    --------------------------------------------------------------------------
    hash_data          : 3f0ba8
    hash_diode         : 808328
    hash_weights       : 088d39
    rotation           : [1. 0. 0.], [ 0. -1.  0.], [ 0.  0. -1.]
    j_offset           : 0.0
    k_offset           : 0.3
    inner_angle        : None
    outer_angle        : None
    inner_axis         : 0.0, 0.0, -1.0
    outer_axis         : 1.0, 0.0, 0.0
    --------------------------------------------------------------------------


    Parameters
    ----------
    data_path : str, optional
        Path of the data file relative to the directory of execution.
        If None, a data container with an empty :attr:`projections`
        attached will be initialized.
    data_type : str, optional
        The type (or format) of the data file. Supported values are
        ``h5`` (default) for hdf5 format and ``None`` for an empty ``DataContainer``
        that can be manually populated.
    skip_data : bool, optional
        If ``True``, will skip data from individual measurements when loading the file.
        This will result in a functioning :attr:`geometry` instance as well as
        :attr:`diode` and :attr:`weights` entries in each projection, but
        :attr:`data` will be empty.
    nonfinite_replacement_value : float, optional
        Value to replace nonfinite values (``np.nan``, ``np.inf``, and ``-np.inf``)  with in the
        data, diode, and weights. If ``None`` (default), an error is raised
        if any nonfinite values are present in these input fields.
    """
    def __init__(self,
                 data_path: str = None,
                 data_type: str = 'h5',
                 skip_data: bool = False,
                 nonfinite_replacement_value: float = None):
        self._correct_for_transmission_called = False
        self._projections = ProjectionStack()
        self._geometry_dictionary = dict()
        self._skip_data = skip_data
        self._nonfinite_replacement_value = nonfinite_replacement_value
        if data_path is not None:
            if data_type == 'h5':
                self._h5_to_projections(data_path)
            else:
                raise ValueError(f'Unknown data_type: {data_type} for'
                                 ' load_only_geometry=False.')

    def _h5_to_projections(self, file_path: str):
        """
        Internal method for loading data from hdf5 file.
        """
        h5_data = h5.File(file_path, 'r')
        projections = h5_data['projections']
        number_of_projections = len(projections)
        max_shape = (0, 0)
        inner_axis = np.array((0., 0., -1.))
        outer_axis = np.array((1., 0., 0.))
        found_inner_in_base = False
        found_outer_in_base = False
        if 'inner_axis' in h5_data:
            inner_axis = h5_data['inner_axis'][:]
            logger.info('Inner axis found in dataset base directory. This will override the default.')
            found_inner_in_base = True
        if 'outer_axis' in h5_data:
            outer_axis = h5_data['outer_axis'][:]
            logger.info('Outer axis found in dataset base directory. This will override the default.')
            found_outer_in_base = True

        for i in range(number_of_projections):
            p = projections[f'{i}']
            if 'diode' in p:
                max_shape = np.max((max_shape, p['diode'].shape), axis=0)
        for i in range(number_of_projections):
            p = projections[f'{i}']
            if 'diode' in p:
                diode = np.ascontiguousarray(np.copy(p['diode']).astype(np.float64))
                pad_sequence = np.array(((0, max_shape[0] - diode.shape[0]),
                                         (0, max_shape[1] - diode.shape[1]),
                                         (0, 0)))
                diode = np.pad(diode, pad_sequence[:-1])
            elif 'data' in p:
                diode = None
                pad_sequence = np.array(((0, max_shape[0] - p['data'].shape[0]),
                                         (0, max_shape[1] - p['data'].shape[1]),
                                         (0, 0)))
            else:
                pad_sequence = np.zeros((3, 2))
            if not self._skip_data:
                data = np.ascontiguousarray(np.copy(p['data']).astype(np.float64))
                data = np.pad(data, pad_sequence)
                if 'weights' in p:
                    weights = np.ascontiguousarray(np.copy(p['weights']).astype(np.float64))
                    if weights.ndim == 2 or (weights.ndim == 3 and weights.shape[-1] == 1):
                        weights = weights.reshape(weights.shape[:2])
                        weights = weights[..., np.newaxis] * \
                            np.ones((1, 1, data.shape[-1])).astype(np.float64)
                    weights = np.pad(weights, pad_sequence)
                else:
                    weights = np.ones_like(data)
            else:
                data = None
                if 'weights' in p:
                    weights = np.ascontiguousarray(np.copy(p['weights']).astype(np.float64))
                    weights = np.pad(weights, pad_sequence[:weights.ndim])
                else:
                    if diode is None:
                        weights = None
                    else:
                        weights = np.ones_like(diode)
                        weights = np.pad(weights, pad_sequence[:weights.ndim])
            # Look for rotation information and load if available
            if 'inner_axis' in p:
                p_inner_axis = p['inner_axis'][:]
                if found_inner_in_base:
                    logger.info(f'Inner axis found in projection {i}. This will override '
                                'the value found in the base directory for all projections '
                                'where it is found.')
                    found_inner_in_base = False
                # override default only if projection zero
                elif i == 0:
                    logger.info(f'Inner axis found in projection {i}. This will override '
                                'the default value for all projections, if they do not specify '
                                'another axis.')
                    inner_axis = p_inner_axis
            else:
                p_inner_axis = inner_axis
            if 'outer_axis' in p:
                p_outer_axis = p['outer_axis'][:]
                if found_outer_in_base:
                    logger.info(f'Outer axis found in projection {i}. This will override '
                                'the value found in the base directory for all projections '
                                'where it is found.')
                    found_outer_in_base = False
                elif i == 0:
                    logger.info(f'Inner axis found in projection {i}. This will override '
                                'the default value for all projections, if they do not specify '
                                'another axis.')
                    outer_axis = p_outer_axis
            else:
                p_outer_axis = outer_axis

            inner_angle = None
            outer_angle = None

            if 'inner_angle' in p:
                inner_angle = np.copy(p['inner_angle'][...]).flatten()[0]
                # if at least one angle exists, assume other is 0 by default.
                if outer_angle is None:
                    outer_angle = 0
            elif 'rotations' in p:
                inner_angle = np.copy(p['rotations'][...]).flatten()[0]
                _deprecated_key_warning('rotations')
                if outer_angle is None:
                    outer_angle = 0
            if 'outer_angle' in p:
                outer_angle = np.copy(p['outer_angle'][...]).flatten()[0]
                if inner_angle is None:
                    inner_angle = 0
            elif 'tilts' in p:
                outer_angle = np.copy(p['tilts'][...]).flatten()[0]
                _deprecated_key_warning('tilts')
                if inner_angle is None:
                    inner_angle = 0

            if 'rotation_matrix' in p:
                rotation = p['rotation_matrix'][...]
                if i == 0:
                    logger.info('Rotation matrices were loaded from the input file.')
            elif 'rot_mat' in p:
                rotation = p['rot_mat'][...]
                _deprecated_key_warning('rot_mat')
                if i == 0:
                    logger.info('Rotation matrices were loaded from the input file.')
            elif outer_angle is not None:
                R_inner = Rotation.from_rotvec(inner_angle * p_inner_axis).as_matrix()
                R_outer = Rotation.from_rotvec(outer_angle * p_outer_axis).as_matrix()
                rotation = R_outer @ R_inner
                if i == 0:
                    logger.info('Rotation matrix generated from inner and outer angles,'
                                ' along with inner and outer rotation axis vectors.'
                                ' Rotation and tilt angles assumed to be in radians.')
            else:
                rotation = np.eye(3)
                if i == 0:
                    logger.info('No rotation information found.')

            # default to 0-dim array to simplify subsequent code
            j_offset = np.array(0)
            if 'j_offset' in p:
                j_offset = p['j_offset'][...]
            elif 'offset_j' in p:
                j_offset = p['offset_j'][...]
                _deprecated_key_warning('offset_j')
            # offset will be either numpy/size-0 or size-1 array, ravel and extract.
            j_offset = j_offset.ravel()[0]
            j_offset -= pad_sequence[0, 1] * 0.5

            k_offset = np.array(0)
            if 'k_offset' in p:
                k_offset = p['k_offset'][...]
            elif 'offset_k' in p:
                k_offset = p['offset_k'][...]
                _deprecated_key_warning('offset_k')
            k_offset = k_offset.ravel()[0]
            k_offset -= pad_sequence[1, 1] * 0.5

            if not self._skip_data:
                self._handle_nonfinite_values(data)
            self._handle_nonfinite_values(weights)
            self._handle_nonfinite_values(diode)

            projection = Projection(data=data,
                                    diode=diode,
                                    weights=weights,
                                    rotation=rotation,
                                    j_offset=j_offset,
                                    k_offset=k_offset,
                                    outer_angle=outer_angle,
                                    inner_angle=inner_angle,
                                    inner_axis=p_inner_axis,
                                    outer_axis=p_outer_axis
                                    )
            self._projections.append(projection)
        if not self._skip_data:
            self._projections.geometry.detector_angles = np.copy(h5_data['detector_angles'])
            self._estimate_angular_coverage(self._projections.geometry.detector_angles)
        if 'volume_shape' in h5_data.keys():
            self._projections.geometry.volume_shape = np.copy(h5_data['volume_shape']).astype(int)
        else:
            self._projections.geometry.volume_shape = np.array(max_shape)[[0, 0, 1]]
        # Load sample geometry information
        if 'p_direction_0' in h5_data.keys():  # TODO check for orthogonality, normality
            self._projections.geometry.p_direction_0 = np.copy(h5_data['p_direction_0'][...])
            self._projections.geometry.j_direction_0 = np.copy(h5_data['j_direction_0'][...])
            self._projections.geometry.k_direction_0 = np.copy(h5_data['k_direction_0'][...])
            logger.info('Sample geometry loaded from file.')
        else:
            logger.info('No sample geometry information was found. Default mumott geometry assumed.')

        # Load detector geometry information
        if 'detector_direction_origin' in h5_data.keys():  # TODO check for orthogonality, normality
            self._projections.geometry.detector_direction_origin = np.copy(
                h5_data['detector_direction_origin'][...])
            self._projections.geometry.detector_direction_positive_90 = np.copy(
                h5_data['detector_direction_positive_90'][...])
            logger.info('Detector geometry loaded from file.')
        else:
            logger.info('No detector geometry information was found. Default mumott geometry assumed.')

        # Load scattering angle
        if 'two_theta' in h5_data:
            self._projections.geometry.two_theta = np.array(h5_data['two_theta'])
            logger.info('Scattering angle loaded from data.')

    def write(self, filename: str) -> None:
        """
        Save data and geometry information to a mumott .h5 file.

        Parameters
        ----------
        filename
            Path of the data file.

        Raises
        ------
        ValueError
            If the file name does not end on ".h5".
        """

        extension = os.path.splitext(filename)[-1]
        if not extension.lower() in ('.h5', ''):
            raise ValueError('Only .h5 files supported. Data was not saved.')
        if extension == '':
            filename = filename + '.h5'

        # Alias for line-length limit
        g = self.geometry

        # Build file
        with h5.File(filename, 'w') as file:

            # Assign global parameters
            file.create_dataset('detector_angles', data=g.detector_angles)
            file.create_dataset('volume_shape', data=g.volume_shape)

            file.create_dataset('p_direction_0', data=g.p_direction_0)
            file.create_dataset('j_direction_0', data=g.j_direction_0)
            file.create_dataset('k_direction_0', data=g.k_direction_0)

            file.create_dataset('detector_direction_origin', data=g.detector_direction_origin)
            file.create_dataset('detector_direction_positive_90', data=g.detector_direction_positive_90)

            # Make data group
            grp = file.create_group('projections')

            # Loop through projections
            for ii, (projection, geom_tpl) in enumerate(zip(self.projections, g)):

                # Make a group for each projection
                subgrp = grp.create_group(str(ii))

                # Prpjection data
                subgrp.create_dataset('data', data=projection.data)
                subgrp.create_dataset('diode', data=projection.diode)
                subgrp.create_dataset('weights', data=projection.weights)
                subgrp.create_dataset('j_offset', data=geom_tpl.j_offset)
                subgrp.create_dataset('k_offset', data=geom_tpl.k_offset)
                subgrp.create_dataset('rotation_matrix', data=geom_tpl.rotation)

                subgrp.create_dataset('inner_axis', data=geom_tpl.inner_axis)
                subgrp.create_dataset('inner_angle', data=geom_tpl.inner_angle)
                subgrp.create_dataset('outer_axis', data=geom_tpl.outer_axis)
                subgrp.create_dataset('outer_angle', data=geom_tpl.outer_angle)

    def _estimate_angular_coverage(self, detector_angles: list):
        """Check if full circle appears covered in data or not."""
        delta = np.abs(detector_angles[0] - detector_angles[-1] % (2 * np.pi))
        if abs(delta - np.pi) < min(delta, abs(delta - 2 * np.pi)):
            self.geometry.full_circle_covered = False
        else:
            logger.warning('The detector angles appear to cover a full circle. This '
                           'is only expected for WAXS data.')
            self.geometry.full_circle_covered = True

    def _handle_nonfinite_values(self, array):
        """ Internal convenience function for handling nonfinite values. """
        if np.any(~np.isfinite(array)):
            if self._nonfinite_replacement_value is not None:
                np.nan_to_num(array, copy=False, nan=self._nonfinite_replacement_value,
                              posinf=self._nonfinite_replacement_value,
                              neginf=self._nonfinite_replacement_value)
            else:
                raise ValueError('Nonfinite values detected in input, which is not permitted by default. '
                                 'To permit and replace nonfinite values, please set '
                                 'nonfinite_replacement_value to desired value.')

    def __len__(self) -> int:
        """
        Length of the :attr:`projections <mumott.data_handling.projection_stack.ProjectionStack>`
        attached to this :class:`DataContainer` instance.
        """
        return len(self._projections)

    def append(self, f: Projection) -> None:
        """
        Appends a :class:`Projection <mumott.core.projection_stack.Projection>`
        to the :attr:`projections` attached to this :class:`DataContainer` instance.
        """
        self._projections.append(f)

    @property
    def projections(self) -> ProjectionStack:
        """ The projections, containing data and geometry. """
        return self._projections

    @property
    def geometry(self) -> Geometry:
        """ Container of geometry information. """
        return self._projections.geometry

    @property
    def data(self) -> NDArray[np.float64]:
        """
        The data in the :attr:`projections` object
        attached to this :class:`DataContainer` instance.
        """
        return self._projections.data

    @property
    def diode(self) -> NDArray[np.float64]:
        """
        The diode data in the :attr:`projections` object
        attached to this :class:`DataContainer` instance.
        """
        return self._projections.diode

    @property
    def weights(self) -> NDArray[np.float64]:
        """
        The weights in the :attr:`projections` object
        attached to this :class:`DataContainer` instance.
        """
        return self._projections.weights

    def correct_for_transmission(self) -> None:
        """
        Applies correction from the input provided in the :attr:`diode
        <mumott.core.projection_stack.Projection.diode>` field.  Should
        only be used if this correction has *not* been applied yet.
        """
        if self._correct_for_transmission_called:
            logger.info(
                'DataContainer.correct_for_transmission() has been called already.'
                ' The correction has been applied previously, and the repeat call is ignored.')
            return

        data = self._projections.data / self._projections.diode[..., np.newaxis]

        for i, f in enumerate(self._projections):
            f.data = data[i]
        self._correct_for_transmission_called = True

    def _Rx(self, angle: float) -> NDArray[float]:
        """ Generate a rotation matrix for rotations around
        the x-axis, following the convention that vectors
        have components ordered ``(x, y, z)``.

        Parameters
        ----------
        angle
            The angle of the rotation.

        Returns
        -------
        R
            The rotation matrix.

        Notes
        -----
        For a vector ``v`` with shape ``(..., 3)`` and a rotation angle :attr:`angle`,
        ``np.einsum('ji, ...i', _Rx(angle), v)`` rotates the vector around the
        ``x``-axis by :attr:`angle`. If the
        coordinate system is being rotated, then
        ``np.einsum('ij, ...i', _Rx(angle), v)`` gives the vector in the
        new coordinate system.
        """
        return Rotation.from_euler('X', angle).as_matrix()

    def _Ry(self, angle: float) -> NDArray[float]:
        """ Generate a rotation matrix for rotations around
        the y-axis, following the convention that vectors
        have components ordered ``(x, y, z)``.

        Parameters
        ----------
        angle
            The angle of the rotation.

        Returns
        -------
        R
            The rotation matrix.

        Notes
        -----
        For a vector ``v`` with shape ``(..., 3)`` and a rotation angle ``angle``,
        ``np.einsum('ji, ...i', _Ry(angle), v)`` rotates the vector around the
        For a vector ``v`` with shape ``(..., 3)`` and a rotation angle :attr:`angle`,
        ``np.einsum('ji, ...i', _Ry(angle), v)`` rotates the vector around the
        ``y``-axis by :attr:`angle`. If the
        coordinate system is being rotated, then
        ``np.einsum('ij, ...i', _Ry(angle), v)`` gives the vector in the
        new coordinate system.
        """
        return Rotation.from_euler('Y', angle).as_matrix()

    def _Rz(self, angle: float) -> NDArray[float]:
        """ Generate a rotation matrix for rotations around
        the z-axis, following the convention that vectors
        have components ordered ``(x, y, z)``.

        Parameters
        ----------
        angle
            The angle of the rotation.

        Returns
        -------
        R
            The rotation matrix.

        Notes
        -----
        For a vector ``v`` with shape ``(..., 3)`` and a rotation angle :attr:`angle`,
        ``np.einsum('ji, ...i', _Rz(angle), v)`` rotates the vector around the
        ``z``-axis by :attr:`angle`. If the
        coordinate system is being rotated, then
        ``np.einsum('ij, ...i', _Rz(angle), v)`` gives the vector in the
        new coordinate system.
        """
        return Rotation.from_euler('Z', angle).as_matrix()

    def _get_str_representation(self, max_lines=50) -> str:
        """ Retrieves a string representation of the object with specified
        maximum number of lines.

        Parameters
        ----------
        max_lines
            The maximum number of lines to return.
        """
        wdt = 74
        s = []
        s += ['=' * wdt]
        s += ['DataContainer'.center(wdt)]
        s += ['-' * wdt]
        s += ['{:26} : {}'.format('Corrected for transmission', self._correct_for_transmission_called)]
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
        truncated_s += ['=' * wdt]
        return '\n'.join(truncated_s)

    def __str__(self) -> str:
        return self._get_str_representation()

    def _get_html_representation(self, max_lines=25) -> str:
        """ Retrieves an html representation of the object with specified
        maximum number of lines.

        Parameters
        ----------
        max_lines
            The maximum number of lines to return.
        """
        s = []
        s += ['<h3>DataContainer</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th></tr></thead>']
        s += ['<tbody>']
        s += ['<tr><td style="text-align: left;">Number of projections</td>']
        s += [f'<td>{len(self._projections)}</td></tr>']
        s += ['<tr><td style="text-align: left;">Corrected for transmission</td>']
        s += [f'<td>{self._correct_for_transmission_called}</td></tr>']
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
