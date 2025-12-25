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

import abc
import numpy as np
from typing import Union, List

class SiPMCameraGeometry(abc.ABC):
    """
    Abstract base class for defining the geometry of the focal plane of a Silicon Photomultiplier (SiPM) camera of squared SiPM tiles.
    Default unit is mm.
    """

    @property
    @abc.abstractmethod
    def body_dimensions(self) -> Union[tuple[float], List[float], np.ndarray]:
        """Camera body dimensions:
        
            - width, height (optical axis), depth for rectangular cameras;
            - radius, height (optical axis) for cylindrical cameras.

        Returns
        -------
        Union[tuple[float, float, float], List[float], numpy.ndarray]
            A tuple, list or NumPy array containing the width, height, and depth of the camera body.
            Using numpy array is preferable.
        """
        pass

    @property
    @abc.abstractmethod
    def position(self) -> Union[tuple[float, float, float], List[float], np.ndarray]:
        """Camera surface center position in the focal surface reference frame.

        Returns
        -------
        Union[tuple[float, float, float], List[float], numpy.ndarray]
            A tuple, list or NumPy array representing the (x, y, z) coordinates of the camera surface center.
            Using numpy array is preferable.
        """
        pass

    @property
    @abc.abstractmethod
    def modules_p(self) -> Union[tuple[float, float, float], List[float], np.ndarray]:
        """Modules center position in the focal surface reference frame.

        Returns
        -------
        Union[tuple[float, float, float], List[float], numpy.ndarray]
            A tuple, list or NumPy array representing the (x, y, z) coordinates of the modules center.
            Using numpy array is preferable.
        """
        pass

    @property
    @abc.abstractmethod
    def modules_n(self) -> Union[tuple[float, float, float], List[float], np.ndarray]:
        """Modules normal vector in the focal surface reference frame.

        Returns
        -------
        Union[tuple[float, float, float], List[float], numpy.ndarray]
            A tuple, list or NumPy array representing the (x, y, z) components of the modules normal vector.
            Using numpy array is preferable.
        """
        pass

    @property
    @abc.abstractmethod
    def module_side(self) -> float:
        """Length of module edges from the first to the last pixel active area::

            y
            ^   __   __   __
            |  |__| |__| |__|
            |   __   __   __
            |  |__| |__| |__|
            |   __   __   __
            |  |__| |__| |__|
            |   <---------->
            |   3x3 module side
            -------------------> x

        Returns
        -------
        float
            The length of the module side.
        """
        pass

    @property
    @abc.abstractmethod
    def pixel_active_side(self) -> float:
        """Length of the pixel active area edge::

            y  Active area edge
            ^    <------>
            |    ________      ________
            |   | active |    |        |
            |   |  area  |    |        |
            |   |        |    |        |
            |   |________|    |________|
            |
            --------->x

        Returns
        -------
        float
            The length of the pixel active area side.
        """
        pass

    @property
    @abc.abstractmethod
    def pixels_separation(self) -> float:
        """Gap between pixels active area::

            y       Pixels separation
            ^    ________ <--> ________
            |   |        |    |        |
            |   |        |    |        |
            |   |        |    |        |
            |   |________|    |________|
            |
            --------->x

        Returns
        -------
        float
            The distance between pixel active areas.
        """
        pass