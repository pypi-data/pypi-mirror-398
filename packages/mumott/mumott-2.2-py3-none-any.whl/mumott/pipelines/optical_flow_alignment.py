"""
Functions for subpixel alignment algorithm.
"""
import sys

import numpy as np
import scipy as sp
from scipy import ndimage
from tqdm import tqdm

from typing import Any

from mumott.data_handling import DataContainer
from mumott.data_handling.utilities import get_absorbances
from mumott.pipelines import run_mitra
from mumott.methods.projectors import SAXSProjectorCUDA, SAXSProjector
from mumott.pipelines.utilities import image_processing as imp
from mumott.pipelines.utilities.alignment_geometry import get_alignment_geometry


def _define_axis_index(rotation_axis_index: int) -> tuple[int, int]:
    """ Defines the indices of the geometrical x and y axes relative to the axes of the array,
    using the index of the main rotation axis, which by definition is the geometrical y axis.

    Parameters
    ----------
    rotation_axis_index
        The index of the main rotation axis in the projections.

    Returns
    -------
        A tuple comprising the indices of the geometrical x and y axes for the array.

    """

    # define the x and y axis, y being the rotation axis
    if rotation_axis_index == 0:
        x_axis_index = 1
        y_axis_index = 0
    else:
        x_axis_index = 0
        y_axis_index = 1
    return x_axis_index, y_axis_index


def run_optical_flow_alignment(
    data_container: DataContainer,
    **kwargs,
) -> tuple[np.ndarray[float], np.ndarray[float], np.ndarray[float]]:
    """This pipeline implements the alignment algorithm described in [Odstrcil2019]_
    The latter allows one to compute the shifts that are need to align the data
    according to the tomographical problem defined by the given geometry and projector.
    The alignment also relies on the related definition of the reconstruction volume
    and main axis of rotation ('y' axis).
    The procedure can be customized via the keyword arguments described under below (see Notes).

    Parameters
    ----------
    data_container
        Input data.
    volume : tuple[int, int, int]
        **Geometry parameter:**
        The size of the volume of the wanted tomogram.
        If not specified, deduced from information in :attr:`data_container`.
    main_rot_axis : int
        **Geometry parameter:**
        The index of the main rotation axis (``y`` axis on the real geometry) on the array.
        If not specified, deduced from information in :attr:`data_container`.
    smooth_data : bool
        **Data filtering:**
        If ``True`` apply Gaussian filter to smoothen the data; default: ``False``.
    sigma_smooth : float
        **Data filtering:**
        The smoothing kernel related to the overall data smoothing; default: ``0``.
    high_pass_filter : float
        **Data filtering:**
        The kernel for high pass filter in the gradient
        computation to avoid phase artifact; default: ``0.01``.
    optimal_shift : np.ndarray[float]
        **Shifts:**
        The original shift; default: ``np.zeros((nb_projections, 2))``.
    rec_iteration : int
        **Projector parameters:**
        The number of iteration used to solve the tomogram from the
        projections; default: ``20``.
    use_gpu : bool
        **Projector parameters:**
        Use GPU (``True``) or CPU (``False``) for the tomographic computation;
        default: ``False``.
    optimizer_kwargs : dict[str, Any]
        **Projector parameters:**
        Keyword arguments to pass on to the optimizer;
        default: ``dict(nestorov_weight = 0.6)``.
    stop_max_iteration : int
        **Alignment parameters:**
        The maximum iteration allowed to find the shifts for the alignment; default: ``20``.
    stop_min_correction : float
        **Alignment parameters:**
        The optimization is terminated if the correction (in pixel)
        drops below this value; default ``0.01``.
    align_horizontal : bool
        **Alignment parameters:**
        Apply the horizontal alignment procedure; default: ``True``.
    align_vertical : bool
        **Alignment parameters:**
        Apply the vertical alignment procedure; default: ``True``.
    center_reconstruction : bool
        **Alignment parameters:**
        Shift the reconstructed tomogram to the center of the volume
        to avoid drift in the alignment procedure; default: ``True``.

    Returns
    -------
        A tuple comprising the shifts used for aligning the, the resulting (and aligned) projections
        obtained by projecting the reconstructed tomogram based on the aligned data, and the
        resulting tomogram reconstructed using the aligned data.

    Example
    -------
    The alignment procedure is simple to use.

    >>> import numpy as np
    >>> from mumott.data_handling import DataContainer
    >>> from mumott.pipelines import optical_flow_alignment as ofa
    >>> data_container = DataContainer('tests/test_fbp_data.h5')

    We introduce some spurious offsets to this already-aligned data.

    >>> length = len(data_container.geometry)
    >>> data_container.geometry.j_offsets = np.arange(0., length) - length * 0.5
    >>> data_container.geometry.k_offsets = \
        np.cos(np.arange(0., length) * np.pi / length)

    We then perform the alignment with default parameters.

    >>> shifts, sinogram_corr, tomogram_corr = ofa.run_optical_flow_alignment(data_container)
    ...

    To use the alignment shifts, we have to translate them from the reconstruction
    ``(x, y, z)``-coordinates into the projection ``(p, j, k)`` coordinates.
    The function :func:`shifts_to_vector` transforms the shifts in projection space
    into shifts in 3D space based on the detector geometry.
    The function :func:`shifts_to_geometry` transforms the shifts vector from the detector reference
    frame to the sample reference frame.

    >>> j_offsets, k_offsets = ofa.shifts_to_geometry(data_container, shifts)
    >>> data_container.geometry.j_offsets = j_offsets
    >>> data_container.geometry.k_offsets = k_offsets

    We can configure a variety of parameters and pass those to the alignment pipeline.
    For example, we can choose whether to align in the horizontal or vertical directions,
    whether to center the reconstruction, initial guesses for the shifts,
    the number of iterations for the reconstruction,
    the number of iterations for the alignment procedure, and so on.

    A quick way to align very misaligned data is to use the :func:`line_vertical_alignment` function
    to obtain an initial guess.
    It can as well be used between alignment steps. Note that their is two version for the vertical
    It can also be used between alignment steps.
    There are two version for the vertical alignment.
    :func:`line_vertical_alignment` uses the :class:`DataContainer` geometry and data,
    while :func:`sinogram_line_vertical_alignment` is based on a sinogram and the geometry.
    Note that the more strongly the object deviates from axial symmetry,
    the worse the vertical line alignment will be.

    >>> initial_shift = ofa.line_vertical_alignment(data_container)

    >>> alignment_param = dict(
    ...    optimal_shift=initial_shift,
    ...    rec_iteration=10,
    ...    stop_max_iteration=3,
    ...    align_horizontal=True,
    ...    align_vertical=True,
    ...    center_reconstruction=True,
    ...    optimizer_kwargs=dict(nestorov_weight=0.6))
    >>> shifts, sinogram_corr, tomogram_corr = ofa.run_optical_flow_alignment(data_container,
    ...                                                                       **alignment_param)
    >>> vertical_shift, index = ofa.sinogram_line_vertical_alignment(
    ...    sinogram_corr, ofa.get_alignment_geometry(data_container)[0])
    >>> shifts[:,index] += vertical_shift # to update the shifts with vertical line alignment.
    """

    # deduce main rotation axis and associated volume from information in data container
    main_rot_axis_deduced, volume_deduced = get_alignment_geometry(data_container)

    # -- options

    nb_projections = np.size(data_container.diode, 0)

    # =========    geometry    ================
    # volume to reconstruct
    volume = kwargs.get('volume', volume_deduced)

    # main rotation axis
    main_rot_axis = kwargs.get('main_rot_axis', main_rot_axis_deduced)

    # =========    data filtering    ================
    # overall filtering
    smooth_data = kwargs.get('smooth_data', False)
    sigma_smooth = kwargs.get('sigma_smooth', 0)

    # phase artifact removal filtering
    high_pass_filter = kwargs.get('high_pass_filter', 0.01)

    # =========    original shift    ================
    optimal_shift = kwargs.get('optimal_shift', np.zeros((nb_projections, 2)))

    # =========    projector parameters    ================

    # number of iteration for the tomogram reconstruction
    rec_iteration = kwargs.get('rec_iteration', 20)

    # =========    alignment parameters    ================

    # stoppage criteria
    # maximum iteration possible
    max_iteration = kwargs.get('stop_max_iteration', 20)
    # stop iterate if the position is not corrected enough anymore
    min_correction = kwargs.get('stop_min_correction', 0.01)

    # alignment condition
    # horizontal and vertical algwinment
    align_horizontal = kwargs.get('align_horizontal', True)
    align_vertical = kwargs.get('align_vertical', True)

    # to avoid a full volume shift
    center_reconstruction = kwargs.get('center_reconstruction', True)

    # use the GPU for tomographic computation
    use_gpu = kwargs.get('use_gpu', False)

    # optimizer kwargs
    optimizer_kwargs = kwargs.get('optimizer_kwargs', dict(nestorov_weight=0.6))

    # add the max iter
    optimizer_kwargs.update({'maxiter': rec_iteration})

    # call the real function
    return _optical_flow_alignment_full_param(
        data_container,
        volume,
        main_rot_axis,
        smooth_data,
        sigma_smooth,
        high_pass_filter,
        optimal_shift,
        rec_iteration,
        max_iteration,
        min_correction,
        align_horizontal,
        align_vertical,
        center_reconstruction,
        use_gpu,
        optimizer_kwargs,
    )


def _optical_flow_alignment_full_param(
    data_container: DataContainer,
    volume: tuple[int, int, int],
    main_rot_axis: int,
    smooth_data: bool = False,
    sigma_smooth: float = 0.0,
    high_pass_filter: float = 0.01,
    optimal_shift: np.ndarray[float] = 0.0,
    rec_iteration: int = 20,
    max_iteration: int = 100,
    min_correction: float = 0.01,
    align_horizontal: bool = True,
    align_vertical: bool = True,
    center_reconstruction: bool = True,
    use_gpu: bool = False,
    optimizer_kwargs: dict[str, Any] = None,
):
    """ To compute the shifts nescessary to align the datas according to the tomographical
    problem defined by the geom and the projector given in arg.
    This will also rely on the related definition of the reconstruction volume and main axis of rotation
    ('y' axis), and a lot of alignment parameters.
    This function should not be called on itself, but through the wrapper optical_flow_alignment.

    Complete re-use and reformating of the code of Michal Odstrcil, 2016. Based on [Odstrcil2019]_

    Parameters
    ----------
    data_container
        Input data.
    volume
        The size of the volume of the wanted tomogram.
    main_rot_axis
        The index of the main rotation axis ('y' axis on the real geometry) on the array.
    smooth_data
        To smooth the data by gaussian filter.
    sigma_smooth
        The smoothing kernel related to the overall data smoothing.
    high_pass_filter
        The kernel for high pass filter in the gradient computation, to avoid phase artifact.
    optimal_shift
        The original shift.
    rec_iteration
        The number of iteration used to solve the tomogram from the projections.
    max_iteration
        The maximum iteration allowed to find the shifts for the alignment.
    min_correction
        The minimum of correction (in pixel) needed for each iteration to not stop the iterative procedure.
    align_horizontal
        Apply the horizontal alignment procedure.
    align_vertical
        Apply the horizontal vertical procedure.
    center_reconstruction
        Recenter the reconstructed tomogram at the center of the volume to avoid drift in the
        alignment procedure.
    use_gpu
        Use GPU or CPU for the tomographic computation.
    optimizer_kwargs
        kwargs for the optimizer, for the run pipeline.

    Returns
    -------
    shift
        np.ndarray[float].
        The shifts nescessary to align the data.
    sinogram_corr
        A tuple comprising the shifts used for aligning the, the resulting (and aligned) projections
        obtained by projecting the reconstructed tomogram based on the aligned data, and the
        resulting tomogram reconstructed using the aligned data.
    """

    # define the x and y axis, y being the rotation axis
    x_axis_index, y_axis_index = _define_axis_index(main_rot_axis)

    # get absorbance for the sino
    abs_dict = get_absorbances(data_container.diode, normalize_per_projection=True)
    absorbances = abs_dict['absorbances']
    sinogram_0 = np.moveaxis(np.squeeze(absorbances), 0, -1)

    # reference diodes
    diodes_ref = np.moveaxis(np.squeeze(data_container.diode), 0, -1)

    # define sinogram sizes
    nb_projections = np.size(sinogram_0, -1)
    # the volume is a parallepipede with square base
    nb_layers = data_container.diode.shape[main_rot_axis + 1]
    width = data_container.diode.shape[np.mod(main_rot_axis + 1, 2) + 1]

    # -- pre processing

    # if data is smoothened, smooth sinogram_0 via Gaussian filter
    if smooth_data:
        sinogram_0 = sp.ndimage.gaussian_filter(sinogram_0, sigma_smooth)
    sinogram_0 = imp.smooth_edges(sinogram_0)

    # Tukey window, necessary for the grad computation, to avoid edges issues
    W = imp.compute_tukey_window(width, nb_layers)
    if x_axis_index == 0:
        W = W.transpose(1, 0, 2)

    # -- configuration for the loop
    iteration = 0
    max_step = 1 + min_correction
    shifts = np.zeros((max_iteration + 1, nb_projections, 2))

    # shift initial tomogram with a guessed shift
    shifts[0, :, :] = optimal_shift

    # shift in geometry to 0, since it is done by sinogram shift
    # data_container.geometry.j_offsets = optimal_shift[:, 0] * 0
    # data_container.geometry.k_offsets = optimal_shift[:, 1] * 0

    # visual feedback of the progression
    pbar = tqdm(total=max_iteration, desc='Alignment iterations', file=sys.stdout)

    while True:

        # compute the shifts and the related tomogram and corrected sinograms
        max_step, sinogram_corr, tomogram, shifts = compute_shifts(
            sinogram_0,
            diodes_ref,
            shifts,
            data_container,
            iteration,
            x_axis_index,
            y_axis_index,
            rec_iteration,
            high_pass_filter,
            W,
            align_horizontal,
            align_vertical,
            center_reconstruction,
            use_gpu,
            optimizer_kwargs,
        )

        pbar.update(1)
        # if the step size is too small stop optimization
        if max_step <= min_correction:
            print(
                'The largest change ({max_step})'
                ' has dropped below the stopping criterion ({min_correction})'
                ' The alignment is complete.',
            )
            break
        if iteration + 1 >= max_iteration:
            break
        else:
            iteration = iteration + 1
    pbar.close()

    shift = shifts[iteration + 1, :, :]
    return shift, np.moveaxis(sinogram_corr, 0, -1), tomogram


def recenter_tomogram(
    tomogram: np.ndarray[float],
    step: float = 0.2,
    **kwargs: dict[str, Any],
):
    """ Recenter a tomogram in frame.

    Parameters
    ----------
    tomogram
        The tomogram to shift.
    step
        The step for the recentering, should be smaller than one. Default is 0.2

    Returns
    -------
        The shifted tomogram, recentered in frame.

    """
    # remove the extra dimension for this calculation
    tomo_2 = np.squeeze(np.copy(tomogram))

    # the volume is a parallelepiped with square base
    axis = 0
    volume = tomo_2.shape
    if volume[0] == volume[1]:
        axis = 2
    elif volume[0] == volume[2]:
        axis = 1
    axis = kwargs.get('axis ', axis)

    # the 2 first dimensions must be the transverse slices of the tomogram, i.e., have the same dimension
    tomo_2 = np.moveaxis(tomo_2, axis, -1)

    # try to keep reconstruction in center
    # enforce positivity
    pos_tomo_2 = np.copy(tomo_2)
    pos_tomo_2[pos_tomo_2 < 0] = 0
    x, y, mass = imp.center(np.sqrt(pos_tomo_2))  # x is here first axis, y second axis
    # more robust estimation of the center
    # remove nan
    ind_x = np.argwhere(~np.isnan(x))
    ind_y = np.argwhere(~np.isnan(y))

    x = (
        np.mean(x[ind_x] * mass[ind_x] ** 2)
        / np.mean(mass[ind_x] ** 2 + np.finfo(float).eps)
        * np.ones(x.shape)
    )
    y = (
        np.mean(y[ind_y] * mass[ind_y] ** 2)
        / np.mean(mass[ind_y] ** 2 + np.finfo(float).eps)
        * np.ones(y.shape)
    )
    # shift (slowly) the tomogram to the new center
    # here, x is the first axis, y the second axis, same reference for imshift_fft function
    tomo_2 = imp.imshift_fft(
        tomo_2, -x * step, -y * step
    )  # go slowly, using only one fifth of the shift
    # put back the right order
    tomo_2 = np.moveaxis(tomo_2, -1, axis)

    tomogram[:, :, :, 0] = tomo_2

    return tomogram


def compute_shifts(
    sinogram_0: np.ndarray[float],
    diodes_ref: np.ndarray[float],
    shifts,
    data_container: DataContainer,
    iteration: int,
    x_axis_index: int,
    y_axis_index: int,
    rec_iteration: int,
    high_pass_filter: float,
    W: np.ndarray[float],
    align_horizontal: bool,
    align_vertical: bool,
    center_reconstruction: bool,
    use_gpu: bool,
    optimizer_kwargs: dict[str, Any],
) -> tuple[float, np.ndarray[float], np.ndarray[float], np.ndarray[float]]:
    """ Compute the shifts to align the reference sinogram and the synthetized sinogram.

    Parameters
    ----------
    sinogram_0
        The absorbance of the data to align.
    diodes_ref
        The data to align.
    data_container
        The data container.
    iteration
        The current iteration.
    shifts
        Current shifts.
    x_axis_index
        The index in the array of the geometrical X axis (tilt axis).
    y_axis_index
        The index in the array of the geometrical Y axis (main rotation axis).
    rec_iteration
        The number of iteration used to solve the tomogram from the projections.
    high_pass_filter
        The kernel for high pass filter in the gradient computation
        applied to avoid phase artifact.
    W
        The Tukey window associated with our computation.
    align_horizontal
        Apply the horizontal alignment procedure.
    align_vertical
        Apply the vertical alignment procedure.
    center_reconstruction
        Shift the reconstructed tomogram to the center of the volume to avoid drift in the
        alignment procedure.
    use_gpu
        Use GPU (``True``) or CPU (``False``) for the tomographic computation.

    Returns
    -------
        Tuple comprising the maximum update in this iteration,
        the resulting aligned projections found by projecting
        the reconstructed tomogram using the aligned data,
        the resulting tomogram reconstructed by the aligned data, and
        the updated shifts.
    """

    nb_projections = np.size(sinogram_0, -1)

    # shift the original sinogram_0 by the new value
    sinogram_shifted = imp.imshift_fft(
        np.copy(sinogram_0), shifts[iteration, :, 0], shifts[iteration, :, 1])
    # shift the original diodes
    diodes_shifted = imp.imshift_fft(diodes_ref, shifts[iteration, :, 0], shifts[iteration, :, 1])

    # update the shifts for SIRT / MITRA
    for ii in range(data_container.projections.diode.shape[0]):
        data_container.projections[ii].diode = diodes_shifted[..., ii]

    # reconstruct the tomogram with the given geometry, shifts, and data
    tomogram = run_mitra(
        data_container,
        use_gpu=use_gpu,
        maxiter=rec_iteration,
        ftol=None,
        enforce_non_negativity=True,
        optimizer_kwargs=optimizer_kwargs,
    )['result']['x']

    if center_reconstruction and (iteration < 20):
        tomogram = recenter_tomogram(tomogram)
        # positivity constraint
        tomogram[tomogram < 0] = 0

    # compute the projected data from the reconstructed tomogram: sinogram_corr
    if use_gpu:
        projector = SAXSProjectorCUDA(data_container.geometry)
    else:
        projector = SAXSProjector(data_container.geometry)
    sinogram_corr = projector.forward(tomogram)
    # remove extra dimension of the sinogram
    sinogram_corr = np.squeeze(sinogram_corr)

    # find the optimal shift
    shift_hor, shift_vect = compute_shift_through_sinogram(
        sinogram_shifted,
        np.moveaxis(sinogram_corr, 0, -1),
        x_axis_index,
        y_axis_index,
        high_pass_filter,
        W,
        align_horizontal,
        align_vertical,
    )

    # store the values on the right axis
    shift_vector = np.zeros((1, nb_projections, 2))
    shift_vector[:, :, x_axis_index] = shift_hor
    shift_vector[:, :, y_axis_index] = shift_vect

    # apply the optical flow correction method
    step_relaxation = 0.5  # small relaxation is needed to avoid oscilations
    shifts[iteration + 1, :, :] = shifts[iteration, :, :] + shift_vector * step_relaxation
    # remove degree of freedom in the vertical dimension (avoid drifts)
    shifts[iteration + 1, :, y_axis_index] = shifts[iteration + 1, :, y_axis_index] - np.median(
        shifts[iteration + 1, :, y_axis_index]
    )

    max_step = np.maximum(np.max(np.abs(shift_hor)), np.max(np.abs(shift_vect)))

    # put back original data
    for ii in range(data_container.projections.diode.shape[0]):
        data_container.projections[ii].diode = diodes_ref[..., ii]

    return max_step, sinogram_corr, tomogram, shifts


def compute_shift_through_sinogram(
    sinogram_shifted: np.ndarray[float],
    sinogram_corr: np.ndarray[float],
    x_axis_index: int,
    y_axis_index: int,
    high_pass_filter: float,
    W: np.ndarray[float],
    align_horizontal: bool,
    align_vertical: bool,
) -> tuple[np.ndarray[float], np.ndarray[float]]:
    """ Compute the shift needed to obtain a better sinogram, based on actual shifted
sinogram and the sythetic sinogram.

    Parameters
    ----------
    sinogram_shifted
        The sinogram, aka data, to compute the shift correction on.
    sinogram_corr
        The sythetic sinogram obtain after reconstruction on the tomogram obtain from the
        sinogram_shifted and reprojecting it.
    W
        The Tukey window associated with our computation.
    x_axis_index
        The index in the array of the geometrical X axis (tilt axis).
    y_axis_index
        The index in the array of the geometrical Y axis (main rotation axis).
    high_pass_filter
        The kernel for high pass filter in the gradient computation, to avoid phase artifact.
    align_horizontal
        Compute the horizontal alignment shift.
    align_vertical
        Compute the horizontal vertical shift.

    Returns
    -------
        A tuple comprising the horizontal and vertical shifts.
    """

    nb_projections = np.size(sinogram_shifted, -1)

    # find the optimal shift
    d_vect = np.zeros(sinogram_corr.shape)
    d_hor = np.zeros(sinogram_corr.shape)
    for index in range(nb_projections):
        d_hor[..., index], d_vect[..., index] = imp.get_img_grad(
            imp.smooth_edges(sinogram_corr)[..., index], x_axis_index, y_axis_index
        )
    DS = sinogram_corr - sinogram_shifted

    # apply high pass filter => get rid of phase artefacts
    DS = imp.imfilter_high_pass_1d(DS, x_axis_index, high_pass_filter)

    # align horizontal
    if align_horizontal:
        # calculate optimal shift of the 2D projections in horiz direction
        d_hor = imp.imfilter_high_pass_1d(d_hor, x_axis_index, high_pass_filter).real
        shift_hor = -(
            np.sum(W * d_hor * DS, axis=(0, 1)) / np.sum(W * d_hor ** 2 + np.finfo(float).eps, axis=(0, 1))
        )
        # do not allow more than 1px shift per iteration !
        shift_hor = np.minimum(np.ones(shift_hor.shape), np.abs(shift_hor)) * np.sign(shift_hor)
    else:
        # if disable
        shift_hor = np.zeros((1, nb_projections))

    # align vertical
    if align_vertical:
        # calculate optimal shift of the 2D projections in vert direction
        d_vect = imp.imfilter_high_pass_1d(d_vect, x_axis_index, high_pass_filter).real
        shift_vect = -(
            np.sum(W * d_vect * DS, axis=(0, 1)) / np.sum(W * d_vect ** 2 + np.finfo(float).eps, axis=(0, 1))
        )

        shift_vect = shift_vect - np.mean(shift_vect)
        # do not allow more than 1px shift per iteration !
        shift_vect = np.minimum(np.ones(shift_vect.shape), np.abs(shift_vect)) * np.sign(shift_vect)
    else:
        # if disable
        shift_vect = np.zeros((1, nb_projections))

    return shift_hor, shift_vect


def sinogram_line_vertical_alignment(
    sinogram: np.ndarray[float],
    main_rot_axis: int,
    threshold: float = 0
) -> tuple[np.ndarray[float], float]:

    """
    Compute the vertical, i.e., transverse, weight on a given sinogram and
    align it by aligning the center of mass.
    This yields only a very rough alignment but it is very efficient if the misalignment is large.
    It can be used as the initial step in an alignment procedure or between different steps of the alignment.

    Parameters
    ----------
    sinogram
        The sinogram to align, as a stack of 2D arrays.
    main_rot_axis
        The index of the vertical axis on the given sinogram. It is the
        axis perpendicular to the rotation axis ``// y_axis_index``.
    threshold
        Maximum value to take into account for the weighting.

    Returns
    -------
        Computed shifts in the vertical direction.
    """

    horizontal_axis = main_rot_axis
    # defining the horizontal axis as the one not vertical
    vertical_axis = 0 if horizontal_axis == 1 else 1

    im = np.copy(sinogram)
    # select the center of the sinogram to have only a 2D array left
    if vertical_axis == 0:
        im = im[:, round(sinogram.shape[1] / 2), :]
    else:
        im = im[round(sinogram.shape[0] / 2), :, :]

    center_vect = np.zeros(im.shape[-1])

    # threshold value to avoid outliers to influence the alignment too much
    if threshold > 0:
        im[im > threshold] = threshold

    # compute the weights and positions of each vertical line of the sinogram
    for ii in range(im.shape[-1]):
        center_vect[ii] = ndimage.center_of_mass(im[:, ii])[0]

    # we want all vertical center of mass to be aligned with the global center of mass
    center_vect = -(center_vect - np.mean(center_vect))

    return center_vect, vertical_axis


def line_vertical_alignment(
    data_container: DataContainer,
    threshold: float = 0,
    **kwargs
) -> np.ndarray[float]:

    """
    Compute the vertical, i.e. transverse weight on the sinogram of a given DataContainer and
    align it by aligning the center of mass.
    It is a very rough alignment but very efficient for large misalignment. It can be used
    as initialisation of an alignment procedure or between different steps of the alignment.

    Parameters
    ----------
    data_container
        The DataContainer with the absorption data to align.
    threshold
        Maximum value to take into account for the weighting.
    main_rot_axis : int
        Geometry parameter.
        The index of the main rotation axis (``y`` axis on the real geometry) of the array.
        If not specified, deduced from information in :attr:`data_container`.

    Returns
    -------
        Computed shifts in the vertical direction.
    """
    # deduce main rotation axis and associated volume from information in data container
    main_rot_axis_deduced, _ = get_alignment_geometry(data_container)

    # main rotation axis
    main_rot_axis = kwargs.get('main_rot_axis', main_rot_axis_deduced)

    # get absorbance for the sinogram
    abs_dict = get_absorbances(data_container.diode, normalize_per_projection=True)
    absorbances = abs_dict['absorbances']
    sinogram_0 = np.moveaxis(np.squeeze(absorbances), 0, -1)
    print(sinogram_0.shape)

    vertical_shift, vertical_axis = sinogram_line_vertical_alignment(sinogram_0, main_rot_axis)

    # realign sinogram that was shifted originally
    shift_all = np.zeros((sinogram_0.shape[-1], 2))
    shift_all[:, vertical_axis] = vertical_shift

    return shift_all


def shifts_to_vector(
    shifts: np.ndarray[float],
    data_container: DataContainer,
    **kwargs,
) -> np.ndarray[float]:
    """
    This function expresses the detector-referenced shifts in a 3D Cartesian coordinate
    system based on the detector frame and the inner and outer axes of the geometry.

    Parameters
    ----------
    shifts
        The shifts expressed in the detector frame.
    data_container
        The data container containing the geometry information.
    main_rot_axis : int
        Geometry parameter.
        The index of the main rotation axis (``y`` axis on the real geometry) of the array.
        If not specified, deduced from information in :attr:`data_container`.

    Returns
    -------
    vector_shifts in 3D coordinates system based on the detector given geometry.
    """

    # deduce main rotation axis and associated volume from information in data container
    main_rot_axis_deduced, _ = get_alignment_geometry(data_container)

    # main rotation axis
    main_rot_axis = kwargs.get('main_rot_axis', main_rot_axis_deduced)

    other_axis = 0 if main_rot_axis == 1 else 1

    vector_shifts = np.array(
        [(
            shifts[i, main_rot_axis] * g.inner_axis +
            shifts[i, other_axis] * g.outer_axis
         )
         for i, g in enumerate(data_container.geometry)]
    )

    return vector_shifts


def shifts_to_geometry(
    data_container: DataContainer,
    shifts: np.ndarray[float],
) -> tuple[np.ndarray[float], np.ndarray[float]]:
    """
    This function expresses the detector-referenced shifts in a 3D Cartesian coordinate
    system based on the object coordinate system, i.e., the ``j`` and ``k``-directions.

    Parameters
    ----------
    data_container
        The data container containing the geometry information connected to the data.
    shifts
        The shifts expressed in the detector frame.

    Returns
    -------
        Two tuples for the shifts in the j and k directions.
    """

    # computing the shifts in detector space from the projection shifts
    vector_shifts = shifts_to_vector(shifts, data_container)

    j_offsets = np.sum(vector_shifts * data_container.geometry.j_direction_0[np.newaxis], axis=1)
    k_offsets = np.sum(vector_shifts * data_container.geometry.k_direction_0[np.newaxis], axis=1)

    return j_offsets, k_offsets
