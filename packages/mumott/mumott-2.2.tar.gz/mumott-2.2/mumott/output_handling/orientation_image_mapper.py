""" Container for class OrientationImageMapper. """
from matplotlib.colors import Colormap
from matplotlib.cm import get_cmap
import colorcet # noqa
from typing import Union
import numpy as np


class OrientationImageMapper():

    def __init__(self,
                 colormap: Union[str, Colormap] = 'cet_cyclic_isoluminant'):
        """
        Helper class for generating a color wheel to be used in plots.

        Parameters
        ----------
        colormap : Union[str, Colormap]
            The colormap to be used for creating the colorwheel. Should be cyclic.
            Default is ``cet_cyclic_isoluminant``.
        """
        self._colormap = get_cmap(colormap)
        r = np.sqrt(np.linspace(1.0, 0.0, 360))
        th = np.linspace(0, 2 * np.pi, 360)
        th, r = np.meshgrid(th, r)
        th_flip = np.arctan2(np.cos(th), np.sin(th))
        thx = (th[:-1, :-1] - (th[:-1, :-1] > np.pi).astype(float) * np.pi) / np.pi
        thx = self._colormap(thx)
        self._wheel_properties = [th_flip, r, thx]

    @property
    def colormap(self) -> Colormap:
        """ Returns the colormap used by the wheel. """
        return self._colormap

    @property
    def wheel_properties(self) -> list:
        """ Returns wheel properties as a list. The entry at
        ``wheel_properties[0]`` contains the angles. ``wheel_properties[1]`` contains the radius.
        ``wheel_properties[2]`` contains the RGBA values mapped to the angles. """
        return self._wheel_properties
