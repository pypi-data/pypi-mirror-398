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

from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..._iact import IACT

import numpy as np
import cupy as cp
import matplotlib.pyplot as plt

from .directions import (
    AbstractPhotonDirections,
    PointLike as PointLikeDir,
    UniformBeam,
    GaussianBeam
)

from .positions import (
    AbstractPhotonPositions,
    PointLike as PointLikePos,
    UniformDisk,
    UniformSphericalCap
)

from .._cpu_transforms import pointing_dir, local_to_pointing_rotation, local_to_telescope_rotation
from .._surface import SurfaceType

class Spectrum():
    """Generate a photon spectral distribution.

    Parameters
    ----------
    type : str
        Distribution type. Supported values are: "uniform", "constant", and "cherenkov".
    
    """
    
    __spectra = ['uniform', 'constant', 'cherenkov']

    def __init__(self, type: str):
        self.type: str = type  #: Distribution type, supported values are: "uniform", "constant" and "cherenkov".
        self.lmin: float = 200.  #: Minimum wavelength (in nm).
        self.lmax: float = 900.  #: Maximum wavelength (in nm).
        self.l0: float = 450.  #: Central wavelength (in nm, used only if :attr:`type` is "constant").
        self.dtype: type = cp.float32  #: Data type for generated wavelengths.
        self.seed = None

    @property
    def seed(self):
        return self._seed
    
    @seed.setter
    def seed(self, a_seed):
        self.rng = cp.random.default_rng(cp.random.Philox4x3210(a_seed))
        self._seed = a_seed
    
    @property
    def type(self) -> str:
        """
        str
            The distribution type ("uniform", "constant", or "cherenkov")
        """
        return self.__type

    @type.setter
    def type(self, dist_type: str):
        if dist_type not in self.__spectra:
            raise ValueError(f"Spectrum '{dist_type}' not supported. Supported choices are {self.__spectra}")
        self.__type = dist_type

    def generate(self, n: int) -> cp.ndarray:
        """
        Generates wavelength samples based on the specified distribution.

        Parameters
        ----------
        n : int
            The number of samples to generate.

        Returns
        -------
        sample : ndarray
            An array of generated wavelength samples.

        Raises
        ------
        NotImplementedError
            If the distribution type is not recognized.
        """
        if self.__type == 'cherenkov':
            emin = 1. / self.lmax
            emax = 1. / self.lmin
            sample = 1. / self.rng.uniform(emin, emax, size=n, dtype=self.dtype)

        elif self.__type == 'uniform':
            sample = self.rng.uniform(self.lmin, self.lmax, size=n, dtype=self.dtype)
        elif self.__type == 'constant':
            sample = cp.full((n,), self.l0, dtype=self.dtype)
        else:
            raise NotImplementedError(f"Distribution {self.__type} is not yet implemented.")
        return sample

class TimeDistribution():
    """Generate photon arrival times.
        
        Parameters
        ----------
        type : str
            Distribution type. Supported values are: "uniform" (i.e. Poissonian) and "constant".

    """
    __dists = ['uniform', 'constant']

    def __init__(self, type: str):
        self.type: str = type  #: Distribution type, supported values are: "uniform" and "constant".
        self.tmin: float = 0.  #: Start time (in ns).
        self.tmax: float = 10.  #: End time (in ns).
        self.t0: float = 0.  #: Central time (in ns, used only if :attr:`type` is "constant").
        self.dtype: type = cp.float32  #: Data type for generated times.
        self.seed = None

    @property
    def seed(self):
        return self._seed
    
    @seed.setter
    def seed(self, a_seed):
        self.rng = cp.random.default_rng(cp.random.Philox4x3210(a_seed))
        self._seed = a_seed
    
    @property
    def type(self) -> str:
        """
        str
            The distribution type ("uniform" or "constant").
        """
        return self.__type

    @type.setter
    def type(self, dist_type: str):
        if dist_type not in self.__dists:
            raise ValueError(f"Time distribution '{dist_type}' not supported. Supported choices are {self.__dists}")
        self.__type = dist_type

    def generate(self, n: int) -> cp.ndarray:
        """
        Generates time samples based on the specified distribution.

        Parameters
        ----------
        n : int
            The number of samples to generate.

        Returns
        -------
        sample : ndarray
            An array of generated time samples.

        Raises
        ------
        NotImplementedError
            If the distribution type is not recognized.
        """
        if self.__type == 'uniform':
            sample = self.rng.uniform(self.tmin, self.tmax, size=n, dtype=self.dtype)
        elif self.__type == 'constant':
            sample = cp.full((n,), self.t0, dtype=self.dtype)
        else:
            raise NotImplementedError(f"Distribution {self.__type} is not yet implemented.")
        return sample

class Source():
    """Represents a photon source.
    By default a point-like source at zenith is generated. Photons are generated at a point (0, 0, 100) m in the local reference frame. 

    Parameters
    ----------
    telescope : IACT | None, optional
        The IACT object associated with this source. If None, the source is assumed to be at a fixed position defined by `self.positions.position`.
        Otherwise, a point-like source is generated as a uniform disk, at a coordinates (0, 0, 100) m in the local reference frame, with a radius big enough to illimunate the aperture of the telescope.
        
    dtype : type, optional
        The desired data type for generated quantities, by default np.float32.
    """
    def __init__(self, telescope: Optional['IACT'] = None, dtype: type = np.float32):
        self._tel: 'IACT' | None = telescope

        self.spectrum: Spectrum = Spectrum('uniform')  #: Photon wavelengths generator.
        self.spectrum.dtype = dtype

        self.arrival_times: TimeDistribution = TimeDistribution('constant')  #: Photon arrival times generator.
        self.arrival_times.dtype = dtype
        
        self.positions: AbstractPhotonPositions = PointLikePos([0,0,1e5]) #: Photon positions generator.

        self.directions: AbstractPhotonDirections = PointLikeDir(90,0) #: Photon directions generator.

        if telescope is not None:
            # On axis source by default
            self.directions.altitude = telescope.pointing[0]
            self.directions.azimuth = telescope.pointing[1]
            # Uniform disk by default
            radii = [s.half_aperture for s in self._tel.optical_system if hasattr(s, 'half_aperture')]
            # Relative distance 
            radial_position = [np.sqrt(s.position[0]**2+s.position[1]**2) for s in self._tel.optical_system if hasattr(s, 'position')]
            rmax = 2.*max(radii) if len(radii)>0 else 4000.
            if len(radial_position)>0:
                rmax += 2.*max(radial_position) 
            self.positions = UniformDisk(0, rmax)
            self.set_target()
    
    
    def set_target(self, target_surface: str | int | None = None, distance: float = 1e5):
        """Adjust source position to match the center of a target surface.
        If the target surface is not specified it is assumed to be the telescope position.

        Parameters
        ----------
        target_surface : int or str, optional
            Name or index of the surface in the telescope optical system, by default the telescope position is assumed as the target.
        distance : float
            Source-target distance in mm.
        """
        if self._tel is None:
            raise(RuntimeError('Source must be linked to a telescope when initialized in order to set a target.'))
        
        if target_surface is None:
            target = self._tel
        else:
            target = self._tel.optical_system[target_surface]
        
        source_central_dir = self.directions.altitude, self.directions.azimuth

        # Set source origin position in order to point the target
        p = cp.array(target.position)
        central_dir = -pointing_dir(*source_central_dir)
        p0 = p - cp.asarray(distance*central_dir)
        self.positions.position = p0

        # Get the position of the target in the local reference frame
        p = target.position @ local_to_telescope_rotation(*self._tel.pointing).T + self._tel.position
        p = cp.asarray(p)

        # Get the direction of the source
        central_dir = pointing_dir(*source_central_dir)

        # Center the source on the target
        p0 = p + cp.asarray(distance*central_dir)
        self.positions.position = p0

        # Rotate position into the source direction
        # N.B. extracted position are rotated and then translated into p0
        self.positions.rotation = local_to_pointing_rotation(self.directions.altitude, self.directions.azimuth).T

    def generate(self, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Generate *n* photons.

        Parameters
        ----------
        n : int
            Number of photons to generate.

        Returns
        -------
        ps, vs, wls, ts: tuple of ndarrays
            Position, direction, wavelength and arrival time of photons.
        """
        
        ps = self.positions.generate(n)
        # Non-random source can generate a lower number of photons
        if ps.shape[0] != n:
            n = ps.shape[0]
        vs = self.directions.generate(n)
        wls = self.spectrum.generate(n)
        ts = self.arrival_times.generate(n)
        return ps, vs, wls, ts
    
    def visualize(self, n_photons: int = 1000, opacity=0.1, length=None, show_hits=True, show_rays=True, resolution=10.):
        """VTK visualization of the source.

        Parameters
        ----------
        n_photons : int, optional
            Number of photons to generate, by default 1000.
        opacity : float, optional
            Ray opacity, by default 0.1
        opacity : float, optional
            Transparency of the rays from 0.0 (invisible) to 1.0 (opaque). 
            Default is 0.5.
        length : float, optional
            If provided, rays that not intersects the telescope will be drawn with this length using the direction vector.
        resolution : float, optional
            Objects mesh resolution (in mm). By default 10 mm.
        
        Raises
        ------
        RuntimeError
            If the source is not linked to a telescope.
        """
        # Import vtk here, so we are not force to add it to the package requirements
        from ...visualization._vtk_optical_system import VTKOpticalSystem

        if self._tel is None:
            raise RuntimeError('Source must be linked to a telescope when initialized in order to visualize it.')
        
        # Transform every surface into a sensitive one
        old_types = []
        for s in self._tel.optical_system:
            old_types.append(s.type)
            s.type = SurfaceType.TEST_SENSITIVE
        self._tel.cuda_init()

        # Generate photons and trace them into the telescope
        ps, vs, wls, ts = self.generate(n_photons)
        ps_start = ps.get()
        vs_start = vs.get()
        self._tel.trace_photons(ps, vs, wls, ts, trace_onto_camera=False)
        ps_stop = ps.get()

        # TEST_SENSITIVE returns the hit position into the telescope reference system
        # transform into the local reference system
        ps_stop = ps_stop @ local_to_telescope_rotation(*self._tel.pointing).T - self._tel.position

        # VTK renderer
        renderer = VTKOpticalSystem(self._tel, resolution=resolution)
        renderer.add_rays(ps_start, ps_stop, opacity=opacity, length=length, directions=vs_start, show_hits=show_hits, show_rays=show_rays)
        renderer.start_render()

        # Reset the surface types
        for s,s_type in zip(self._tel.optical_system, old_types):
            s.type = s_type
        self._tel.cuda_init()