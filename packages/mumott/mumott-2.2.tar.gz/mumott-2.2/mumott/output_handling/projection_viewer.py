""" Container for the class ProjectionViewer. """

import logging
from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt
import colorcet  # noqa

from colorspacious import cspace_converter
from matplotlib import cm
from matplotlib.colors import Colormap
from matplotlib.gridspec import GridSpec
from numpy.typing import NDArray
from typing import Union, Tuple

from .orientation_image_mapper import OrientationImageMapper
from mumott.data_handling import DataContainer


@dataclass
class ProjectionImage:
    """
    A dataclass for storing images for instances of
    class:`ProjectionViewer <mumott.output_handling.ProjectionViewer>`.

    Attributes
    ----------
    mean
        The mean value of the data.
    std
        The standard deviation of the data.
    angle_color_quad
        A quadruplet of RGBA colors mapping phase angles
        that indicate the orientation of the image.
    """
    mean: NDArray[float]
    std: NDArray[float]
    angle_color_quad: NDArray[float]


class ProjectionViewer:
    """
    Class for viewing data and synthetic projections in a scrollable plot.
    The viewed projection can be changed with either the arrow keys or
    with the mouse scrolling wheel.

    Parameters
    ----------
    data_container : DataContainer
        A :class:`DataContainer
        <mumott.data_handling.data_container.DataContainer>` object, containing
        the necessary dimension and rotation information to show orientations correctly.
    data : numpy.ndarray(dtype=numpy.float64), optional
        A flat array of data from e.g. reconstruction output. If not given, data
        will be loaded from the provided ``data_container``. Provide if you e.g.
        want to look at synthetic projections from a reconstruction.
    orientation_symmetry : ``'longitudinal'``, ``'transversal'``, optional
        Specifies the assumed three-dimensional symmetry of the reciprocal
        space map, which determines whether the minimum or the maximum of the
        ``cos(phi) ** 2`` component of the of the intensity is interpreted as
        the orientation angle. The default is ``'longitudinal'``, which interprets the
        angle of maximum scattering as the orientation, corresponding to
        an assumed three-dimensional symmetry of polar caps of intensity.
        The other option is ``transversal``, which corresponds to a symmetry
        of a great circle of intensity (also known as fiber symmetry), corresponding
        to a phase shift of ``90`` degrees.
    mean_colormap : str or matplotlib.colors.Colormap
        Specifies the colormap of the mean intensity across all angles. The default
        is ``'cet_linear_bmy_10_95_c71'``, a linear high-contrast with blue, magenta
        and yellow.
    std_colormap : str or matplotlib.colors.Colormap
        Specifies the colormap of the standar deviation of the data across all angles.
        The default is ``'cet_gouldian'``, a linear high-contrast map with blue,
        green and yellow.
    phase_colormap : str or matplotlib.colors.Colormap
        Specifies the colormap of the phase of the ``cos(detector_angles) ** 2`` fit
        of the data. The default is ``'cet_CET_C10'``, an isoluminant cyclic map.
    mean_range : tuple(float, float)
        Specifies the range of the colormap of the mean.
    std_range : tuple(float, float)
        Specifies the range of the colormap of the standard deviation.
    """

    def __init__(self,
                 data_container: DataContainer,
                 data: NDArray[np.float64] = None,
                 orientation_symmetry: str = 'longitudinal',
                 mean_colormap: Union[str, Colormap] = 'cet_linear_bmy_10_95_c71',
                 std_colormap: Union[str, Colormap] = 'cet_gouldian',
                 phase_colormap: Union[str, Colormap] = 'cet_CET_C10',
                 mean_range: Tuple[float, float] = None,
                 std_range: Tuple[float, float] = None):
        detector_angles = data_container.geometry.detector_angles
        det_vector = \
            (np.cos(detector_angles[np.newaxis, :]) *
             data_container.geometry.detector_direction_origin[:, np.newaxis] +
             np.sin(detector_angles[np.newaxis, :]) *
             data_container.geometry.detector_direction_positive_90[:, np.newaxis])
        distance_j = np.dot(data_container.geometry.j_direction_0[np.newaxis, :],
                            det_vector).squeeze()
        distance_k = np.dot(data_container.geometry.k_direction_0[np.newaxis, :],
                            det_vector).squeeze()
        if not np.allclose(np.diff(detector_angles).reshape(1, -1),
                           np.diff(detector_angles).reshape(-1, 1),
                           rtol=2e-01, atol=8e-02):
            logging.warning('The provided `detector_angles` do not appear to be '
                            'sorted and equally spaced to within an absolute tolerance '
                            'of 5 degrees and a relative tolerance of twenty percent of the '
                            'segment width.'
                            '\nThe orientation angle may not behave as expected. Please be cautious'
                            'in interpreting the figure.')
        detector_angles = np.arctan2(distance_k, distance_j)
        if data is None:
            data = data_container.data
        if orientation_symmetry == 'transversal':
            detector_angles = np.arctan2(np.sin(detector_angles), np.cos(detector_angles))
        elif orientation_symmetry == 'longitudinal':
            detector_angles = np.arctan2(-np.cos(detector_angles), np.sin(detector_angles))
        else:
            logging.warning(
                    'Unknown `orientation_symmetry` option: "' + orientation_symmetry +
                    '"\nUsing default value: "longitudinal".\n'
                    'Valid options are "transversal" and "longitudinal".')
            detector_angles = np.arctan2(-np.cos(detector_angles), np.sin(detector_angles))
        direction = np.arctan2(np.sin(detector_angles[1] - detector_angles[0]),
                               np.cos(detector_angles[1] - detector_angles[0]))
        a = float(np.round(direction >= 0))
        b = np.exp((-2j) * detector_angles[0])
        self._mean_colormap = mean_colormap
        self._std_colormap = std_colormap
        self._phase_colormap = phase_colormap
        self._cielab_converter = cspace_converter('sRGB255', 'JCh')
        self._srgb_converter = cspace_converter('JCh', 'sRGB255')
        self._orientation_image_mapper = OrientationImageMapper(phase_colormap)
        self._wheel_properties = self._orientation_image_mapper.wheel_properties
        self._phase_colormap_lut = cm.get_cmap(self._phase_colormap, 256)
        self._projection_number = len(data)
        self._clims_mean = np.percentile(
            a=data.mean(axis=2),
            q=(1., 99.9))
        if mean_range is not None:
            if mean_range[0] is not None:
                self._clims_mean[0] = mean_range[0]
            if mean_range[1] is not None:
                self._clims_mean[1] = mean_range[1]
        self._clims_std = np.percentile(
            a=data.std(axis=2),
            q=(1., 99.9))
        if std_range is not None:
            if std_range[0] is not None:
                self._clims_std[0] = std_range[0]
            if std_range[1] is not None:
                self._clims_std[1] = std_range[1]
        self._projection_images = []
        for i, frame in enumerate(data):
            temp_mean = frame[:, :, :detector_angles.size].mean(axis=2).T
            temp_std = frame[:, :, :detector_angles.size].std(axis=2).T
            temp_fft = np.fft.rfft(frame[:, :, :detector_angles.size] ** 2, axis=2, norm='ortho')
            if a:
                temp_angle = (np.sqrt(temp_fft[:, :, 1] * b)).T
            else:
                temp_angle = (np.sqrt(np.conj(temp_fft[:, :, 1]) * b)).T
            temp_angle = np.angle(np.sign(temp_angle.imag) * temp_angle)
            temp_mask = np.round(
                np.sqrt(
                    abs(temp_fft[:, :, 0])) > 0.5 * np.sqrt(abs(temp_fft[:, :, 0])).mean()).astype(float).T
            temp_aniso_factor = np.sqrt(
                abs(temp_fft[:, :, 1]) / (np.finfo(float).tiny + abs(temp_fft[:, :, 0]))).T
            temp_shader = temp_aniso_factor.clip(0., 1)
            phase_rgba = self._phase_colormap_lut(temp_angle / np.pi)
            phase_cielab = self._cielab_converter(phase_rgba[:, :, :-1])
            phase_cielab[:, :, :2] *= 1.1 * ((1 - np.exp(-temp_shader)) /
                                             (1 - np.exp(-1))).reshape(temp_shader.shape + (1,))
            phase_rgba[:, :, :-1] = self._srgb_converter(phase_cielab).clip(0., 1.)
            phase_rgba[:, :, -1] = temp_mask
            temp_image = ProjectionImage(
                mean=temp_mean,
                std=temp_std,
                angle_color_quad=phase_rgba)
            self._projection_images.append(temp_image)
        self._fig = plt.figure()
        self._grid_spec = GridSpec(6, 9, figure=self._fig)
        self._axes = []
        self._axes.append(self._fig.add_subplot(self._grid_spec[0:4, 0:3]))
        self._axes.append(self._fig.add_subplot(self._grid_spec[0:4, 3:6]))
        self._axes.append(self._fig.add_subplot(self._grid_spec[0:4, 6:9]))
        self._axes.append(self._fig.add_subplot(self._grid_spec[4:6, 6:9], projection='polar'))
        self._colorbar_axes = []
        self._colorbar_axes.append(self._fig.add_subplot(self._grid_spec[5, 0:3]))
        self._colorbar_axes.append(self._fig.add_subplot(self._grid_spec[5, 3:6]))
        for a in self._axes:
            a.grid(False)
            a.set_yticks([])
            a.set_xticks([])
            a.set_yticklabels([])
            a.set_xticklabels([])
        self._im1 = self._axes[0].imshow(
            self._projection_images[0].mean, origin='lower', cmap=self._mean_colormap)
        self._axes[0].set_title('Mean')
        self._fig.colorbar(
            self._im1, cax=self._colorbar_axes[0], orientation='horizontal')
        self._im2 = self._axes[1].imshow(
            self._projection_images[0].std, origin='lower', cmap=self._std_colormap)
        self._axes[1].set_title('Standard deviation')
        self._fig.colorbar(self._im2, cax=self._colorbar_axes[1], orientation='horizontal')

        self._im3 = self._axes[2].imshow(self._projection_images[0].angle_color_quad,
                                         origin='lower',)
        self._axes[2].set_title('Orientation phase')
        self._axes[2].set_facecolor((254 / 255, 254 / 255, 254 / 255))
        self._wheel_rgba = self._wheel_properties[2]
        self._axes[3].set_facecolor((254 / 255, 254 / 255, 254 / 255))
        wheel_shader = self._wheel_properties[1][:-1, :-1] ** 2
        wheel_cielab = self._cielab_converter(self._wheel_rgba[:, :, :-1])
        wheel_cielab[:, :, :2] *= 1.1 * ((1 - np.exp(-wheel_shader)) /
                                         (1 - np.exp(-1))).reshape(wheel_shader.shape + (1,))
        wheel_rgb = self._srgb_converter(wheel_cielab).clip(0., 1.)
        self._wheel_rgba[:, :, :-1] = wheel_rgb
        self._axes[3].grid(False)
        self._color_wheel = self._axes[3].pcolormesh(self._wheel_properties[0],
                                                     1 - np.arccos(self._wheel_properties[1]) * 2 / np.pi,
                                                     wheel_shader[:, :],
                                                     facecolors=self._wheel_rgba.reshape(-1, 4),
                                                     edgecolors=self._wheel_rgba.reshape(-1, 4))
        self._axes[3].set_rmax(1.)
        self._axes[3].set_rmin(0.)
        self._projection_ind = 0

    def change_projection(self, ind: int) -> None:
        """
        Method for updating the projection shown
        when the projection slider changes.

        Parameters
        ----------
        ind
            The index of the projection to be shown.
        """
        if ind != self._projection_ind:
            self._projection_ind = ind
            ind = int(ind)
            self._im1.set_data(self._projection_images[ind].mean)
            self._im1.set_clim(*self._clims_mean)
            self._im2.set_data(self._projection_images[ind].std)
            self._im2.set_clim(*self._clims_std)
            self._im3.set_data(self._projection_images[ind].angle_color_quad)
            self._im3.autoscale()
            self._axes[0].relim()
            self._axes[1].relim()
            self._axes[2].relim()
            self._axes[0].autoscale_view()
            self._axes[1].autoscale_view()
            self._axes[2].autoscale_view()
            self._axes[0].set_aspect('equal')
            self._axes[1].set_aspect('equal')
            self._axes[2].set_aspect('equal')
            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events()
