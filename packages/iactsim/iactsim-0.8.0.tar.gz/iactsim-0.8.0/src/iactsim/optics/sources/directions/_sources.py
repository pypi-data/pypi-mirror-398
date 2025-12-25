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
from abc import ABC, abstractmethod

from ..._cpu_transforms import local_to_pointing_rotation

class AbstractPhotonDirections(ABC):
    """
    Abstract base class for a photon source direction generator.

    This class defines the interface for generating photon directions,
    specified by altitude and azimuth angles.

    Attributes
    ----------
    altitude : float
        Altitude angle of the source (in degrees).
    azimuth : float
        Azimuth angle of the source (in degrees).
    """
    def __init__(self, altitude: float, azimuth: float, dtype: type = cp.float32, seed: int | None = None):
        self._altitude = altitude
        self._azimuth = azimuth
        self.dtype = dtype
        self.seed = seed
        self._rot_to_local = cp.asarray(local_to_pointing_rotation(self._altitude, self._azimuth).T, dtype=self.dtype)
    
    @property
    def seed(self):
        """Seed to initialize the CuPy random number generator (cuRAND Philox4x3210)."""
        return self._seed
    
    @seed.setter
    def seed(self, a_seed):
        self.rng = cp.random.default_rng(cp.random.Philox4x3210(a_seed))
        self._seed = a_seed

    @property
    def altitude(self):
        """Source altitude (deg)."""
        return self._altitude

    @altitude.setter
    def altitude(self, alt):
        self._altitude = alt
        self._rot_to_local = cp.asarray(local_to_pointing_rotation(self._altitude, self._azimuth).T, dtype=self.dtype)

    @property
    def azimuth(self):
        """Source azimuth (deg)."""
        return self._azimuth

    @azimuth.setter
    def azimuth(self, az):
        self._azimuth = az
        self._rot_to_local = cp.asarray(local_to_pointing_rotation(self._altitude, self._azimuth).T, dtype=self.dtype)
    
    @abstractmethod
    def generate(self, n: int) -> cp.ndarray:
        """
        Generates photon direction vectors.

        Parameters
        ----------
        n : int
            Number of photon directions to generate.

        Returns
        -------
        directions : cp.ndarray
            A CuPy array of shape (n, 3) where each row represents a
            photon direction vector (unit vector).

        Raises
        ------
        ValueError
            If n is not a positive integer.
        """
        if not isinstance(n, int) or n <= 0:
            raise ValueError("`n` must be a positive integer.")
        pass

class PointLike(AbstractPhotonDirections):
    """
    Generates a set of identical direction vector from a source specified in 
    horizontal coordinates.

    This class creates an array of `n` identical unit vectors that represent
    the direction of a source specified by its altitude and azimuth angles.

    Parameters
    ----------
    altitude : float
        Altitude angle of the source in degrees.
    azimuth : float
        Azimuthal angle of the source in degrees (0 degrees corresponds to the
        positive x-axis, and the angle increases counterclockwise).
    dtype : data-type, optional
        Desired output data-type. Defaults to `cp.float32`.
    """

    def __init__(self, altitude: float, azimuth: float, dtype: type = cp.float32):
        super().__init__(altitude, azimuth, dtype=dtype)

    def generate(self, n: int) -> cp.ndarray:
        """
        Generates the set of identical direction vectors.

        Parameters
        ----------
        n : int
            Number of identical direction vectors to generate.

        Returns
        -------
        vs : ndarray, shape (n, 3)
            An array of `n` identical unit vectors representing the direction of
            the source in a right-handed Cartesian coordinate system.

        Raises
        ------
        ValueError
            If `n` is not a positive integer.
        """

        if not isinstance(n, int) or n <= 0:
            raise ValueError("`n` must be a positive integer.")

        vs: cp.ndarray = cp.empty((n, 3), dtype=self.dtype)
        vs[:, :2] = 0.
        vs[:, 2] = 1.

        vs = vs @ self._rot_to_local
        vs[:, :] *= -1.

        return vs

class UniformBeam(AbstractPhotonDirections):
    """
    Generates uniformly distributed directions within a cone around a central direction.

    This class provides a way to generate `n` unit vectors that are uniformly
    distributed within a cone defined by a central direction (`altitude`, `azimuth`)
    and an aperture angle. The distribution is uniform in the sense that the
    probability of finding a vector within a given solid angle is proportional
    to that solid angle.

    Parameters
    ----------
    altitude : float
        Altitude angle of the central direction of the cone (in degrees).
    azimuth : float
        Azimuth angle of the central direction of the cone (in degrees).
    aperture : float
        Angular half-size (radius) of the cone (in degrees).
    dtype : data-type, optional
        Desired data type of the output array, by default cupy.float32
    seed : int | None, optional
        A seed to initialize the CuPy random number generator (cuRAND Philox4x3210). If None, the
        generator is seeded using unpredictable data from the operating system.
    """

    def __init__(
            self,
            altitude: float,
            azimuth: float,
            half_aperture: float,
            dtype: type = cp.float32,
            seed: int | None = None
        ):
        super().__init__(altitude, azimuth, dtype=dtype, seed=seed)
        self.half_aperture = half_aperture

    def generate(self, n: int) -> cp.ndarray:
        """
        Generates `n` uniformly distributed direction vectors within the cone.

        Parameters
        ----------
        n : int
            Number of direction vectors to generate.

        Returns
        -------
        directions : ndarray, shape (n, 3)
            A CuPy array of shape (n, 3) containing the generated direction vectors.
            Each row represents a unit vector (x, y, z).

        Raises
        ------
        ValueError
            If `n` is not a positive integer.
        """
        if not isinstance(n, int) or n <= 0:
            raise ValueError("`n` must be a positive integer.")

        # Ensure uniform distribution over the sphere's surface within the cone
        phis = 2 * cp.pi * self.rng.random(size=n)
        aperture_rad = self.half_aperture / 180. * cp.pi
        cos_theta_min = cp.cos(aperture_rad)
        cos_thetas = self.rng.uniform(cos_theta_min, 1., n)
        thetas = cp.arccos(cos_thetas)

        # Allocate array for direction vectors
        vs = cp.empty((n, 3), dtype=self.dtype)

        sith = cp.sin(thetas)

        # Convert spherical coordinates (altitude, azimuth) to Cartesian coordinates (x, y, z)
        vs[:, 0] = cp.cos(phis) * sith  # x-component
        vs[:, 1] = cp.sin(phis) * sith  # y-component
        vs[:, 2] = cos_thetas #cp.cos(thetas)  # z-component

        # Apply the rotation to the direction vectors
        vs = vs @ self._rot_to_local

        # Flip the z-axis
        vs[:, :] *= -1.

        return vs

class GaussianBeam(AbstractPhotonDirections):
    """
    Generates direction vectors with a Gaussian distribution around a central direction.

    This class generates `n` direction vectors sampled from a Gaussian
    distribution centered around the direction specified by `altitude` and `azimuth`.
    The spread of the distribution is controlled by `dispersion`.

    Parameters
    ----------
    altitude : float
        Altitude angle of the beam center in degrees.
    azimuth : float
        Azimuthal angle of the beam center in degrees.
    dispersion : float
        Standard deviation (sigma) of the Gaussian distribution in degrees.
    seed : int | None, optional
        A seed to initialize the CuPy random number generator (cuRAND Philox4x3210). If None, the
        generator is seeded using unpredictable data from the operating system.
    dtype : data-type, optional
        Desired output data-type. Default is `cp.float32`.

    """
    def __init__(self, altitude: float, azimuth: float, dispersion: float, seed: int | None = None, dtype: type = cp.float32):
        super().__init__(altitude, azimuth, dtype=dtype, seed=seed)
        self.dispersion = dispersion
    
    def generate(self, n: int) -> cp.ndarray:
        """
        Generates the direction vectors sampled from the Gaussian beam.

        Parameters
        ----------
        n : int
            Number of direction vectors to generate. Must be a positive integer.

        Returns
        -------
        vs : ndarray, shape (n, 3)
            An array of `n` unit vectors representing the directions sampled from
            the Gaussian beam in a right-handed Cartesian coordinate system.
        
        Raises
        ------
        ValueError
            If `n` is not a positive integer.
        """

        if not isinstance(n, int) or n <= 0:
            raise ValueError("`n` must be a positive integer.")

        logu = cp.log(self.rng.random(size=n))
        thetas = self.dispersion / 180 * cp.sqrt(-2. * logu) * cp.pi
        phis = self.rng.random(size=n) * 2. * cp.pi

        sin_theta = cp.sin(thetas)
        cos_theta = cp.cos(thetas)
        sin_phi = cp.sin(phis)
        cos_phi = cp.cos(phis)

        # Allocate array for direction vectors
        vs = cp.empty((n, 3), dtype=self.dtype)
        vs[:, 0] = sin_theta * cos_phi
        vs[:, 1] = -sin_theta * sin_phi
        vs[:, 2] = cos_theta

        # Apply the rotation to the direction vectors
        vs = vs @ self._rot_to_local

        # Flip the z-axis
        vs[:, :] *= -1.

        return vs