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

import cupy as cp
import numpy as np

from abc import ABC, abstractmethod

from .._utils import _disk_picking

def check_position(position, dtype=cp.float32):
    # Convert position to a CuPy array if it's not already
    
    if isinstance(position, (list, tuple)):
        position = np.array(position)
    
    if isinstance(position, np.ndarray):
        position = cp.asarray(position, dtype=dtype)
    
    if not isinstance(position, cp.ndarray):
        raise TypeError("position must be a list, tuple, Numpy ndarray or CuPy ndarray.")

    if position.shape != (3,):
        raise ValueError("position must be a 3-element array_like object.")
    
    return position

class AbstractPhotonPositions(ABC):
    """
    Abstract base class for a photon position generator.

    This class defines the interface for generating photon positions in 3D space.

    Attributes
    ----------
    position : cp.ndarray
        The (x, y, z) coordinates of the point or center of the photon source.
    rotation : cp.ndarray
        Rotation to be applied to the generated points.
    dtype : type
        The desired data type of the returned array.
    seed : int | None
        Seed for the random number generator.
    """

    def __init__(self, position: tuple | list | np.ndarray | cp.ndarray, rotation: np.ndarray | cp.ndarray = None, dtype: type = cp.float32, seed: int | None = None):
        self.position = position
        self.dtype = dtype
        self.seed = seed
        self.rotation = None

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, a_position):
        self._position = check_position(a_position)

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, a_rotation):
        if a_rotation is not None:
            a_rotation = cp.asarray(a_rotation, self.dtype)
        self._rotation = a_rotation
    
    @property
    def seed(self):
        return self._seed
    
    @seed.setter
    def seed(self, a_seed):
        self.rng = cp.random.default_rng(cp.random.Philox4x3210(a_seed))
        self._seed = a_seed
    
    @abstractmethod
    def _generate(self, n: int) -> cp.ndarray:
        if not isinstance(n, int) or n <= 0:
            raise ValueError("`n` must be a positive integer.")
        pass

    def generate(self, n: int) -> cp.ndarray:
        """
        Generates photon positions.

        Parameters
        ----------
        n : int
            Number of photon positions to generate.

        Returns
        -------
        positions : cp.ndarray
            A CuPy array of shape (n, 3) where each row represents a
            photon position vector (x, y, z).

        Raises
        ------
        ValueError
            If n is not a positive integer.
        """
        ps = self._generate(n)
        if self.rotation is not None:
            ps = ps @ self.rotation
        ps += self.position
       
        return ps 

class PointLike(AbstractPhotonPositions):
    """
    Represents a point source by generating a set of identical 3D points.

    This class creates an array of `n` identical 3D points, all located at the
    specified `position`.

    Parameters
    ----------
    position : tuple, list, or cp.ndarray, shape (3,)
        The (x, y, z) coordinates of the point source. Can be a tuple, list, or CuPy array.
    dtype : type, optional
        The desired data type of the returned array. Defaults to `cp.float32`.
    seed : int | None, optional
        Seed for the random number generator.

    Raises
    ------
    ValueError
        If `position` is not a 3-element tuple, list, or CuPy array.
    """

    def __init__(self, position: tuple | list | cp.ndarray, rotation: cp.ndarray = None, dtype: type = cp.float32, seed: int | None = None):
        super().__init__(position, rotation=rotation, dtype=dtype, seed=seed)

    def _generate(self, n: int) -> cp.ndarray:
        """
        Generates the set of identical 3D points representing the point source.

        Parameters
        ----------
        n : int
            The number of identical points to generate.

        Returns
        -------
        ps : cp.ndarray, shape (n, 3)
            A CuPy array where each row represents a point at the given `position`.

        Raises
        ------
        ValueError
            If `n` is not a positive integer.
        """
        if not isinstance(n, int) or n <= 0:
            raise ValueError("`n` must be a positive integer.")
        
        ps = cp.zeros((n, 3), dtype=self.dtype)

        return ps

class UniformDisk(AbstractPhotonPositions):
    """
    Generates uniformly distributed points on a disk (or annulus) parallel to the x-y plane.

    Parameters
    ----------
    r_min : float
        Minimum radius of the disk (or annulus). If `r_min` > 0, it defines the inner radius of an annulus.
    r_max : float
        Maximum radius of the disk (or annulus). Defines the outer radius.
    position : array_like, shape (3,)
        Center of the disk (or annulus) in Cartesian coordinates. Can be a list, tuple, NumPy array or CuPy array.
    radial_uniformity : bool, optional
        If True (default), uses a radial uniform distribution. If False, uses a uniform distribution in area.
    random : bool, optional
        If True (default), generates random points. If False, generates a grid of points.
    seed : int | None, optional
        A seed to initialize the random number generator.
    dtype : type, optional
        Desired data type of the output array, by default cp.float32.

    Raises
    ------
    ValueError
        If `position` does not have a length of 3.
        If `r_min` is not >= 0 and less than `r_max`.
    TypeError
        If `position` is not a list, tuple, NumPy array or CuPy array.
    """

    def __init__(self,
                 r_min: float,
                 r_max: float,
                 position: list | tuple | np.ndarray | cp.ndarray = cp.asarray([0., 0., 0.]),
                 rotation: np.ndarray | cp.ndarray = None,
                 radial_uniformity: bool = False,
                 random: bool = True,
                 seed: int | None = None,
                 dtype: type = cp.float32):
        super().__init__(position, rotation=rotation, dtype=dtype, seed=seed)
        self.r_min = r_min 
        self.r_max = r_max
        self.radial_uniformity = radial_uniformity
        self.random = random

    @property
    def r_min(self):
        return self._r_min

    @r_min.setter
    def r_min(self, value):
        if not (isinstance(value, (int, float)) and value >= 0):
            raise ValueError("r_min must be a non-negative number")
        self._r_min = float(value)

    @property
    def r_max(self):
        return self._r_max

    @r_max.setter
    def r_max(self, value):
        if not (isinstance(value, (int, float)) and value > 0):
            raise ValueError("r_max must be a positive number")
        self._r_max = float(value)

    def _check_radii(self):
        """Checks that r_min and r_max are valid."""
        if self.r_min >= self.r_max:
            raise ValueError("r_min must be strictly less than r_max")

    def _generate(self, n: int) -> cp.ndarray:
        """
        Generate points on the disk (or annulus).

        Parameters
        ----------
        n : int
            Number of points to generate.

        Returns
        -------
        ps : ndarray, shape (n, 3)
            The generated points on the disk (or annulus). Each row represents a point (x, y, z).
        """
        self._check_radii()

        if self.random:
            ps = _disk_picking(self.r_min, self.r_max, n, self.seed, radial_uniformity=self.radial_uniformity, dtype=self.dtype)
        else:
            # The number of points could be changed
            if self.radial_uniformity:
                n_theta = int(cp.sqrt(n))
                n_r = n_theta
                n = n_r*n_theta

                theta = cp.linspace(0, 2*cp.pi, n_theta, endpoint=False)
                r = cp.linspace(self.r_min, self.r_max, n_r)
                
                p1, p2 = cp.meshgrid(theta, r, sparse=False)
                p1 = p1.reshape((n,))
                p2 = p2.reshape((n,))

                ps = cp.empty((n, 3), dtype=self.dtype)
                ps[:, 0] = p2 * cp.cos(p1)
                ps[:, 1] = p2 * cp.sin(p1)
                ps[:, 2] = 0.
            
            else:
                n = n / (1. - self.r_min**2 / self.r_max**2) / cp.pi * 4
                n = int(cp.sqrt(n))

                x = cp.linspace(-self.r_max, self.r_max, n)
                p1, p2 = cp.meshgrid(x, x, sparse=False)
                p1 = p1.reshape((n * n,))
                p2 = p2.reshape((n * n,))
                r = cp.sqrt(p1**2 + p2**2)
                where = (r > self.r_min) & (r < self.r_max)
                p1 = p1[where]
                p2 = p2[where]
                p3 = cp.zeros_like(p1)

                n = p1.shape[0]
                ps = cp.empty((n, 3), dtype=self.dtype)
                ps[:, 0] = p1
                ps[:, 1] = p2
                ps[:, 2] = p3

        return ps

class UniformSphericalCap(AbstractPhotonPositions):
    """
    Generates uniformly distributed points on a spherical cap.

    The spherical cap is defined by its center (`position`), radius,
    and an angular extent (or "opening angle").
    Points are uniformly distributed over the cap's surface and are
    generated symmetrically around the z-axis, relative to the center.

    Parameters
    ----------
    position : array_like, shape (3,)
        The center of the sphere in Cartesian coordinates (x, y, z).
        Can be a list, tuple, NumPy array or CuPy array.
    radius : float
        The radius of the sphere.
    angular_extent : float
        The opening angle of the cap in degrees, measured from the positive
        z-axis. Must be between 0 and 180 degrees.
    seed : int | None, optional
        An optional seed for the random number generator. If None, the
        generator is seeded using unpredictable data from the operating system.
    dtype : type, optional
        The desired data type of the returned array (default: np.float32).

    Raises
    ------
    ValueError
        If angular_extent is not within the range [0, 180].
        If position does not have a length of 3.
    TypeError
        If position is not a list, tuple, or ndarray.
    """

    def __init__(self, 
                 radius: float,
                 angular_extent: float,
                 seed: int | None = None,
                 position: list | tuple | np.ndarray | cp.ndarray = cp.asarray([0., 0., 0.]),
                 rotation: np.ndarray | cp.ndarray = None,
                 dtype: type = cp.float32):
        super().__init__(position, rotation=rotation, dtype=dtype, seed=seed)

        if not (0 <= angular_extent <= 180):
            raise ValueError("angular_extent must be between 0 and 180 degrees")

        self.radius = radius
        self.angular_extent = angular_extent

    def _generate(self, n: int) -> cp.ndarray:
        """
        Generates `n` random points on the spherical cap.

        Parameters
        ----------
        n : int
            The number of points to generate.

        Returns
        -------
        ndarray
            A CuPy array of shape (n, 3) containing the Cartesian coordinates
            (x, y, z) of the generated points. The points are relative to the origin
            of the coordinate system, not the center of the sphere.
        """
        # Azimuth (longitude)
        theta = 2. * cp.pi * self.rng.random(n)

        # Altitude (latitude)
        cosmin = cp.cos(cp.deg2rad(self.angular_extent))
        cos = self.rng.random(n) * (1. - cosmin) + cosmin
        phi = cp.arccos(cos)

        ps = cp.empty((n, 3), dtype=self.dtype)
        sinph = cp.sin(phi)
        ps[:, 0] = self.radius * cp.cos(theta) * sinph
        ps[:, 1] = self.radius * cp.sin(theta) * sinph
        ps[:, 2] = self.radius * cp.cos(phi)

        return ps