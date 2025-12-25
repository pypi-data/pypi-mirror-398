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

import time
from typing import (
    Tuple, List, 
    Union, Optional
)

import cupy as cp
import numpy as np
from tqdm.auto import tqdm
import random

from .optics._optical_system import OpticalSystem
from .optics.utils._aspheric_coeffs import normalize_aspheric_coefficients
from .optics._cpu_transforms import local_to_telescope_rotation, photon_to_local_rotation
from .optics._surface_misc import SurfaceShape
from .optics._atmosphere import AtmosphericTransmission
from .optics._materials import Materials
from .optics import ray_tracing

from .electronics import CherenkovCamera, CherenkovSiPMCamera

from .utils._timer import BenchmarkTimer


class IACT:
    """A class to represent an Imaging Atmospheric Cherenkov Telescope (IACT).

    This class serves as a wrapper for a CUDA-accelerated backend. It handles the conversion 
    of optical system and camera information into CuPy ndarrays (transferring data to the GPU), 
    and arranges this data in a format suitable for input to the CUDA kernels that perform the 
    actual simulation.

    Parameters
    ----------
    optical_system : OpticalSystem
        An instance of a class derived from :py:class:`OpticalSystem` representing the 
        telescope optical system.
    camera : CherenkovCamera
        An instance of a class derived from :py:class:`CherenkovCamera` representing the 
        telescope Cherenkov camera.
    position : Tuple[float, float, float] | List[float] | numpy.ndarray
        The Cartesian coordinates (x, y, z) representing the telescope 
        position in millimeters. Can be a tuple, list, or NumPy array.
    pointing : Tuple[float, float] | List[float] | numpy.ndarray
        The horizontal coordinates (altitude, azimuth) representing the 
        telescope pointing direction in degrees. Can be a tuple, list, 
        or NumPy array.    
    
    Raises
    ------
    TypeError
        
        - If optical_system is not an instance of :py:class:`OpticalSystem` or a derived class.
        - If camera is not an instance of :py:class:`CherenkovCamera` or a derived class.

    ValueError
        
        - If position does not have 3 elements.
        - If pointing does not have 2 elements.

    """

    def __init__(
        self,
        optical_system: OpticalSystem,
        camera: CherenkovCamera = None,
        position: Tuple[float, float, float] | List[float] | np.ndarray = (0.,0.,0.),
        pointing: Tuple[float, float] | List[float] | np.ndarray = (0,0),
    ):
        if not isinstance(optical_system, OpticalSystem):
            raise TypeError("optical_system must be an instance of OpticalSystem or a derived class")

        # Validate and convert position to NumPy array
        if not isinstance(position, (tuple, list, np.ndarray)) or len(position) != 3:
            raise ValueError("position must be a tuple, list, or NumPy array of length 3")

        self._cuda_tracing_args = [None] * 5 # ray-tracing kernel related arguments
        self._cuda_atmosphere_args = [None] * 5 # atmosphere transmission related arguments
        self._cuda_materials_args = [None] * 5 # materials refractive index args
        
        self._position = np.asarray(position)

        self.pointing = pointing

        self._optical_system = optical_system
        self._camera = camera

        self.atmospheric_transmission = AtmosphericTransmission()

        # Benchmark
        self.timer = BenchmarkTimer()
        self.timer.add_section('simulate_response')

        self.show_progress = False

    @property
    def position(self) -> np.ndarray:
        """
        numpy.ndarray: The telescope position in Cartesian coordinates (x, y, z) 
                    in millimeters.
        """
        return self._position

    @position.setter
    def position(self, value: Tuple[float, float, float] | List[float] | np.ndarray):
        if not isinstance(value, (tuple, list, np.ndarray)) or len(value) != 3:
            raise ValueError("position must be a tuple, list, or NumPy array of length 3")
        self._position = np.asarray(value)
        self._cuda_telescope_init()

    @property
    def pointing(self) -> np.ndarray:
        """
        numpy.ndarray: The telescope pointing direction in horizontal 
                    coordinates (altitude, azimuth) in degrees.
        """
        return self._pointing

    @pointing.setter
    def pointing(self, value: Tuple[float, float] | List[float] | np.ndarray):
        if not isinstance(value, (tuple, list, np.ndarray)) or len(value) != 2:
            raise ValueError("pointing must be a tuple, list, or NumPy array of length 2")
        self._pointing = np.asarray(value)
        self._altitude = value[0]
        self._azimuth = value[1]
        self._cuda_telescope_init()
    
    @property
    def altitude(self) -> float:
        """
        float: Telescope pointing altitude (0-90).
        """
        return self._altitude
    
    @altitude.setter
    def altitude(self, value: float):
        if value < 0 or value > 90:
            raise(ValueError('Telescope pointing altitude must be between 0 (horizon) and 90 (zenith) degrees.'))
        self._altitude = value
        self._pointing[0] = value
        self._cuda_telescope_init()

    @property
    def azimuth(self) -> float:
        """
        float: Telescope pointing azimuth (0-360).
        """
        return self._azimuth
    
    @azimuth.setter
    def azimuth(self, value: float):
        if value < 0 or value > 360:
            raise(ValueError('Telescope pointing azimuth must be between 0 and 360 degrees (increasing from north to east).'))
        self._azimuth = value
        self._pointing[1] = value
        self._cuda_telescope_init()
    
    @property
    def optical_system(self) -> OpticalSystem:
        """
        OpticalSystem: The telescope optical system
        """
        return self._optical_system
    
    @property
    def camera(self) -> CherenkovCamera:
        """
        CherenkovCamera: The telescope Cherenkov camera.
        """
        return self._camera

    @camera.setter
    def camera(self, a_camera):
        if a_camera is not None and not isinstance(a_camera, CherenkovCamera):
            raise TypeError("camera must be an instance of CherenkovCamera or a derived class")
        self._camera = a_camera

    def _cuda_telescope_init(self):
        # Position and rotation to transform into the telescope reference frame
        telescope_rot = cp.asarray(local_to_telescope_rotation(*self.pointing), dtype=cp.float32)
        telescope_pos = cp.asarray(self.position, dtype=cp.float32)
        
        self._cuda_tracing_args[0] = telescope_pos
        self._cuda_tracing_args[1] = telescope_rot
    
    def _cuda_surfaces_init(self):
        """Prepares optical surface data for CUDA-based ray tracing.

        This function extracts relevant properties from the optical surfaces
        defined in :py:attr:`optical_system` and converts them into CuPy arrays.
        """

        NUM_ASPHERIC_COEFFS = 10
        ROT_MATRIX_SIZE = 9

        surface_data_dtype = np.dtype([
            ('position',              np.float32, 3),                   # 12 bytes
            ('_pad1',                 np.uint8,   4),                   # ! Padding to align 'offset' (float2) to 8 bytes (12+4=16)
            ('offset',                np.float32, 2),                   # 8 bytes (starts at 16)
            ('rotation_matrix',       np.float32, ROT_MATRIX_SIZE),     # 36 bytes (starts at 24)
            ('curvature',             np.float32),                      # 4 bytes (starts at 60)
            ('conic_constant',        np.float32),                      # 4 bytes (starts at 64)
            ('aspheric_coefficients', np.float32, NUM_ASPHERIC_COEFFS), # 40 bytes (starts at 68, ends at 108)
            ('_pad2',                 np.uint8,   4),                   # ! Padding to align 'aperture_size' to 112
            ('aperture_size',         np.float32, 2),                   # 8 bytes (starts at 112)
            ('aperture_shape',        np.int32,   2),                   # 8 bytes
            ('flags',                 np.bool_,   2),                   # 2 bytes
            # align=True will automatically handle the 2-byte padding needed here for 'type' (int)
            ('type',                  np.int32),                        # 4 bytes
            ('shape',                 np.int32),                        # 4 bytes
            ('material_before',       np.int32),                        # 4 bytes
            ('material_after',        np.int32),                        # 4 bytes
            ('scattering_dispersion', np.float32)                       # 4 bytes
        ], align=True)

        n_surfaces = len(self.optical_system)

        h_surfaces = np.zeros(n_surfaces, dtype=surface_data_dtype)

        for i, surface in enumerate(self.optical_system):
            if surface._shape == SurfaceShape.ASPHERICAL:
                h_surfaces[i]['offset'] = np.asarray(surface.offset, dtype=np.float32)
                h_surfaces[i]['curvature'] = np.float32(surface.curvature)
                h_surfaces[i]['conic_constant'] = np.float32(surface.conic_constant)
                surface_asph_coeffs = normalize_aspheric_coefficients(surface.aspheric_coefficients, surface.half_aperture)
                for j in range(len(surface_asph_coeffs)):
                    h_surfaces[i]['aspheric_coefficients'][j] = np.float32(surface_asph_coeffs[j])
                h_surfaces[i]['aperture_size'][0] = np.float32(surface.half_aperture)
                h_surfaces[i]['aperture_size'][1] = np.float32(surface.central_hole_half_aperture)
                h_surfaces[i]['aperture_shape'][0] = np.int32(surface.aperture_shape.value)
                h_surfaces[i]['aperture_shape'][1] = np.int32(surface.central_hole_shape.value)
                h_surfaces[i]['flags'][0] = np.bool_(surface.is_fresnel)
                h_surfaces[i]['flags'][1] = np.bool_(surface.is_fresnel)
            elif surface._shape == SurfaceShape.CYLINDRICAL:
                h_surfaces[i]['aperture_size'][0] = np.float32(surface.radius)
                h_surfaces[i]['aperture_size'][1] = np.float32(surface.height)
                h_surfaces[i]['flags'][0] = np.bool_(surface.top)
                h_surfaces[i]['flags'][1] = np.bool_(surface.bottom)
            else:
                raise(ValueError(f"Surface shape '{surface._shape}' ray-tracing not yet implemented."))
            
            h_surfaces[i]['position'] = np.asarray(surface.position, dtype=np.float32)
            h_surfaces[i]['rotation_matrix'] = np.asarray(surface.get_rotation_matrix().flatten(), dtype=np.float32)
            h_surfaces[i]['type'] = np.int32(surface.type.value)
            h_surfaces[i]['shape'] = np.int32(surface._shape.value)
            h_surfaces[i]['material_before'] = np.int32(surface.material_in.value)
            h_surfaces[i]['material_after'] = np.int32(surface.material_out.value)
            h_surfaces[i]['scattering_dispersion'] = np.float32(surface.scattering_dispersion/180.)
        
        self._cuda_tracing_args[2] = cp.asarray(h_surfaces.view(np.uint8), dtype=cp.uint8)

    def _cuda_surfaces_efficiency_init(self):
        optical_tables_dtype = np.dtype([
            ('transmittance_front', np.uint64),
            ('reflectance_front',   np.uint64),
            ('transmittance_back',  np.uint64),
            ('reflectance_back',    np.uint64),
            ('inv_dwl',       np.float32),
            ('start_wl',      np.float32),
            ('inv_dang',      np.float32),
            ('start_ang',     np.float32)
        ], align=True)
        
        n_surfaces = len(self.optical_system)
        h_optical_tables = np.zeros(n_surfaces, dtype=optical_tables_dtype)
        self._surface_textures = [] # keep a reference to the textures to avoid garbage collection
        for k,s in enumerate(self.optical_system):
            surface_prop = s.properties
            if surface_prop is None or not surface_prop.is_defined:
                continue
            opt_textures = surface_prop.get_optical_textures()
            self._surface_textures.append(opt_textures)
            h_optical_tables[k]['transmittance_front'] = opt_textures.transmittance.ptr
            h_optical_tables[k]['reflectance_front'] = opt_textures.reflectance.ptr
            h_optical_tables[k]['transmittance_back'] = opt_textures.transmittance_back.ptr
            h_optical_tables[k]['reflectance_back'] = opt_textures.reflectance_back.ptr
            h_optical_tables[k]['inv_dwl'] = opt_textures.wavelength_inv_step
            h_optical_tables[k]['start_wl'] = opt_textures.wavelength_start
            h_optical_tables[k]['inv_dang'] = opt_textures.angle_inv_step
            h_optical_tables[k]['start_ang'] = opt_textures.angle_start
        
        self._cuda_tracing_args[3] = cp.asarray(h_optical_tables.view(np.uint8), dtype=cp.uint8)

    def _cuda_materials_init(self):
        """Prepares materials data for CUDA-based ray tracing.
        This function extracts relevant properties from all defined materials.
        """
        # Refractive indices
        refractive_tables_dtype = np.dtype([
            ('texture',  np.uint64),
            ('inv_dwl',  np.float32),
            ('start_wl', np.float32)
        ], align=True)

        n_materials = sum(1 for _ in Materials._members())

        h_refractive_tables = np.zeros(n_materials, dtype=refractive_tables_dtype)

        self._ri_textures = [] # keep a reference to the textures to avoid garbage collection
        for material in Materials._members():
            material_texture = material.get_refractive_index_texture()
            self._ri_textures.append(material_texture)
            h_refractive_tables[material.value]['texture'] = material_texture.texture.ptr
            h_refractive_tables[material.value]['inv_dwl'] = material_texture.wavelength_inv_step
            h_refractive_tables[material.value]['start_wl'] = material_texture.wavelength_start

        self._cuda_tracing_args[4] = cp.asarray(h_refractive_tables.view(np.uint8), dtype=cp.uint8)

    def _cuda_sipm_camera_geometry_init(self):
        # Number of modules
        n_pmds = len(self.camera.geometry.modules_n)
        # Modules rotation
        modules_r = np.empty((n_pmds*9,), dtype=np.float32)

        for i in range(n_pmds):
            modules_r[i*9:(i+1)*9] = photon_to_local_rotation(self.camera.geometry.modules_n[i]).flatten()

        self._trace_onto_sipm_modules_args = [ 
            cp.asarray(self.camera.geometry.modules_p, dtype=cp.float32),
            cp.asarray(modules_r, dtype=cp.float32),
            cp.float32(0.5*self.camera.geometry.module_side),
            cp.float32(self.camera.geometry.pixel_active_side),
            cp.float32(self.camera.geometry.pixels_separation),
            cp.int32(8),
            cp.int32(self.camera.geometry.modules_p.shape[0]),
        ]

        # Photon detection efficiency
        pde_curve = self.camera.pde
        wl = pde_curve.wavelength
        value = pde_curve.value
        if pde_curve is not None and wl is not None and value is not None:
            if np.any(value>1) or np.any(value<0):
                raise(ValueError('Photon detection efficiency must be between 0 and 1.'))
            if len(wl) != len(value):
                raise(ValueError('Photon detection efficiency value array and wavelength array must have the same number of elements.'))
            self._trace_onto_sipm_modules_args += [
                cp.asarray(wl, dtype=cp.float32),
                cp.asarray(value, dtype=cp.float32),
                cp.int32(len(wl)),
                cp.float32(1./(wl[1]-wl[0])),
            ]
        else:
            self._trace_onto_sipm_modules_args += [
                cp.empty((0,), dtype=cp.float32),
                cp.empty((0,), dtype=cp.float32),
                cp.int32(0),
                cp.float32(0.),
            ]
        
        # TODO: for now assume focal plane is surrounded only by AIR
        # find a way to easly expose this to the user
        # Keep a reference to avoid garbage collection
        self._fp_surroundingmaterial = Materials.AIR.get_refractive_index_texture()
        self._trace_onto_sipm_modules_args += [
            cp.uint64(self._fp_surroundingmaterial.texture.ptr),
            cp.float32(self._fp_surroundingmaterial.wavelength_inv_step),
            cp.float32(self._fp_surroundingmaterial.wavelength_start)
        ]

    def _cuda_atmosphere_init(self):
        if self.atmospheric_transmission.value is not None:
            wl = self.atmospheric_transmission.wavelength
            zem = self.atmospheric_transmission.altitude
            self._cuda_atmosphere_args[:] = [
                cp.asarray(self.atmospheric_transmission.value, dtype=cp.float32),
                cp.asarray(wl, dtype=cp.float32),
                cp.asarray(zem, dtype=cp.float32),
                cp.asarray([len(wl), len(zem)], dtype=cp.int32),
            ]
                
    def cuda_init(self):
        """Build and copy to device all the CUDA kernels input related to the optical configuration."""

        self._cuda_surfaces_init()

        self._cuda_materials_init()

        self._cuda_telescope_init()

        self._cuda_surfaces_efficiency_init()

        if isinstance(self.camera, CherenkovSiPMCamera):
            self._cuda_sipm_camera_geometry_init()

        self._cuda_atmosphere_init()

        self._d_num_surfaces = cp.int32(len(self.optical_system))

    # TODO: revise _trace_onto_sipm_modules_args:
    #   - split it into sub-arg lists
    #   - init each-sub arg at run-time when a parameter is modified
    def trace_photons(self,
            positions: Union[np.ndarray, cp.ndarray],
            directions: Union[np.ndarray, cp.ndarray],
            wavelengths: Union[np.ndarray, cp.ndarray],
            arrival_times: Union[np.ndarray, cp.ndarray],
            emission_altitudes: Optional[Union[np.ndarray, cp.ndarray]] = None,
            events_mapping: Union[np.ndarray, list] = None,
            *,
            photons_per_bunch: int = 1,
            simulate_camera = False,
            min_n_pes = 1,
            trace_onto_camera: bool = True,
            get_camera_input: bool = False,
            max_bounces=100,
            save_last_bounce=False,
            reset_state=True,
            seed: Optional[int] = None,
        ):
        """Traces the paths of photons through the telescope optical system and optionally simulates the Cherenkov camera response.

        This function simulates the propagation of photons through an optical system,
        taking into account their initial positions, directions, wavelengths, and arrival times.
        It can optionally:
        
          - model the effects of atmospheric transmission based on emission altitudes;
          - simulate the Cherenkov camera response.

        Each element in the input arrays can represent either a single photon or a "bunch" of photons.
        The ``photons_per_bunch`` parameter determines how many photons are represented by each element.
        If ``photons_per_bunch`` > 1, it is assumed that all photons within a bunch share the same
        initial position, direction, wavelength, and arrival time.

        Parameters
        ----------
        positions : Union[numpy.ndarray, cp.ndarray] of shape (N, 3)
            Initial Cartesian coordinates (x, y, z) of the photon bunches in millimeters (mm).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        directions : Union[numpy.ndarray, cp.ndarray] of shape (N, 3)
            Initial direction vectors (vx, vy, vz) of the photon bunches.
            These should be normalized. Must be either a NumPy (CPU) or CuPy (GPU) array.
        wavelengths : Union[numpy.ndarray, cp.ndarray] of shape (N,)
            Wavelengths of the photon bunches in nanometers (nm).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        arrival_times : Union[numpy.ndarray, cp.ndarray] of shape (N,)
            Arrival times of the photon bunches at their respective positions in nanoseconds (ns).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        emission_altitudes : Optional[Union[numpy.ndarray, cp.ndarray]], optional
            Emission altitudes of the photon bunches in millimeters (mm).
            This is used to calculate atmospheric transmission effects if enabled.
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        events_mapping : numpy.ndarray or list
            A NumPy array of shape (N+1,) to split the photons in to groups corresponding to N different events when 
            generating the camera input arrays.
            ``events_mapping[i]`` indicates the starting index in ``positions`` for the i-th event.
            ``events_mapping[i+1]`` indicates the ending index (exclusive) in ``positions`` for the i-th event.
            Therefore, photons belonging to event i are located in ``positions[events_mapping[i]:events_mapping[i+1], :]``.
            The last element of events_mapping must be equal to the number of photons.
        photons_per_bunch : int, optional
            Number of photons represented by each element in the input arrays. If 1, each element represents a single photon.
            If > 1, each element represents a bunch of photons that share the same properties, by default 1. Maximum value is 65535.
        simulate_camera : bool, optional
            Whether to simulate the response of the telescope Cherenkov camera.
        min_n_pes : int, optional
            Minimum number of photo-electrons needed to trigger a camera simulation (if ``simulate_camera`` is True). By default 1.
        trace_onto_camera : bool, optional
            Whether to trace photons into camera pixels (if a camera is definined). It is set to True if ``simulate_camera`` is True.
            By default True.
        get_camera_input : bool, optional
            Wheter to return the input for camera simulation (i.e. photon arrival times for each pixel) as CuPy ndarrays.
            By default False.
        max_bounces : int, optional
            Maxium number of bounces before the photon is killed. By default 100.
        save_last_bounce : float, optional
            Keep the position at the last bounce. Only for ray tracing visualization. By default False.
        reset_state : bool, optional
            Keep the ID of the last surface reached without re-initialize the _d_weights array. Only for ray tracing visualization. By default True.
        seed : int, optional
            Base seed of the simulation. If None a random seed will be used. By default None.

        Returns
        -------
        ndarray
            List of triggered events index. If ``simulate_camera`` is True and ``get_camera_input`` is False.
        tuple(cp.ndarray, cp.ndaray)
            Input CuPy arrays for :py:meth:`CherenkovCamera.simulate_response()`` method. If ``simulate_camera`` is False and ``get_camera_input`` is True.
        tuple(cp.ndarray, cp.ndaray, np.ndarray)
            Input CuPy arrays for :py:meth:`CherenkovCamera.simulate_response()`` method and the list of triggered events index. If ``simulate_camera`` is True and ``get_camera_input`` is True.

        Warning
        -------
            The input arrays can be either CuPy or NumPy ndarray. In the former case arrays are modified in place.
            In the latter case the arrays are copied to the device and can be accessed through the following attributes:

              - self._d_directions
              - self._d_positions
              - self._d_wavelengths
              - self._d_arrival_times
              - self._d_emission_altitudes
              - self._d_weights
        
        Warning
        -------
            Telescope configuration must be copied into the device before calling this method. Use the :py:meth:`cuda_init()` method.

        Notes
        -----

          - The ray-tracing operates with positions in mm, wavelengths in nm, and times in ns. It also handles photon bunches,
            where each thread may process multiple photons if ``photons_per_bunch`` > 1. In this case is assumed 
            that each element of the input arrays represents a bunch of photons that share the same 
            initial position, direction, wavelength, and arrival time. The arrays will maintain this
            structure, with each element representing the updated properties of a photon bunch, but the bunch size may
            be reduced throught the ray-tracing due to the interacrtion with optical elements, atmosphere and pixels.

        """
        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t0 = time.time()

        blocksize = 256  # Threads per block
        n_photons = positions.shape[0] # Number of input elements
        num_blocks = int(np.ceil(n_photons / blocksize))
        d_num_photons = cp.int32(n_photons)

        self._d_arrival_times = cp.asarray(arrival_times, dtype=cp.float32)
        self._d_directions = cp.asarray(directions, dtype=cp.float32)
        self._d_positions = cp.asarray(positions, dtype=cp.float32)
        self._d_wavelengths = cp.asarray(wavelengths, dtype=cp.float32)

        if emission_altitudes is not None:
            self._d_emission_altitudes = cp.asarray(emission_altitudes, dtype=cp.float32)

        # This step can be skipped for visualization purposes. Since when save_last_bounce is True 
        # The last surface ID is stored in the last 16 bit of each element in _d_weights.
        # Initialize photon bunches size on device
        if reset_state:
            self._d_weights = cp.full((n_photons,), photons_per_bunch, dtype=cp.int32)

        if seed is None:
            seed = random.getrandbits(63)

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t1 = time.time()
            self.timer.add_entry('simulate_response', 'copy to device', t1-t0)
        
        # Optional atmospheric transmission calculation
        if self.atmospheric_transmission.value is not None and emission_altitudes is not None:
            ray_tracing.atmospheric_transmission(
                (num_blocks,), 
                (blocksize,),
                (
                    self._d_positions,
                    self._d_directions,
                    self._d_wavelengths,
                    self._d_arrival_times,
                    self._d_weights, 
                    self._d_emission_altitudes,
                    *self._cuda_atmosphere_args,
                    d_num_photons,
                    cp.uint64(seed)
                )
            )

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t2 = time.time()
            self.timer.add_entry('simulate_response', 'atmospheric transmission', t2-t1)

        # Perform ray tracing on GPU
        ray_tracing.ray_tracing(
            (num_blocks,),
            (blocksize,),
            (
                self._d_positions,
                self._d_directions,
                self._d_wavelengths,
                self._d_arrival_times,
                self._d_weights,
                *self._cuda_tracing_args,
                self._d_num_surfaces,
                d_num_photons,
                cp.int32(max_bounces),
                cp.bool_(save_last_bounce),
                cp.uint64(seed+1)
            ),
            shared_mem = len(self.optical_system) * 4
        )

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t3 = time.time()
            self.timer.add_entry('simulate_response', 'trace onto focal plane', t3-t2)

        # Trace onto SiPM camera
        if (trace_onto_camera or simulate_camera) and issubclass(type(self.camera), CherenkovSiPMCamera):
            # The id of the pixel the photon reaches
            self._d_pixid = cp.empty((n_photons,), dtype=cp.int32)
            ray_tracing.trace_onto_sipm_modules(
                (num_blocks,),
                (blocksize,),
                (
                    self._d_positions,
                    self._d_directions,
                    self._d_wavelengths,
                    self._d_arrival_times,
                    self._d_weights,
                    self._d_pixid,
                    d_num_photons,
                    *self._trace_onto_sipm_modules_args,
                    cp.uint64(seed+2)
                )
            )

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t4 = time.time()
                self.timer.add_entry('simulate_response', 'trace onto SiPM modules', t4-t3)

            # Build the input for `CherenkovCamera.simulate_response()` method
            if get_camera_input or simulate_camera:
                if events_mapping is None:
                    events_mapping = cp.asarray([0,n_photons], dtype=cp.int32)
                else:
                    events_mapping = cp.asarray(events_mapping, dtype=cp.int32)
                                
                n_events = len(events_mapping) - 1
                n_pixels = self.camera.n_pixels
                
                blocksize = 128
                nblock = int(np.ceil(n_events/blocksize))

                pix_counter = cp.zeros((n_events,n_pixels+1), dtype=cp.int32)
                counter = cp.zeros((n_photons,), dtype=cp.int32)
                gpu_ntot = cp.zeros((n_events+1,), dtype=cp.int32)
                ray_tracing.count_all_photons(
                    (nblock,),
                    (blocksize,),
                    (
                        self._d_weights,
                        self._d_pixid,
                        counter,
                        pix_counter,
                        events_mapping,
                        gpu_ntot,
                        cp.int32(n_pixels),
                        cp.int32(n_events)
                    )
                )

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t5 = time.time()
                    self.timer.add_entry('simulate_response', 'count pixel pes', t5-t4)
                
                ntot = cp.int32(np.sum(gpu_ntot.get(), dtype=np.int32))
                phs = cp.empty((ntot,), dtype=cp.float32)
                phs_mapping = cp.cumsum(pix_counter, dtype=cp.int32, axis=1)
                pe_mapping = cp.cumsum(gpu_ntot, dtype=cp.int32)
                ray_tracing.camera_inputs(
                    (nblock,),
                    (blocksize,),
                    (
                        phs,
                        phs_mapping,
                        self._d_arrival_times,
                        self._d_weights,
                        self._d_pixid,
                        counter,
                        pe_mapping,
                        events_mapping,
                        cp.int32(n_pixels),
                        cp.int32(n_events)
                    )
                )

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t6 = time.time()
                    self.timer.add_entry('simulate_response', 'generate camera input', t6-t5)

                if simulate_camera:
                    # Mapping onto the photo-electrons arrival time array (phs_mapping)
                    # Since phs_mapping contains the mapping for each individual event:
                    #    phs[event] -> phs_mapping[event]
                    # We need to add an offset to phs_mapping to take into account
                    # all the photons in the previous events in order to select a slice
                    # of phs that corresponds to a single event
                    phs_mapping_global = np.insert(np.cumsum(np.sum(np.diff(phs_mapping.get(),axis=1), axis=1)), 0, 0)
                    event_number = []
                    for i in tqdm(range(len(phs_mapping)), disable=not self.show_progress):
                        start_phs = phs_mapping_global[i]
                        end_phs = phs_mapping_global[i+1]
                        if end_phs-start_phs < min_n_pes:
                            continue
                        self.camera.simulate_response((phs[start_phs:end_phs], phs_mapping[i]))
                        if self.camera.triggered:
                            event_number.append(i)
                    
                    event_number = np.asarray(event_number)

                    if self.timer.active:
                        cp.cuda.stream.get_current_stream().synchronize()
                        t7 = time.time()
                        self.timer.add_entry('simulate_response', 'simulate camera response', t7-t6)

                    if get_camera_input:
                        return phs, phs_mapping, event_number
                    else:
                        return event_number
                
                if get_camera_input:
                    return phs, phs_mapping
    
    def visualize_ray_tracing(self,
            positions: Union[np.ndarray, cp.ndarray],
            directions: Union[np.ndarray, cp.ndarray],
            wavelengths: Union[np.ndarray, cp.ndarray],
            arrival_times: Union[np.ndarray, cp.ndarray],
            emission_altitudes: Optional[Union[np.ndarray, cp.ndarray]] = None,
            photons_per_bunch: int = 1,
            get_renderer = False,
            *,
            opacity=None,
            show_hits=True,
            show_rays=True, 
            point_size=1,
            orthographic=False,
            focal_point=None,
            resolution=10,
        ):
        """
        Visualizes the ray tracing process by performing step-by-step propagation of photons.

        This method initializes a VTK renderer and iteratively calls `trace_photons` with 
        `max_bounces=1` to capture and visualize the path of photons between surfaces.

        Parameters
        ----------
        positions : Union[numpy.ndarray, cp.ndarray] of shape (N, 3)
            Initial Cartesian coordinates (x, y, z) of the photon bunches in millimeters (mm).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        directions : Union[numpy.ndarray, cp.ndarray] of shape (N, 3)
            Initial direction vectors (vx, vy, vz) of the photon bunches.
            These should be normalized. Must be either a NumPy (CPU) or CuPy (GPU) array.
        wavelengths : Union[numpy.ndarray, cp.ndarray] of shape (N,)
            Wavelengths of the photon bunches in nanometers (nm).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        arrival_times : Union[numpy.ndarray, cp.ndarray] of shape (N,)
            Arrival times of the photon bunches at their respective positions in nanoseconds (ns).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        emission_altitudes : Optional[Union[numpy.ndarray, cp.ndarray]], optional
            Emission altitudes of the photon bunches in millimeters (mm).
            This is used to calculate atmospheric transmission effects if enabled.
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        photons_per_bunch : int, optional
            Number of physical photons represented by one simulated photon. Defaults to 1.
        get_renderer : bool, optional
            If True, returns the `VTKOpticalSystem` instance instead of starting the render loop immediately. 
            Defaults to False.
        opacity : float, optional
            Opacity of the ray lines (0.0 to 1.0). If None, it is calculated based on the number 
            of photons. Defaults to None.
        show_hits : bool, optional
            Whether to render points at the location where rays intersect surfaces. Defaults to True.
        show_rays : bool, optional
            Whether to render lines representing the photon paths. Defaults to True.
        point_size : int, optional
            Size of the points rendered at intersection hits. Defaults to 1.
        orthographic : bool, optional
            If True, start with a parallel projection. 
            If False, start with a Perspective projection. Default is False.
        focal_point : tuple, list, or str, optional
            If tuple/list: (x, y, z) coordinates to look at.
            If str: The name of the surface in self.os to look at.
            If None: Defaults to center of system.
        resolution : float, optional
            Objects mesh resolution (in mm). By default 10 mm.
        
        Returns
        -------
        VTKOpticalSystem or None
            Returns the renderer instance if `get_renderer` is True, otherwise returns None 
            after the render window is closed.
        """
        from .visualization._vtk_optical_system import VTKOpticalSystem
        
        positions = cp.asarray(positions, dtype=cp.float32)
        directions = cp.asarray(directions, dtype=cp.float32)
        wavelengths = cp.asarray(wavelengths, dtype=cp.float32)
        arrival_times = cp.asarray(arrival_times, dtype=cp.float32)
        emission_altitudes = cp.asarray(emission_altitudes, dtype=cp.float32) if emission_altitudes is not None else None

        old_wavelenth = wavelengths.copy()

        first_step = True

        renderer = VTKOpticalSystem(self, resolution=resolution)
        while True:
            ps_start = positions.get()
            self.trace_photons(
                positions,
                directions,
                wavelengths,
                arrival_times,
                emission_altitudes,
                photons_per_bunch=photons_per_bunch, 
                trace_onto_camera=False, 
                simulate_camera=False,
                max_bounces=1, 
                save_last_bounce=True,
                reset_state=first_step
            )
            ps_stop = positions.get()

            # Set opacity based on number of photons hitting a valid surface
            if opacity is None and first_step:
                n_ph_survived = cp.count_nonzero(cp.isfinite(wavelengths)).get()
                opacity = np.clip(50/n_ph_survived, 0., 1.) if n_ph_survived > 0 else 1.0
            
            first_step = False

            if np.array_equal(ps_start, ps_stop, equal_nan=True):
                break
            
            renderer.add_rays(ps_start, ps_stop, opacity=opacity, show_hits=show_hits, show_rays=show_rays, point_size=point_size)
        
        wavelengths[~cp.isnan(self._d_arrival_times)] = old_wavelenth[~cp.isnan(self._d_arrival_times)]

        if get_renderer:
            return renderer
        else:
            renderer.start_render(focal_point=focal_point, orthographic=orthographic)