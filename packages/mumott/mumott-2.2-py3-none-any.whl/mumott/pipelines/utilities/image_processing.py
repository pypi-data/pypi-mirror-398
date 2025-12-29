"""
Image processing methods that are necessary but not exclusive to alignment procedures.
"""

from typing import Tuple
import numpy as np
import scipy as sp


def compute_tukey_window(
        width: int,
        length: int = 0,
) -> np.ndarray[float]:
    """
    Tukey window, an array with decreasing values at the border from 1 to 0.
    Here, the shape parameter $\alpha$ is always 0.2; see
    [here](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.tukey.html)
    for more information.

    Parameters
    ----------
    width
        Width of the window.
    length
        Length of the window; the default is 0.

    Returns
    -------
        Tukey window, an array with dimensions :attr:`width` and :attr:`length`.
    """

    W = sp.signal.windows.tukey(width, 0.2)
    W = np.transpose(W[:, np.newaxis])

    if length > 0:
        V = sp.signal.windows.tukey(length, 0.2)
        V = V[:, np.newaxis]
        W = V * W
        W = W[..., np.newaxis]
    else:
        W = W[..., np.newaxis]
    return W


def get_img_grad(
    img: np.ndarray[float],
    x_axis_index: int = 1,
    y_axis_index: int = 0,
) -> Tuple[np.ndarray[float], np.ndarray[float]]:
    """
    Compute the vertical and horizontal gradient of the image.

    Parameters
    ----------
    img
        Image of wich we want to compute the gradient.

    Returns
    -------
        Tuple of two arrays that respectively contain the horizontal
        and vertical gradient of the image.
    """

    # check if its real, to enforce its type at the end
    is_real = ~np.iscomplexobj(img)

    Np = np.shape(img)

    # defining a basis vector
    vector = np.linspace(0, (Np[1] - 1) / (Np[1] + np.finfo(float).eps), Np[1])
    Y = 1j * 2 * np.pi * (np.fft.fftshift(vector) - 0.5)
    # Fourier transform on a list of vectors, i.e., FFT in one direction only
    f_img_Y = np.fft.fft(img, axis=1)
    # compute gradient in Fourier space
    dY = f_img_Y * np.transpose(Y[:, np.newaxis])
    # back to direct space
    dY = np.fft.ifft(dY, axis=1)

    vector = np.linspace(0, (Np[0] - 1) / (Np[0] + np.finfo(float).eps), Np[0])
    X = 1j * 2 * np.pi * (np.fft.fftshift(vector) - 0.5)
    # Fourier transform on a list of vector, i.e., FFT in one direction only
    f_img_X = np.fft.fft(img, axis=0)
    # compute gradient in Fourier space
    dX = np.transpose(np.transpose(f_img_X) * X[np.newaxis, :])
    # back to direct space
    dX = np.fft.ifft(dX, axis=0)

    # force real if it was
    if is_real:
        dX = np.real(dX)
        dY = np.real(dY)

    if x_axis_index == 0:
        return dX, dY
    # else invert them
    return dY, dX


def imshift_fft(
        img: np.ndarray[float],
        x: np.ndarray[float],
        y: np.ndarray[float],
) -> np.ndarray[float]:
    """
    Apply subpixel shift to a stack of images in direct space.

    Parameters
    ----------
    img
        Stack of images to translate; the array should have three dimensions,
        the last of which corresponds to the index relative to the stack.
    x
        Translation to apply along the 0 axis, for each image of the stack.
    y
        Translation to apply along the 1 axis, for each image of the stack.

    Returns
    -------
        Translated stack of images as a three-dimensional array.
    """

    if len(x) != img.shape[-1]:
        raise ValueError(f'The length of x ({len(x)}) does not match the'
                         f' third dimension of the input stack ({img.shape[-1]}).')
    if len(y) != img.shape[-1]:
        raise ValueError(f'The length of y ({len(y)}) does not match the'
                         f' third dimension of the input stack ({img.shape[-1]}).')

    img_t = np.zeros(img.shape, dtype=complex)

    # apply shift per image
    for index in range(img.shape[-1]):
        # do not use FFT shift, as its in a way included in the fourier_shift function,
        # and back to direct space
        tmp = np.fft.fft2(img[:, :, index])
        tmp = sp.ndimage.fourier_shift(tmp, (x[index], y[index]))
        img_t[:, :, index] = np.fft.ifft2(tmp)
    return np.real(img_t)


def smooth_edges(
        img: np.ndarray[float],
        smooth_kernel: int = 3,
) -> np.ndarray[float]:
    """Given a stack of 2D images this function smoothens the border of
    the images to avoid sharp edge artefacts during imshift_fft.

    Parameters
    ----------
    img
        Stack of images, for which to smoothen the edges; the array should
        have three dimensions, the last of which corresponds to the index
        relative to the stack.
    smooth_kernel : int, optional
        Size of the smoothing region.

    Returns
    -------
        Stack of images with smoothened edges.
    """

    # init
    Npix = np.shape(img)
    smooth_img = img

    # we do the smoothing on the two axes
    for i in range(2):
        # the middle coordinates of the image along the current axis
        half = int(np.ceil(Npix[i] / 2))
        # roll push and we want to pull, therefore we put a negative sign
        smooth_img = np.roll(smooth_img, -half, axis=i)
        # define the range of data that we are going to smoothen
        indices = half + np.linspace(-smooth_kernel, smooth_kernel, 2 * smooth_kernel + 1).astype(int) - 1
        # define the smoothing kernel
        ker_size = [1, 1, 1]
        # on the appropriate dimension we shape the kernel to the wanted size
        ker_size[i] = smooth_kernel

        # we extract the data that we want to smoothen, on the appropriate range and axis
        if i == 0:
            img_tmp = smooth_img[indices, :, ...]
        else:
            img_tmp = smooth_img[:, indices, ...]
        # smoothen across the image edges by convolution
        img_tmp = sp.ndimage.convolve(img_tmp, np.ones(ker_size), mode='constant')

        # avoid boundary issues
        boundary_shape = [1, 1, 1]
        boundary_shape[i] = 2 * smooth_kernel + 1

        # compute the core convolution that was applied
        convolution = sp.ndimage.convolve(np.ones(boundary_shape), np.ones(ker_size), mode='constant')

        # remove it from the image
        img_tmp = img_tmp / (convolution + np.finfo(float).eps)
        # what is left is just a convolution of the border

        # store the result on top of the original image, on the appriate range and axis
        if i == 0:
            smooth_img[indices, :, ...] = img_tmp
        else:
            smooth_img[:, indices, ...] = img_tmp
        # roll push
        smooth_img = np.roll(smooth_img, half, axis=i)
    return smooth_img


def imfilter_high_pass_1d(
        img: np.ndarray[float],
        ax: int,
        sigma: float,
) -> np.ndarray[float]:
    """Applies an FFT filter along the :attr:`ax` dimension that removes
    :attr:`sigma` ratio of the low frequencies.

    Parameters
    ----------
    img
        Input image as a two-dimensional array.
    ax
        Filtering axis.
    sigma
        Filtering intensity; should be between 0 and 1,
        where a value <=0 implies no filtering.

    Returns
    -------
        The filtered image.
    """

    if sigma <= 0:
        return img
    Ndims = np.ndim(img)
    Npix = np.shape(img)
    shape = np.ones((Ndims))
    shape[ax] = Npix[ax]

    isReal = ~np.iscomplexobj(img)

    img_f = np.fft.fft(img, axis=ax)

    # create
    x = np.linspace(-Npix[ax] / 2, Npix[ax] / 2 - 1, Npix[ax]) / (Npix[ax] + np.finfo(float).eps)
    x = np.reshape(x, shape.astype(int))

    # compute spectral filter
    spectral_filter = np.fft.fftshift(
        np.exp(1 / (-(x**2 + np.finfo(float).eps) / (sigma**2 + np.finfo(float).eps)))
    )

    img_f = img_f * spectral_filter
    img_filt = np.fft.ifft(img_f, axis=ax)

    if isReal:
        img_filt = np.real(img_filt)
    return img_filt


def center(
        tomogram: np.ndarray[float],
        use_shift: bool = True,
) -> Tuple[float, float, float]:
    """Find the center of mass of :attr:`tomogram` and return the
    displacement vector to find it at a given rate step, calculate
    variance if needed.

    Parameters
    ----------
    tomogram
        A tomogram in the form of a stack of 2D images; the array should have three dimensions,
        the last of which corresponds to the index relative to the stack.
    use_shift
        If ``True``, the center of mass is calculated relative to the center of the image.

    Returns
    -------
        A tuple that comprises the the x and y coordinates of
        the barycenter of mass as well as  the mass.
    """

    # size
    size_y = np.size(tomogram, 1)
    size_x = np.size(tomogram, 0)

    # the mass is just the sum of the values
    mass = np.sum(tomogram, axis=(0, 1)) + np.finfo(float).eps  # epsilon to avoid zero division latter

    # defining the grid to compute the barycenter
    xgrid = np.arange(0, size_x) + 1
    ygrid = np.transpose(np.arange(0, size_y) + 1)

    # compute the barycenter of mass
    pos_x = np.sum(xgrid[..., np.newaxis] * np.sum(tomogram, 1), 0) / mass  # sum on y, to weight the x
    pos_y = np.sum(ygrid[..., np.newaxis] * np.sum(tomogram, 0), 0) / mass  # sum on x, to weigth the y

    if use_shift:
        pos_x = pos_x - (size_x + 1) / 2  # defined so that center(ones(N), use_shift = true) == [0,0]
        pos_y = pos_y - (size_y + 1) / 2  # defined so that center(ones(N), use_shift = true) == [0,0]
    return pos_x, pos_y, mass  # pos_y => shift on the axis 1 ; pos_x => shift on the axis 0
