import numpy as np
from numpy.typing import NDArray


def TOMCAT_7(half_sphere: bool = True) -> NDArray:
    r""" The seven sensitivity directions used in publications by the TOMCAT group.

    Parameters
    ----------
    half_sphere
        Whether to use points only covering the half sphere or the full sphere.

    Returns
    ---------
    directions
        Array with shape ``(N, 3)`` containing the coordinated of the ``N`` unit vectors.
    """

    # Hard coded {100} and {111} cubic directions in the +z hemisphere
    directions = [[1.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0],
                  [0.0, 0.0, 1.0],
                  [1.0, 1.0, 1.0],
                  [1.0, -1.0, 1.0],
                  [-1.0, 1.0, 1.0],
                  [-1.0, -1.0, 1.0]]

    directions = np.stack(directions)

    if not half_sphere:
        directions = np.concatenate((directions, -directions), axis=0)

    # Normalize
    norm = np.linalg.norm(directions, axis=1)
    directions = directions/norm[:, np.newaxis]

    return directions


def football(half_sphere=True) -> NDArray:
    r""" 16 sensitivity directions uniformly distributed on the half sphere.

    Parameters
    ----------
    half_sphere
        Whether to use points only covering the half sphere or the full sphere.

    Returns
    ---------
    directions
        Array with shape ``(N, 3)`` containing the coordinated of the ``N`` unit vectors.
    """

    # football face centers in the +z hemisphere
    C0 = 3*(np.sqrt(5) - 1)/4
    C1 = 9*(9 + np.sqrt(5))/76
    C2 = 9*(7 + 5 * np.sqrt(5))/76
    C3 = 3*(1 + np.sqrt(5))/4

    directions = np.array([[0.0, C0, C3],
                           [0.0, -C0, C3],
                           [C3, 0.0, C0],
                           [-C3, 0.0, C0],
                           [C0, C3, 0.0],
                           [-C0, C3, 0.0],
                           [C1, 0.0, C2],
                           [-C1, 0.0, C2],
                           [C2, C1, 0.0],
                           [-C2, C1, 0.0],
                           [0.0, C2, C1],
                           [0.0, -C2, C1],
                           [1.5, 1.5, 1.5],
                           [1.5, -1.5, 1.5],
                           [-1.5, 1.5, 1.5],
                           [-1.5, -1.5, 1.5]])

    directions = np.stack(directions)

    if not half_sphere:
        directions = np.concatenate((directions, -directions), axis=0)

    # Normalize
    norm = np.linalg.norm(directions, axis=1)
    directions = directions / norm[:, np.newaxis]

    return directions
