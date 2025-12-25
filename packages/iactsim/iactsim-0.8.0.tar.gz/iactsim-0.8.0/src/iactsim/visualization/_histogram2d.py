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

from matplotlib import colors
import matplotlib.pyplot as plt
import numpy as np
import cupy as cp

coordinate_indices = {
    'X': 0, 'x': 0,
    'Y': 1, 'y': 1,
    'Z': 2, 'z': 2,
}

def histogram2d(vectors3d, bins, plane='xy', to_weight=None, dx=None, ax=None, scale=1., norm=None, range=None, update_this=None, log=False, vmin=None, vmax=None, cmap='viridis', interpolation='nearest', colorbar=True, cbar_label=None, title=None, xlabel=None, ylabel=None, **kwargs):
    """Generates and displays a 2D histogram of two components of a set of 3D vectors.

    Parameters
    ----------
    vectors3d : numpy.ndarray
        A NumPy array representing a set of 3D vectors. The first two columns are used as x and y coordinates for the histogram. The third column is ignored.
    bins : int or array_like
        The number of bins or the bin edges (see `numpy.histogram2d` documentation for details).
    plane : str
        String representation of the components to plot, e.g.: 'xy', 'zy', 'zx', etc.
    to_weight : numpy.ndarray, optional
        Weights for each vector. If None, all vectors are weighted equally.
    dx : float, optional
        Determines the range if `range` is not explicitly provided. Defines a square region around the data's center with sides of length 2*dx.
    ax : matplotlib.axes.Axes, optional
        An Axes object to plot on. If None, the current axes (plt.gca()) is used.
    scale : float, optional
        Scaling factor applied to x and y coordinates.
    norm : matplotlib.colors.Normalize, optional
        Normalization instance for histogram data (e.g., `colors.LogNorm` for logarithmic scaling).
    range : sequence, optional
        A sequence of (min, max) pairs for each dimension, specifying the data range to be histogrammed.
    update_this : numpy.ndarray, optional
        A 2D array (another histogram) to be added to the calculated histogram.
    log : bool, optional
        If True, applies a log1p transformation (log(1 + x)) to the histogram counts.
    vmin : float, optional
        Minimum value for colormap scaling.
    vmax : float, optional
        Maximum value for colormap scaling.
    cmap : str, optional
        The colormap to use.
    interpolation : str, optional
        Interpolation method used by `imshow`.
    colorbar : bool, optional
        Whether to add a colorbar.
    cbar_label : str, optional
        Label for the colorbar.
    title : str, optional
        Title of the plot.
    xlabel : str, optional
        Label for the x-axis.
    ylabel : str, optional
        Label for the y-axis.
    **kwargs :
        Additional keyword arguments passed to `numpy.histogram2d`.

    Returns
    -------
    H : numpy.ndarray
        The 2D histogram array.
    im : matplotlib.image.AxesImage
        The image object returned by `imshow`.

    Examples
    --------
    >>> data = np.random.randn(1000, 3)
    >>> H, im = histogram2d(data, bins=50, log=True, title="2D Histogram")
    >>> plt.show()

    >>> weights = np.random.rand(1000)
    >>> H, im = histogram2d(data, bins=50, to_weight=weights, cbar_label="Average Weight")
    >>> plt.show()
    """
    if ax is None:
        ax = plt.gca()

    if not isinstance(plane, str) or len(plane)>2:
        raise(ValueError("`plane` argument must indicate in which plane perform the scatter plot (e.g. 'xy', 'Yx', 'Xz', etc...)."))
    
    index1 = coordinate_indices[plane[0]]
    index2 = coordinate_indices[plane[1]]

    if isinstance(vectors3d, cp.ndarray):
        vectors3d = vectors3d.get()
    
    x = vectors3d[:,index1] / scale
    y = vectors3d[:,index2] / scale

    where = (~np.isnan(x)) & (~np.isnan(y))
    x = x[where]
    y = y[where]

    if range is None and dx is not None:
        xc = np.nanmean(x)
        yc = np.nanmean(y)
        range = [[xc - dx, xc + dx], [yc - dx, yc + dx]]

    if to_weight is None:
        H, xedges, yedges = np.histogram2d(x, y, bins=bins, range=range, **kwargs)
    else:
        to_weight = to_weight[where]
        H, xedges, yedges = np.histogram2d(x, y, bins=bins, range=range, weights=to_weight, **kwargs)
        n, xedges, yedges = np.histogram2d(x, y, bins=bins, range=range, **kwargs)
        with np.errstate(divide='ignore', invalid='ignore'):
            H = np.nan_to_num(H / n)

    if update_this is not None:
        H += update_this

    if log:
        H = np.log1p(H)

    if norm is None:
        if log:
            norm = colors.LogNorm(vmin=vmin or np.nanmin(H[H > 0]), vmax=vmax or np.nanmax(H))
        else:
            norm = colors.Normalize(vmin=vmin, vmax=vmax)
        vmin = None
        vmax = None
    
    im = ax.imshow(H.T, origin='lower', extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], norm=norm, cmap=cmap, vmin=vmin, vmax=vmax, interpolation=interpolation)
    ax.set_aspect(1)

    if colorbar:
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        if cbar_label:
            cbar.set_label(cbar_label)

    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)

    return H, im