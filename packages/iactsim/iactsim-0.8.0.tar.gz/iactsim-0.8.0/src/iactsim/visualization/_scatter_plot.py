# Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of iactsim.
#
# iactsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iactsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import cupy as cp

coordinate_indices = {
    'X': 0, 'x': 0,
    'Y': 1, 'y': 1,
    'Z': 2, 'z': 2,
}

def scatter(vectors3d, colors_array=None, plane='xy', s=0.1, marker=None, ax=None, scale=1., cbar=True, **kwargs):
    """Creates a scatter plot of two components of a set of 3D vectors.

    Parameters
    ----------
    vectors3d : array_like
        A numpy.ndarray or list of 3D vectors. The shape should be (N, 3), where N is the number of vectors.
    colors_array : array_like, optional
        An numpy.ndarray of color values for each point. Can be a list of color names, a list of RGB/RGBA tuples, or a 1D array of numerical values to be mapped to colors using a colormap.
    plane : str
        String representation of the components to plot, e.g.: 'xy', 'zy', 'zx', etc.
    s : float, optional
        The marker size in points**2 (default: 0.1).
    marker : str, optional
        The marker style (default: None, which uses the default marker style from matplotlib). See `matplotlib.markers` for valid marker styles.
    ax : matplotlib.axes.Axes, optional
        The axes on which to plot. If None, the current axes are used (plt.gca()).
    scale : float, optional
        A scaling factor applied to the x and y coordinates (default: 1.).
    cbar : bool, optional
        Whether to add a colorbar (default: True). The colorbar will only be added if `colors_array` is also provided and is a list or NumPy array.
    **kwargs :
        Additional keyword arguments passed to `matplotlib.pyplot.scatter`. This allows for customization of the plot, such as setting the colormap ('cmap'), edgecolors ('edgecolors'), etc.

    Returns
    -------
    cax : matplotlib.axes.Axes or None
        The axes of the colorbar if a colorbar is created; otherwise, None.
    """
    if ax is None:
        ax = plt.gca()
    
    if not isinstance(plane, str) or len(plane)>2:
        raise(ValueError("`plane` argument must indicate in which plane perform the scatter plot (e.g. 'xy', 'Yx', 'Xz', etc...)."))
    index1 = coordinate_indices[plane[0]]
    index2 = coordinate_indices[plane[1]]

    if isinstance(vectors3d, cp.ndarray):
        vectors3d = vectors3d.get()

    x = vectors3d[:,index1]/scale
    y = vectors3d[:,index2]/scale

    sc = ax.scatter(x, y, s=s, marker=marker, c=colors_array, **kwargs)
    ax.set_aspect(1)
    cax = None
    if isinstance(colors_array, (list, np.ndarray)) and cbar:
        ax_divider = make_axes_locatable(ax)
        cax = ax_divider.append_axes("right", size="5%", pad=f"{3}%")
        plt.colorbar(sc, cax=cax)
        plt.sca(ax)

    return cax