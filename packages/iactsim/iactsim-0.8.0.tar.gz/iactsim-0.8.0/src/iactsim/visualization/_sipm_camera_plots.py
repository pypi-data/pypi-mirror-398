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

import inspect
from typing import Callable, Optional, Any, List, Tuple, TYPE_CHECKING
if TYPE_CHECKING:
    from ..electronics._camera import CherenkovSiPMCamera

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from ._iactsim_style import iactsim_style

@iactsim_style
def plot_sipm_modules(
    camera : 'CherenkovSiPMCamera',
    plotf : Callable[[int, Optional[matplotlib.axes.Axes]], Any],
    figsize: float = 10,
    sep_factor: float = 1.25,
    skip: Optional[List[int]] = None
    ) -> Tuple[matplotlib.figure.Figure, List[matplotlib.axes.Axes]]:
    """
    Creates a custom plot for each module based on its ID using a provided plotting function.

    Parameters
    ----------
    camera : CherenkovSiPMCamera
        Camera from which extract geometry info. 
    plotf : Callable[[int, Optional[matplotlib.axes.Axes]], Any]
        A callable that takes the module index (an integer starting from 0)
        as its first argument, and optionally a matplotlib Axes
        object as the second argument.  This function is responsible for
        generating the plot content for each module.  If `plotf` only accepts
        one argument, it's called with the module index only.  If it
        accepts two, it's called with the module index and the
        corresponding Axes object.
    figsize : float
        The size of the figure (both width and height) in inches. By default 10
    sep_factor : float
        A scaling factor that controls the separation between
        modules in the plot.  A larger `sep_factor` results in more
        space between modules. By default 1.25.
    skip : Optional[List[int]], default=None
        An optional list of module indices to skip plotting.

    Returns
    -------
    Tuple[matplotlib.figure.Figure, List[matplotlib.axes.Axes]]
        A tuple containing:
            - fig: The Matplotlib figure object.
            - axes: A list of Matplotlib Axes objects, one for each plotted module.

    Raises
    ------
    RuntimeError
        If `camera.geometry` is None (no camera geometry is defined).
    """
    if camera.geometry is None:
        raise(RuntimeError("A camera geometry must be defined in order to show SiPM module plots."))

    if skip is None:
        skip = []

    # Scale real coordinates into figure coordinates
    x, y,_ = camera.geometry.modules_p.T
    side = camera.geometry.module_side

    scale = (max(np.sqrt(x**2+y**2))*2+side*np.sqrt(2))
    x = (x-min(x)) / scale
    y = (y-min(y)) / scale
    
    side = side / scale / sep_factor
    h_side = 0.5*side

    fig = plt.figure(figsize=(figsize, figsize))
    axes = []
    for module_id in range(len(x)):
        if module_id in skip:
            continue
        ax = fig.add_axes([x[module_id]+h_side, y[module_id]+h_side, side, side])

        n_parameters = len(inspect.signature(plotf).parameters)
        if n_parameters == 1:
            plt.sca(ax)
            plotf(module_id)
        else:
            plotf(module_id, ax)
        
        axes.append(ax)
    
    return fig, axes

@iactsim_style
def plot_sipm_module_pixels(
        camera : 'CherenkovSiPMCamera',
        plotf : Callable[[int, Optional[matplotlib.axes.Axes]], Any], 
        subplot_size : float = 4
        ) -> Tuple[matplotlib.figure.Figure, List[matplotlib.axes.Axes]]:

    """
    Creates a custom plot for each pixel of a module based on its ID using a provided plotting function.

    Parameters
    ----------
    camera : CherenkovSiPMCamera
        Camera from which extract geometry info. 
    plotf : Callable[[int, Optional[matplotlib.axes.Axes]], Any]
        A callable that takes the pixel index (an integer starting from 0)
        as its first argument, and optionally a matplotlib Axes
        object as the second argument.  This function is responsible for
        generating the plot content for each pixel.  If `plotf` only accepts
        one argument, it's called with the pixel index only.  If it
        accepts two, it's called with the pixel index and the
        corresponding Axes object.
    subplot_size : float
        The size of the pixel subplot (both width and height) in inches. By default 4

    Returns
    -------
    Tuple[matplotlib.figure.Figure, List[matplotlib.axes.Axes]]
        A tuple containing:
            - fig: The Matplotlib figure object.
            - axes: A list of Matplotlib Axes objects, one for each plotted pixel.

    Raises
    ------
    RuntimeError
        If `camera.geometry` is None (no camera geometry is defined).
    """

    if camera.geometry is None:
        raise(RuntimeError("A camera geometry must be defined in order to show SiPM module plots."))

    pix_per_side = round(camera.geometry.module_side/(camera.geometry.pixel_active_side+camera.geometry.pixels_separation))

    fig_size = pix_per_side * subplot_size
    fig, axes = plt.subplots(pix_per_side,pix_per_side,figsize=(fig_size,fig_size))
    axes = [ax for axs in axes[::-1] for ax in axs] # flatten

    n_parameters = len(inspect.signature(plotf).parameters)

    for pixel_id,ax in enumerate(axes):        
        if n_parameters == 1:
            plt.sca(ax)
            plotf(pixel_id)
        else:
            plotf(pixel_id, ax)
    
    return fig, axes