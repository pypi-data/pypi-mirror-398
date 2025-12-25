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

from pathlib import Path
import time
from typing import Union, Dict, Any
import yaml
import random

import matplotlib.pyplot as plt
import numpy as np
import cupy as cp
from tqdm.auto import tqdm

from ...electronics._camera_geometry import SiPMCameraGeometry
from ...electronics._camera import CherenkovSiPMCamera
from ...electronics._waveforms import Waveform
from ...electronics._pde import PhotonDetectionEfficiency
from ...electronics.signals.discriminator_signals._disciminator_kernels import (
    last_trigger_time_counter_from_camera_trigger,
    count_pixel_triggers
)
from ...electronics.signals.trigger_logic._trigger_kernels import (
    topological_camera_trigger,
    count_topological_camera_triggers
)
from ...electronics.signals.sampling_signals import digitize
from ...electronics.sources._poisson_flash import generate_poisson_flash

from ...io._path_loader import PathLoader

class AstriCameraGeometry(SiPMCameraGeometry):
    """ASTRI camera geometry class.

    See Also
    --------
        :py:class:`iactsim.electronics.SiPMCameraGeometry`: 
    """
    # Number of pdms per row
    _rows = np.array([3, 5, 7, 7, 7, 5, 3])

    # Maxium number of pdm in a row
    _max_per_row = np.max(_rows)

    #_pdms_below[i] is the number of pdms below the row i
    _pdms_below = np.append(np.array([0]), np.cumsum(_rows))

    # Total number of pdm
    _number_of_pdm = _pdms_below[-1]

    # Number of pixels per PDM side
    _n_pix_pdm = 8

    def __init__(self):
        super().__init__()

        # TODO: should it be used?
        self.position = np.array([0,0,0])
        """Position of the center of the central SiPM module (PDM 19) in the focal surface reference system."""

        self.pixels_separation = 0.225

        self.pixel_active_side = 6.95
    
    @property
    def body_dimensions(self):
        return np.asarray([0,0,0])
    
    @property
    def position(self):
        return self.__position
    
    @position.setter
    def position(self, p):
        self.__position = p
        self.__pdms_p, self.__pdms_n = self.pdms_position_and_rotation()
    
    @property
    def modules_p(self):
        return self.__pdms_p

    @property
    def modules_n(self):
        return self.__pdms_n

    @property
    def module_side(self):
        return self.pixel_active_side*self._n_pix_pdm + (self._n_pix_pdm-1)*self.pixels_separation

    @property
    def pixel_active_side(self):
        return self._pixel_active_side
    
    @pixel_active_side.setter
    def pixel_active_side(self, a_side):
        self._pixel_active_side = a_side

    @property
    def pixels_separation(self):
        return self._pixels_separation

    @pixels_separation.setter
    def pixels_separation(self, a_sep):
        self._pixels_separation = a_sep
    
    def pdmid_to_indices(self, k):
        # Out of range check
        if k<1 or k>self._number_of_pdm: 
            return None, None
        for j in range(len(self._rows)): 
            # Check if the pdm is in the row j
            if k <= self._pdms_below[j+1]:
                # Position of the pdm k starting from the first pdm of the row
                on_row_pos = k - self._pdms_below[j] - 1
                # Missing pdms at the beginning of the row
                n_missing = int((self._max_per_row - self._rows[j])/2)
                # Column i
                i = on_row_pos + n_missing
                return i, j

    def pdms_position_and_rotation(self):
        """Compute and return ASTRI photon detection modules position and normal vector with respect to the focal surface reference system."""
        positions = np.empty((37,3), dtype=np.float64)

        pdm_angular_sep = 3.1945 # degree
        for pdm in range(1,38):
            i, j = self.pdmid_to_indices(pdm)
            # signs and optical axis orientation:
            # (0,0,1) -> beta +, gamma -
            # (0,0,-1) -> beta -, gamma +
            beta = pdm_angular_sep * (i-7//2) * np.pi/180.
            gamma = - pdm_angular_sep * (j-7//2) * np.pi/180.

            sb = np.sin(beta)
            cb = np.cos(beta)
            sg = np.sin(gamma)
            cg = np.cos(gamma)

            # Rotate x then rotate y
            R = np.asarray(
                [
                    [    cb,  0,     sb],
                    [ sg*sb, cg, -sg*cb],
                    [-sb*cg, sg,  cb*cg]
                ]
            )
            
            # PDM position with origin on the focal plane sphere center
            positions[pdm-1] = R.dot([0,0,1060.])
        
        # Normal direction of the PDM surface
        directions = positions/np.linalg.norm(positions,axis=-1)[:,np.newaxis]
        
        # Move PDMs to the camera reference frame (origin at the center of PDM 19)
        positions[:,0] += self.position[0]
        positions[:,1] += self.position[1]
        positions[:,2] += self.position[2] - 1060.
        
        return positions, directions

class AstriCherenkovCamera(CherenkovSiPMCamera):
    """
    ASTRI Cherenkov camera class.

    See Also
    --------
        :py:class:`iactsim.electronics.CherenkovCamera`:
        :py:class:`iactsim.electronics.CherenkovSiPMCamera`:
    """
    _left_asic = np.asarray([0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19, 24, 25, 26, 27, 32, 33, 34, 35, 40, 41, 42, 43, 48, 49, 50, 51, 56, 57, 58, 59])
    _right_asic = np.asarray([4, 5, 6, 7, 12, 13, 14, 15, 20, 21, 22, 23, 28, 29, 30, 31, 36, 37, 38, 39, 44, 45, 46, 47, 52, 53, 54, 55, 60, 61, 62, 63])

    def __init__(
            self,
        ):
        trigger_channels = [0]
        sampling_channels = [1,2]
        geometry = AstriCameraGeometry()
        waveforms = [Waveform()]*4
        channels_time_resolution = [1,1,1,1]
        pde = PhotonDetectionEfficiency()
        n_pixels = 2368

        # Initialize the base class
        super().__init__(
            n_pixels,
            waveforms,
            trigger_channels,
            sampling_channels,
            channels_time_resolution,
            pde,
            geometry,
        )        

        self.channels_gain[0] = cp.full((self.n_pixels,), 1., dtype=cp.float32)
        self.channels_gain[1] = cp.full((self.n_pixels,), 100, dtype=cp.float32)
        self.channels_gain[2] = cp.full((self.n_pixels,), 10, dtype=cp.float32)
        self.channels_gain[3] = self.channels_gain[0]

        # "Time" discriminator
        self.threshold_1 = cp.full((self.n_pixels,), 3, cp.float32)
        self.threshold_1_offset = cp.zeros((self.n_pixels,), dtype=cp.float32)
        self.n_contiguous = 5
        self.discriminator1_signals = None
        self.discriminator1_time_over_threshold = 1 # ns
        
        # Sampling info
        self.enable_peak_detection = True
        # ADCs baseline
        self.hg_adc_offset = cp.full((self.n_pixels,), 2**13, dtype=cp.float32)
        self.lg_adc_offset = cp.full((self.n_pixels,), 2**13, dtype=cp.float32)
        # ADCs noise
        self.hg_adc_noise = cp.full((self.n_pixels,), 10, dtype=cp.float32)
        self.lg_adc_noise = cp.full((self.n_pixels,), 2, dtype=cp.float32)
        self.adc_resolution = 14
        # Peak detection window extent
        self.sampling_window_extent = [45.,45.]
        # Time delay between a PDM triger and the peak-detector activation
        self.sampling_delay = [32., 32.]

        self.auxiliary_delay = [-128.]
        self.auxiliary_window_extent = [256.]

        self.peak_detection_window_extent = 32.

        self.sigma_ucells = np.full((self.n_pixels,), 0.01) 
        self.cross_talk = np.full((self.n_pixels,), 0.03)
        
        # Extend the trigger window by the trigger waveform peaking time
        self.trigger_window_end_offset = 30.

        # Calibration system
        self.blue_laser_illumination = cp.full((self.n_pixels,), 2, cp.float32)
        self.green_laser_illumination = cp.full((self.n_pixels,), 2, cp.float32)
        self.dark_rate = cp.full((self.n_pixels,), 0.001, cp.float32)

        # Seed
        self.increment_seed = True

        # Data
        self._peak_time_hg = cp.empty((self.n_pixels,), dtype=cp.float32)
        self._peak_time_lg = cp.empty((self.n_pixels,), dtype=cp.float32)
        self._peak_amplitude_hg = cp.empty((self.n_pixels,), dtype=cp.float32)
        self._peak_amplitude_lg = cp.empty((self.n_pixels,), dtype=cp.float32)
        self._trigger_time = []
        self._triggered_pdm = []
        self._pixel_trigger_time = []
        self._high_gain = []
        self._low_gain = []

        self.register_pixel_trigger_time = True

        self.show_progress = False
        
        self.restart()

        self.threshold = 3

    def restart(self):
        super().restart()
        self._event_counter = 0
        self._high_gain = []
        self._low_gain = []
        self._trigger_time = []
        self._triggered_pdm = []
        self._pixel_trigger_time = []
        self.timer.clear()

        left = self._left_asic
        right = self._right_asic
        self.pe_to_dac = cp.empty((37,64), dtype=cp.float32)
        peq = self.channels_gain[0].reshape(37,64)
        for k in range(37):
            k_peq = peq[k]
            self.pe_to_dac[k,left] = cp.nanmedian(k_peq[left])
            self.pe_to_dac[k,right] = cp.nanmedian(k_peq[right])

    @property
    def peak_detection_window_extent(self):
        return self._peak_detection_window_extent
    
    @peak_detection_window_extent.setter
    def peak_detection_window_extent(self, a_extent):
        # clock maxium delay
        dt = 1e3/200. + 1e3/300.
        self.sampling_window_extent[0] = a_extent + dt
        self.sampling_window_extent[1] = a_extent + dt
        self._peak_detection_window_extent = a_extent

    @property
    def threshold(self):
        return self._threshold

    @threshold.setter
    def threshold(self, pe):
        """Compute the disciminator thresholds for a given global threshold.
        That is, performs the so-called pe-to-DAC conversion.

        Parameters
        ----------
        pe : float
            Global threshold in photo-electrons.
        """
        self.threshold_1 = cp.round_(pe*self.pe_to_dac)
        self._threshold = pe

    @property
    def triggered_pdm(self):
        if len(self._triggered_pdm) == 0:
            return None
        else:
            return np.asarray(self._triggered_pdm)

    @property
    def high_gain(self):
        if len(self._high_gain) == 0:
            return None
        else:
            return np.stack([hg.get() for hg in self._high_gain])

    @property
    def low_gain(self):
        if len(self._low_gain) == 0:
            return None
        else:
            return np.stack([lg.get() for lg in self._low_gain])

    @property
    def pixel_trigger_time(self):
        if len(self._pixel_trigger_time) == 0:
            return None
        else:
            return np.stack([tt.get() for tt in self._pixel_trigger_time])

    @property
    def adc_resolution(self):
        return self._adc_resolution

    @adc_resolution.setter
    def adc_resolution(self, a_res):
        self._adc_max_value = cp.int32(2**a_res-1)
        self._adc_resolution = a_res
    
    @property
    def threshold_1(self):
        return self._threshold_1

    @threshold_1.setter
    def threshold_1(self, thrs):
        if not isinstance(thrs, cp.ndarray):
            thrs = cp.asarray(thrs, dtype=cp.float32)
        self._threshold_1 = thrs

    @property
    def hg_adc_noise(self):
        return self._hg_adc_noise

    @hg_adc_noise.setter
    def hg_adc_noise(self, noise):
        if not isinstance(noise, cp.ndarray):
            noise = cp.asarray(noise, dtype=cp.float32)
        self._hg_adc_noise = noise

    @property
    def hg_adc_offset(self):
        return self._hg_adc_offset

    @hg_adc_offset.setter
    def hg_adc_offset(self, offset):
        if not isinstance(offset, cp.ndarray):
            offset = cp.asarray(offset, dtype=cp.float32)
        self._hg_adc_offset = offset

    @property
    def lg_adc_noise(self):
        return self._lg_adc_noise

    @lg_adc_noise.setter
    def lg_adc_noise(self, noise):
        if not isinstance(noise, cp.ndarray):
            noise = cp.asarray(noise, dtype=cp.float32)
        self._lg_adc_noise = noise

    @property
    def lg_adc_offset(self):
        return self._lg_adc_offset

    @lg_adc_offset.setter
    def lg_adc_offset(self, offset):
        if not isinstance(offset, cp.ndarray):
            offset = cp.asarray(offset, dtype=cp.float32)
        self._lg_adc_offset = offset
        
    def trigger_action(self):
        """Generate a camera trigger.
        """
        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t0 = time.time()
            self.timer.add_section('trigger_action')
            
        self.discriminator1_signals = self.apply_ideal_discriminator_to_channel(
            0,
            self.threshold_1,
            self.threshold_1_offset,
            self.discriminator1_time_over_threshold/self.channels_time_resolution[0]
        )

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t1 = time.time()
            self.timer.add_entry('trigger_action', 'discriminator', t1-t0)
        
        n_pdms = len(self.geometry.modules_p)
        
        pdm_dimension = cp.int32(self.geometry.module_side/ self.geometry.pixel_active_side)
        window_size = cp.int32(len(self.time_windows[0]))
        n_contiguous = cp.int32(self.n_contiguous)
        self.pdms_trigger_signals = cp.empty((n_pdms,len(self.time_windows[0])), dtype=cp.float32)
        trigger_t_idices = cp.empty((n_pdms,), dtype=cp.int32)
        trigger = cp.empty((2,), cp.int32)

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t2 = time.time()
            self.timer.add_entry('trigger_action', 'copy to device', t2-t1)

        trigger_args = (
            self.discriminator1_signals,
            n_contiguous,
            self.pdms_trigger_signals,
            trigger_t_idices,
            trigger,
            window_size,
            pdm_dimension,
            cp.int32(n_pdms),
            self.seed[0]
        )
        topological_camera_trigger((n_pdms,), (128,), trigger_args)

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t3 = time.time()
            self.timer.add_entry('trigger_action', 'camera trigger', t3-t2)
        
        t_index, pdm_id = trigger.get()
        if t_index >= 0:
            self.triggered = True
            self.trigger_time = self.time_windows[0][t_index]
            self._triggered_pdm.append(pdm_id+1) # count from 1 to match the usual ID
            self._trigger_time.append(self.trigger_time)
        else:
            self.trigger_time = None

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t4 = time.time()
            self.timer.add_entry('trigger_action', 'copy to host', t4-t3)
    
    def sampling_action(self):
        """Perform peak detection and pixels trigger time measurement.
        """
        dt = np.random.uniform(0, 1e3/200 + 1e3/300)
        self._t0_peak_detection_hg = self.trigger_time + self.sampling_delay[0] + dt
        self._t0_peak_detection_lg = self.trigger_time + self.sampling_delay[1] + dt

        if self.enable_peak_detection:
            extent_hg = self.peak_detection_window_extent
            extent_lg = self.peak_detection_window_extent
            self.apply_peak_detection_to_channel(self._peak_amplitude_hg, self._peak_time_hg, 1, self._t0_peak_detection_hg, extent_hg)
            self.apply_peak_detection_to_channel(self._peak_amplitude_lg, self._peak_time_lg, 2, self._t0_peak_detection_lg, extent_lg)
        else:
            t_slice_hg = np.abs(self.time_windows[1] - self._t0_peak_detection_hg).argmin()
            t_slice_lg = np.abs(self.time_windows[2] - self._t0_peak_detection_lg).argmin()
            self._peak_amplitude_hg = self.get_channel_signals(1,reshape=True)[:,t_slice_hg].flatten()
            self._peak_amplitude_lg = self.get_channel_signals(2,reshape=True)[:,t_slice_lg].flatten()
        
        dig_hg = cp.empty((self.n_pixels,), dtype=cp.uint16)
        hg_args = (
            dig_hg,
            self._peak_amplitude_hg,
            self.hg_adc_offset,
            self.hg_adc_noise,
            self.seed,
            self._adc_max_value,
            cp.int32(self.n_pixels),
            cp.int32(1)
        )
        dig_lg = cp.empty((self.n_pixels,), dtype=cp.uint16)
        lg_args = (
            dig_lg,
            self._peak_amplitude_lg,
            self.lg_adc_offset,
            self.lg_adc_noise,
            self.seed,
            self._adc_max_value,
            cp.int32(self.n_pixels),
            cp.int32(1)
        )
        
        digitize((self.n_pixels,),(32,),hg_args)
        digitize((self.n_pixels,),(32,),lg_args)

        self._high_gain.append(dig_hg)
        self._low_gain.append(dig_lg)

        ## Trigger time
        if self.register_pixel_trigger_time:
            tt = cp.empty((self.n_pixels,), dtype=cp.int32)
            self.compute_signals([3])
            self._time_discriminator_signals = self.apply_ideal_discriminator_to_channel(
                3,
                self.threshold_1,
                self.threshold_1_offset,
                self.discriminator1_time_over_threshold/self.channels_time_resolution[3]
            )
            delay = 128. + self.auxiliary_delay[0]
            cam_trigger_clock = cp.int32((np.abs(self.time_windows[3] - (self.trigger_time+delay))).argmin())
            stop_clock = cp.int32(128)
            register_n_bits = cp.int32(8)
            wsize = len(self.time_windows[3])
            n_pixels = cp.int32(self.n_pixels)
            n_threads = self._number_of_threads(wsize)
            last_trigger_time_counter_from_camera_trigger(
                (self.n_pixels,),
                (n_threads,),
                (
                    tt,
                    self._time_discriminator_signals,
                    cam_trigger_clock,
                    stop_clock,
                    register_n_bits,
                    cp.int32(wsize), 
                    n_pixels
                ),
                shared_mem=4*(wsize+n_threads)
            )
            self._pixel_trigger_time.append(tt)

    def acquire_pedestal(self, n_frame):
        """Acquire pulse-height distribution with an external trigger and the current background.

        Parameters
        ----------
        n_frame : int
            number of frame to be acquired.
        """
        self.restart()

        # Save current configuration
        old_enable_camera_trigger = self.enable_camera_trigger
        old_fixed_windows = self.fixed_time_windows

        # Pedestal configuration
        self.trigger_time = 0
        self.enable_camera_trigger = False
        self.fixed_time_windows = True
        self.time_windows = [
            np.asarray([0],dtype=np.float32),
            np.arange(self.sampling_delay[0], self.sampling_delay[0]+self.sampling_window_extent[0], self.channels_time_resolution[1], dtype=np.float32),
            np.arange(self.sampling_delay[1], self.sampling_delay[1]+self.sampling_window_extent[1], self.channels_time_resolution[2], dtype=np.float32),
            np.arange(-128, 128., self.channels_time_resolution[3], dtype=np.float32),
        ]
        
        # Pedestal
        for i in tqdm(range(n_frame), disable=not self.show_progress):
            self.simulate_response(source=None)

        # Restore old configuration (not windows)
        self.enable_camera_trigger = old_enable_camera_trigger
        self.fixed_time_windows = old_fixed_windows
    
    def acquire_variance(self, n_sample):
        """Acquire variance data.

        Parameters
        ----------
        n_frame : int
            number of frame to be acquired.
        """
        self.restart()

        # Save current configuration
        old_fixed_windows = self.fixed_time_windows

        # Pedestal configuration
        self.trigger_time = 0
        self.fixed_time_windows = True
        self.time_windows = [
            np.asarray([0],dtype=np.float32),
            np.asarray([0],dtype=np.float32),
            np.asarray([0],dtype=np.float32),
            np.asarray([0],dtype=np.float32),
        ]
        
        # Pedestal
        self.source = None
        for _ in tqdm(range(n_sample), disable=not self.show_progress):
            self.compute_signals(self.sampling_channels)
            dig_hg = cp.empty((self.n_pixels,), dtype=cp.uint16)
            hg_args = (
                dig_hg,
                self.get_channel_signals(1),
                self.hg_adc_offset,
                self.hg_adc_noise,
                self.seed,
                self._adc_max_value,
                cp.int32(self.n_pixels),
                cp.int32(1)
            )
            dig_lg = cp.empty((self.n_pixels,), dtype=cp.uint16)
            lg_args = (
                dig_lg,
                self.get_channel_signals(2),
                self.lg_adc_offset,
                self.lg_adc_noise,
                self.seed,
                self._adc_max_value,
                cp.int32(self.n_pixels),
                cp.int32(1)
            )
            digitize((self.n_pixels,),(32,),hg_args)
            digitize((self.n_pixels,),(32,),lg_args)

            self._high_gain.append(dig_hg)
            self._low_gain.append(dig_lg)

            self.seed += self.n_pixels

        # Restore old configuration (not windows)
        self.fixed_time_windows = old_fixed_windows
    
    def acquire_dark_pedestal(self, n_frame):
        """Acquire pulse-height distribution with an external trigger and the closed lids background.

        Parameters
        ----------
        n_frame : int
            number of frame to be acquired.
        """
        old_background = self.background_rate.copy()
        self.background_rate = self.dark_rate

        self.acquire_pedestal(n_frame)

        self.background_rate = old_background

    def acquire_phd(self, n_frame):
        """Acquire pulse-height distribution with pulsed flash light.

        Parameters
        ----------
        n_frame : int
            number of frame to be acquired.
        """
        self.restart()
        
        # Save current configuration
        old_enable_camera_trigger = self.enable_camera_trigger
        old_fixed_windows = self.fixed_time_windows
        old_background = self.background_rate.copy()

        # PHD configuration
        self.background_rate = self.dark_rate
        self.enable_camera_trigger = True
        self.fixed_time_windows = True
        self.time_windows = [
            np.arange(0,  64, self.channels_time_resolution[0], np.float32),
            np.arange(0, 256, self.channels_time_resolution[1], np.float32),
            np.arange(0, 256, self.channels_time_resolution[2], np.float32),
            np.arange(0, 256, self.channels_time_resolution[3], np.float32),
        ]
        for i in tqdm(range(n_frame), disable=not self.show_progress):
            source = generate_poisson_flash(self.n_pixels, self.blue_laser_illumination, 0, 10, seed=None)
            self.simulate_response(source)

        # Restore previous configuration (but not time windows)
        self.enable_camera_trigger = old_enable_camera_trigger
        self.fixed_time_windows = old_fixed_windows
        self.background_rate = old_background
    
    def threshold_scan(self, start, stop, step, window_extent=1024., max_duration=1e-3, maximum_count=None, background=None):
        """Measure the camera trigger rate as a function of the trigger threshold.

        Parameters
        ----------
        start : float
            Start threshold value.
        stop : float
            Stop threshold value.
        step : float
            Threshold step.
        window_extent : float, optional
            Extent in ns of the time window where to count triggers, by default 1024 ns.
        max_duration : float, optional
            Integration time (in seconds) for each threshold, by default 1e-3 s.
        maximum_count : int, optional
            Stop when at least ``maximum_count`` triggers have been found at a each threshold, useful to speed-up the procedure at lower thresholds. By default None.

        Returns
        -------
        (numpy.ndarray,numpy.ndarray,numpy.ndarray,numpy.ndarray)
            Thresholds and corresponding rate, rate error and integration time. Integration times can be different for each threshold if a ``maximum_count`` is provided.
        """
        # Save current configuration
        old_fixed_windows = self.fixed_time_windows
        old_threshold = self.threshold
        
        self.restart()
        self.fixed_time_windows = True
        self.time_windows = [
            np.arange(0, window_extent, 10./3, np.float32),
            np.arange(0, 32, 1, np.float32),
            np.arange(0, 32, 1, np.float32),
            np.arange(0, 32, 1, np.float32),
        ]
        window_size = self.time_windows[0].shape[0]

        # Allow signals to be computed with no source
        self.source = None

        update_background = False
        if background is not None:
            if background.ndim == 1:
                self.background_rate = cp.asarray(background)
            elif background.ndim == 2 and len(background) == (stop-start)//step+1:
                update_background = True
                background = cp.asarray(background)
            else:
                raise ValueError("`background` must be a 1D or 2D array. If 2D the shape must be (n_thresholds, n_pixels).")

        max_iterations = int(max_duration/window_extent*1e9)
        thresholds = np.arange(start, stop+step, step, dtype=np.float32)
        trigger_rate = cp.zeros(thresholds.shape, dtype=cp.int32)
        integration_time = np.zeros(thresholds.shape, dtype=np.float32)
        n_threads = self._number_of_threads(window_size)

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t_old = time.time()
            self.timer.add_section('trigger_scan')

        for i in tqdm(range(max_iterations), disable=not self.show_progress):
            self.compute_signals([0])
            for j in range(len(thresholds)):
                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t_th_0 = time.time()

                # Skip if there are enough count at this threshold
                if maximum_count is not None:
                    if trigger_rate[j] > maximum_count:
                        continue

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t_th_1 = time.time()
                    self.timer.add_entry('trigger_scan', f'thr {thresholds[j]}: check rate', t_th_1 - t_th_0)

                # Set the threshold
                self.threshold = thresholds[j]
                if update_background:
                    self.background_rate = background[j]

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t_th_2 = time.time()
                    self.timer.add_entry('trigger_scan', f'thr {thresholds[j]}: set threshold and nsb', t_th_2 - t_th_1)

                # Get triggers
                self.trigger_action()

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t_th_3 = time.time()
                    self.timer.add_entry('trigger_scan', f'thr {thresholds[j]}: trigger action', t_th_3 - t_th_2)
                
                # Initialize count
                cam_trigger_counts = cp.zeros((1,), dtype=cp.int32)
                args = [
                    cam_trigger_counts,
                    self.pdms_trigger_signals,
                    cp.int32(window_size),
                    cp.int32(37)
                ]
                # Count triggers
                count_topological_camera_triggers((1,), (n_threads,), args, shared_mem=4*(window_size+n_threads))

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t_th_4 = time.time()
                    self.timer.add_entry('trigger_scan', f'thr {thresholds[j]}: count triggers', t_th_4 - t_th_3)

                integration_time[j] += window_extent / 1e9
                trigger_rate[j] += cam_trigger_counts[0]

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t_th_5 = time.time()
                    self.timer.add_entry('trigger_scan', f'thr {thresholds[j]}: update counts', t_th_5 - t_th_4)

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t_new = time.time()
                    self.timer.add_entry('trigger_scan', f'thr {thresholds[j]}', t_new-t_old)
                    t_old = t_new

            self.seed = self.seed + self.n_pixels
            self._event_counter += 1
        
        # Restore previous configuration (but not time windows)
        self.fixed_time_windows = old_fixed_windows
        self.threshold = old_threshold

        # Compute rate and erros
        integration_time = np.asarray(integration_time)
        trigger_rate = trigger_rate.get()
        error = np.sqrt(trigger_rate) / integration_time
        trigger_rate = trigger_rate / integration_time
        return thresholds, trigger_rate, error, integration_time

    def acquire_stairs(self, start, stop, step, integration_time=0.001, window_extent=1024.):
        """Acquire staircase curves (pixel dark trigger rate as a function of threshold).

        Parameters
        ----------
        start : float
            Start threshold value.
        stop : float
            Stop threshold value.
        step : float
            Threshold step.
        integration_time : float, optional
            Integration time (in seconds), by default 0.001 s
        window_extent : float, optional
            Extent in ns of the time window where to count triggers, by default 1024 ns.

        Returns
        -------
        (numpy.ndarray, numpy.ndarray)
            Thresholds and corresponding trigger rate per pixel.
        """
        old_background = self.background_rate.copy()
        old_fixed_windows = self.fixed_time_windows

        self.background_rate = self.dark_rate

        self.timer.clear()
        self.restart()
        self.fixed_time_windows = True
        self.time_windows = [
            np.arange(0, window_extent, 10./3., np.float32),
            np.arange(0, 32, 1, np.float32),
            np.arange(0, 32, 1, np.float32),
        ]
        window_size = self.time_windows[0].shape[0]
        
        # Allow signals to be computed with no source
        self.source = None
        
        thrs = np.arange(start, stop+step, step)
        tr_counts = cp.zeros((self.n_pixels,len(thrs)), dtype=np.int32)
        n_iterations = int(integration_time*1e9/window_extent)
        for _ in tqdm(range(n_iterations), disable=not self.show_progress):
            self.compute_signals([0])
            for i,thr in enumerate(thrs):
                counts = cp.zeros((self.n_pixels,), dtype=cp.int32)
                threshold = cp.full((self.n_pixels,), thr, dtype=cp.float32)
                disc_signals = self.apply_ideal_discriminator_to_channel(
                    0,
                    threshold,
                    self.threshold_1_offset,
                    self.discriminator1_time_over_threshold/self.channels_time_resolution[0]
                )
                count_pixel_triggers((self.n_pixels,),(128,),(counts,disc_signals,cp.int32(window_size),cp.int32(self.n_pixels)),shared_mem=4*(window_size+128))
                tr_counts[:,i] += counts
            self.seed += self.n_pixels
            self._event_counter += 1
        
        self.background_rate = old_background
        self.fixed_time_windows = old_fixed_windows

        return thrs, tr_counts.get()

    def measure_pixel_trigger_rate(self, integration_time=0.01, window_extent=1024.):
        old_fixed_windows = self.fixed_time_windows

        self.timer.clear()
        self.restart()

        self.fixed_time_windows = True
        self.time_windows = [
            np.arange(0, window_extent, 10./3., np.float32),
            np.arange(0, 32, 1, np.float32),
            np.arange(0, 32, 1, np.float32),
            np.arange(0, 32, 1, np.float32),
        ]
        window_size = self.time_windows[0].shape[0]
        tr_counts = cp.zeros((self.n_pixels,), dtype=np.int32)
        n_iterations = int(integration_time*1e9/window_extent)
        for _ in tqdm(range(n_iterations), disable=not self.show_progress):
            self.compute_signals([0])
            counts = cp.zeros((self.n_pixels,), dtype=cp.int32)
            self.discriminator1_signals = self.apply_ideal_discriminator_to_channel(
                0,
                self.threshold_1,
                self.threshold_1_offset,
                self.discriminator1_time_over_threshold/self.channels_time_resolution[0]
            )
            count_pixel_triggers((self.n_pixels,),(128,),(counts,self.discriminator1_signals,cp.int32(window_size),cp.int32(self.n_pixels)),shared_mem=4*(window_size+128))
            tr_counts[...] += counts
            self.seed = self.seed + self.n_pixels
            self._event_counter += 1
        
        self.fixed_time_windows = old_fixed_windows

        return tr_counts.get()/integration_time

    def configure(self, config: Union[str, Path, Dict[str, Any]]) -> None:
        """Configure the camera with a yaml configuration file or a dictionary.

        Parameters
        ----------
        config : str, path-like, or dict
            Path to the configuration file (str or pathlib.Path),
            or a dictionary containing the configuration.
        """

        if isinstance(config, (str, Path)):
            with open(config, 'r') as file:
                cam_conf = yaml.load(file, Loader=PathLoader)
        elif isinstance(config, dict):
            cam_conf = config
        else:
            raise TypeError(
                "config must be a string (path), pathlib.Path, or a dictionary, "
                f"not {type(config)}"
            )
        
        if 'waveforms' in cam_conf and cam_conf['waveforms'] is not None:
            waveforms = []
            for file in cam_conf['waveforms']:
                x, y = np.loadtxt(file).T
                wave = Waveform(x, y, 'AC')
                wave.normalize()
                waveforms.append(wave)
            self.waveforms = waveforms

        if 'pde' in cam_conf and cam_conf['pde'] is not None:
            data = np.loadtxt(cam_conf['pde']).T
            wl = data[0,:]
            pde = data[1,:]
            self.pde.value = pde
            self.pde.wavelength = wl

        if 'channels_gain' in cam_conf:
            for i,gain in enumerate(cam_conf['channels_gain']):
                if gain is not None:
                    if isinstance(gain, (int,float)):
                        array = cp.full((self.n_pixels,), gain, dtype=cp.float32)
                    else:
                        array = cp.loadtxt(gain, dtype=cp.float32)
                    if array.size != self.n_pixels:
                        raise(ValueError(f"Channel {i} gain: wrong number of values provided ({array.size}). Provide a single value or a value for each pixel ({self.n_pixels})."))
                    self.channels_gain[i] = array.flatten()

        if 'timer' in cam_conf and cam_conf['timer'] is not None:
            self.timer.active = cam_conf['timer']

        if 'seed' in cam_conf and cam_conf['seed'] is not None:
            seed = cam_conf['seed']
        else:
            seed = random.getrandbits(64)
        
        self.seed = cp.arange(0, self.n_pixels, 1, dtype=cp.uint64) + seed

        assign_directly = [
            'trigger_channels',
            'trigger_window_end_offset',
            'trigger_window_start_offset',
            'sampling_channels',
            'sampling_delay',
            'sampling_window_extent',
            'peak_detection_window_extent',
            'channels_time_resolution',
            'auxiliary_delay',
            'auxiliary_window_extent',
            'adc_resolution',
            'discriminator1_time_over_threshold',
            'register_pixel_trigger_time',
            'increment_seed',
            'show_progress',
            # 'threshold' # Must be assigned after after channels_gain[0] and threshold1_offset
        ]

        check_is_value = [
            'hg_adc_noise',
            'hg_adc_offset',
            'lg_adc_noise',
            'lg_adc_offset',
            'cross_talk',
            'sigma_ucells',
            'pixel_mask',
            'background_rate',
            'dark_rate',
            'blue_laser_illumination',
            'green_laser_illumination',
            'threshold_1_offset'
        ]

        for name in cam_conf.keys():
            value = cam_conf[name]
            if value is not None:
                if name in check_is_value:
                    dtype =cp.float32
                    if name == 'pixel_mask':
                        dtype = cp.int32
                    if isinstance(value, (int,float)):
                        array = cp.full((self.n_pixels,), value, dtype=dtype)
                    else:
                        array = cp.loadtxt(value, dtype=dtype)
                    if array.size != self.n_pixels:
                        raise(ValueError(f"{name}: wrong number of values provided ({array.size}). Provide a single value or a value for each pixel ({self.n_pixels})."))
                    setattr(self, name, array.flatten())
                if name in assign_directly:
                    setattr(self, name, value)

        # Set trigger channels info then set the threshold
        self.restart()

        if 'threshold' in cam_conf and cam_conf['threshold'] is not None:
            self.threshold = cam_conf['threshold']
        
        

    def plot_pixel_trigger_channel(self, pdm, pixel, ax=None):
        if ax is None:
            ax = plt.gca()
        pix = pixel - 1
        pdm = pdm - 1
        window = self.time_windows[0]
        gain = self.channels_gain[0][pix].get()
        signal = self.get_channel_signals(0, True)[64*pdm:64*(pdm+1)][pix].get()/gain
        disc_signal = self.discriminator1_signals.reshape(37,64,-1)[pdm,pix].get()*self.threshold_1[pdm,pix].get()/gain
        
        if self.register_pixel_trigger_time:
            window = self.time_windows[3]
            gain = self.channels_gain[3][pix].get()
            signal = self.get_channel_signals(3, True)[64*pdm:64*(pdm+1)][pix].get()/gain
            disc_signal = self._time_discriminator_signals.reshape(37,64,-1)[pdm,pix].get()*self.threshold_1[pdm,pix].get()/gain
        
        ax.plot(window, signal, ls='-', lw=2, label='Fast signal')
        ax.plot(window, disc_signal, ls='-', lw=1, color='black', label='Pixel Trigger')

        if self.triggered or not self.enable_camera_trigger:
            ax.vlines(self.trigger_time, signal.min(), signal.max(), color='black', ls='--', label='Camera Trigger')

        ax.hlines(self.threshold_1[pdm,pix].get()/gain, window[0], window[-1], ls='--', color='grey', label='Trigger threshold')

        ax.set_ylim(signal.min(), signal.max())
        
        ax.legend(title=f'PDM {pdm+1} Pixel {pix+1}')
        ax.grid(which='both')
    
    def plot_pdm_pixels_trigger_channel(self, pdm):
        from ...visualization._sipm_camera_plots import plot_sipm_module_pixels

        def plotf(pix):
            self.plot_pixel_trigger_channel(pdm, pix+1)
        
        plot_sipm_module_pixels(self, plotf, 5)

    def plot_pixel_sampling_channels(self, pdm, pixel, ax=None):
        if ax is None:
            ax = plt.gca()
        
        if self.enable_camera_trigger and not self.triggered:
            return

        pix = pixel - 1
        pdm = pdm - 1
        hg_window = self.time_windows[1]
        lg_window = self.time_windows[2]
        hg_signal = self.get_channel_signals(1, True)[64*pdm:64*(pdm+1)][pix].get()/self.channels_gain[1][pix].get()
        lg_signal = self.get_channel_signals(2, True)[64*pdm:64*(pdm+1)][pix].get()/self.channels_gain[2][pix].get()
        
        
        hg_plot = ax.plot(hg_window, hg_signal, label='HG signal')
        lg_plot = ax.plot(lg_window, lg_signal, label='LG signal')

        ymin = min(hg_signal.min(),lg_signal.min())
        ymax = max(hg_signal.max(),lg_signal.max())

        ax.set_ylim(ymin,ymax)
    
        if self.enable_peak_detection:
            t0 = self._t0_peak_detection_hg
            t1 = t0 + self.peak_detection_window_extent
            ax.fill_between(x=[t0,t1], y1=[ymin,ymin], y2=[ymax,ymax], color='grey', interpolate=True, alpha=0.2, label='PD interval')
            hg = self._peak_amplitude_hg[pdm*64+pix].get()/self.channels_gain[1][pix].get()
            lg = self._peak_amplitude_lg[pdm*64+pix].get()/self.channels_gain[2][pix].get()
            ax.hlines(hg, hg_window[0], hg_window[-1], color=hg_plot[0].get_color(), ls='--')
            ax.hlines(lg, lg_window[0], lg_window[-1], color=lg_plot[0].get_color(), ls='--')
            
        ax.legend(title=f'PDM {pdm+1} Pixel {pix+1}', framealpha=0.5)
        ax.grid(which='both')
    
    def plot_pdm_pixels_sampling_channels(self, pdm):
        from ...visualization._sipm_camera_plots import plot_sipm_module_pixels

        def plotf(pix):
            self.plot_pixel_sampling_channels(pdm, pix+1)
        
        plot_sipm_module_pixels(self, plotf, 5)