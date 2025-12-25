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

from abc import ABC, abstractmethod
import random
import time
from typing import List, Union, Tuple

import cupy as cp
import numpy as np

from ._waveforms import Waveform
from._camera_geometry import SiPMCameraGeometry
from ._pde import PhotonDetectionEfficiency

from .signals.sipm_signals._sipm_kernels import (
    sipm_signals,
)

from .signals.discriminator_signals._disciminator_kernels import (
    ideal_discriminator,
)

from .signals.sampling_signals._sampling_kernels import (
    peak_detection,
)

from ..utils._timer import BenchmarkTimer

class CherenkovCamera(ABC):
    """Abstract class to simulate a Cherenkov camera. 

    Parameters
    ----------
    n_pixels : int
        Number of pixels.
    waveforms : Union[List[Waveform], Tuple[Waveform]]
        List of `Waveform` instances, one for each channel.
    trigger_channels : List[int]
        Trigger channels index.
    sampling_channels : List[int]
        Sampling channels index.
    channels_time_resolution : List[float]
        Time resolution of each channel.

    Notes
    -----
    **Random Seed Handling**

    The camera manages random number generation for stochastic processes (e.g.,
    cross-talk, background noise) on a per-pixel basis. The seed for each pixel
    is derived from a single ``uint64`` master seed, :py:attr:`base_seed`, to
    ensure reproducibility. This behavior is controlled by the following
    attributes:

    - :py:attr:`base_seed`: The master seed that can be set by the user for
      reproducibility. When this value is changed, the per-pixel seeds in
      :py:attr:`seed` are automatically updated.
    - :py:attr:`random_seed`: If ``True`` (default), a new random value for
      :py:attr:`base_seed` is generated at each :py:meth:`restart()` call.
      This ensures that different simulation runs are independent. When set to ``False``,
      :py:attr:`base_seed` is reset to 0.
    - :py:attr:`increment_seed`: If ``True`` (default), the :py:attr:`base_seed`
      is incremented by `n_pixels` after each :py:meth:`simulate_response()`
      call. This provides different random sequences for consecutive events
      within the same run.
    - :py:attr:`seed`: A CuPy array containing a unique seed for each pixel,
      derived from :py:attr:`base_seed`. This array is passed to the CUDA
      kernels.


    """
    def __init__(
        self,
        n_pixels: int,
        waveforms: Tuple[Waveform],
        trigger_channels: List[int],
        sampling_channels: List[int],
        channels_time_resolution: List[float],
    ):
        self.n_pixels = n_pixels #: Number of pixels.
        self.pixel_mask = cp.zeros((self.n_pixels,), dtype=cp.int32) #: Pixel mask. Pixel with value 1 are ignored.

        # Channels waveform
        self.n_channels = None #: Number of channels.
        self.waveforms = waveforms #: Single photo-electron waveform of each channel.

        # Split channels (to compute trigger signals first)
        self.trigger_channels = trigger_channels #: Trigger channels list.
        self.sampling_channels = sampling_channels #: Sampling channels list.

        self.auxiliary_channels = [] #: Auxiliary channels list.
        for i in range(self.n_channels):
            if i not in trigger_channels + sampling_channels:
                self.auxiliary_channels.append(i)
        
        # Channels time window
        self.time_windows = [None]*self.n_channels #: Time windows where to simulate the signal. One for each channel.
        self.fixed_time_windows = False #: Whether time windows should be computed for each event or assumed fixed.
        self.channels_time_resolution = channels_time_resolution #: Time resolution for each channel.

        # Modulate the amplitude of the waveforms for each pixel
        self.channels_gain = [cp.ones((self.n_pixels,), dtype=cp.float32) for _ in self.waveforms] #: Gain of each channel.

        # Input photo-electrons (discharges initiated by photons)
        self.source = None #: Input photo-electrons arrival times.

        # Signals
        self.signals = cp.asarray([]) #: Computed signals.

        # Dynamic time windows
        # (used if self.fixed_time_windows is False)
        # for every channel in self.sampling_channels
        self.sampling_delay = [0.]*len(self.sampling_channels) #: Delay of the sampling time windows with respect to the camera trigger. One for each sampling channel.
        self.sampling_window_extent = [0.]*len(self.sampling_channels) #: Sampling windows extent. One value for each sampling channel.
        self.auxiliary_delay = [0.]*len(self.auxiliary_channels) #: Delay of the auxiliary time windows with respect to the camera trigger. One for each auxiliary channel.
        self.auxiliary_window_extent = [0.]*len(self.auxiliary_channels) #: Auxiliary windows extent. One value for each auxiliary channel.
        self.trigger_window_start_offset = [0.]*len(self.trigger_channels) #: Trigger channels window start offset with respect to the first photo-electron arrival time in :py:attr:`source`.
        self.trigger_window_end_offset = [0.]*len(self.trigger_channels) #: Trigger channels window end offset with respect to the last photo-electron arrival time in :py:attr:`source`.

        # Trigger info
        self.enable_camera_trigger = True #: Whether to enable the camera trigger or skip directly to the sampling phase (in this case a trigger time must be provided).
        self.triggered = False #: Whether the camera has been triggered.
        self.trigger_time = None #: Time of the last trigger.

        # Seed
        self.seed = None #: Seed state, must be different for each pixel.
        self.increment_seed = True 
        """Whether to increment the seed at each :py:meth:`simulate_response()` call."""
        self.random_seed = True

        # Benchmark
        self.timer = BenchmarkTimer() #: Benchmark timer instance.
        self.timer.add_section('simulate_response')

        # Event counter
        self._event_counter = 0 #: Number of registered events.
        self._triggered_events = [] #: List of triggered events.

        self._adaptive_blocksize = True

    def restart(self):
        self._event_counter = 0
        self._triggered_events = []

    @property
    def random_seed(self):
        """Whether to set a random seed state at each :py:meth:`restart()` call."""
        return self._random_seed

    @random_seed.setter
    def random_seed(self, value: bool):
        self._random_seed = value
        if value:
            self.base_seed = random.getrandbits(63)
        else:
            self.base_seed = 0
    
    def _update_seed(self):
        """Create a unique seed for each pixel."""
        self.seed = cp.uint64(self.base_seed) + cp.arange(0, self.n_pixels, 1, dtype=cp.uint64)
    
    @property
    def base_seed(self):
        """Run-wise seed from wich per-pixel seeds are generated."""
        return self._base_seed
    
    @base_seed.setter
    def base_seed(self, value):
        self._base_seed = value
        self._update_seed()

    @staticmethod
    def _number_of_threads(window_size):
        return min([2**x for x in range(5, 11)], key=lambda x:abs(x-window_size/4))

    @property
    def triggered_events(self):
        return np.asarray(self._triggered_events, dtype=np.int32)

    @property
    def source(self):
        """Tuple containing:

              * *pes*: ndarray with shape (n_pe,) of photo-electron arrival times;
              * *mapping*: ndarray with shape (n_pixels+1,) of first and last arrival time position inside *pes* for each pixel.
            
            For instance:

              * discharge times on pixel 0 -> ``pes[mapping[0]:mapping[1]]``
              * discharge times on pixel n -> ``pes[mapping[n]:mapping[n+1]]``

            If None simulate only background.
        """
        return self._source

    @source.setter
    def source(self, a_source):
        if a_source is not None:
            t0s = cp.asarray(a_source[0], dtype=cp.float32)
            map_ = cp.asarray(a_source[1], dtype=cp.int32)
            a_source = (t0s, map_)
        else:
            a_source = (cp.asarray([], dtype=cp.float32), cp.zeros((self.n_pixels+1), dtype=cp.int32))
        self._source = a_source

    @property
    def waveforms(self):
        """List of `Waveform` instances, one for each channel.
        """
        return self._waveforms
    
    @waveforms.setter
    def waveforms(self, waves):
        waveforms_are_ok = False
        
        # Waveforms list must be immutable
        if isinstance(waves, list):
            waves = tuple(waves)
        
        if isinstance(waves, tuple):
            waveforms_are_ok = all([isinstance(wf, Waveform) for wf in waves])
        
        if not waveforms_are_ok:
            raise(ValueError("Waveforms must be provided as a tuple of `Waveform` instances."))

        if self.n_channels is None:
            self.n_channels = len(waves)
        else:
            if len(waves) != self.n_channels:
                raise(RuntimeError(f'The camera has been initialized with {self.n_channels} default waveforms, but you are providing {len(waves)} waveforms.'))
        self._waveforms = waves
        
        # In this way it is possible to set waveforms attribute later
        # in a custom configuration
        if any([w.amplitude is None for w in waves]):
            self._waveforms_are_initialized = False
            return

        self._waveforms_are_initialized = True
        
        self._max_wave_extent = max([wf.get_extent() for wf in self._waveforms])

        start_time = []
        texture_pointer = []
        inv_dt = []
        self._texture_waveform_objects = []
        for wave in self.waveforms:
            obj, inv_dx, start = wave.get_waveform_texture()
            self._texture_waveform_objects.append(obj)
            texture_pointer.append(obj.ptr)
            inv_dt.append(inv_dx)
            start_time.append(start)

        start_time = cp.asarray(start_time, dtype=cp.float32)
        inv_dt = cp.asarray(inv_dt, dtype=cp.float32)
        tex_handles_gpu = cp.asarray(texture_pointer, dtype=cp.uint64)

        self._waveforms_params = [
            tex_handles_gpu,
            inv_dt,
            start_time
        ]

    def get_channel_signals(self, channel, reshape=False):
        """Retrieves the signals for a specified channel.

        Parameters
        ----------
        channel : int
            The channel number for which to retrieve signals.
        reshape : bool, optional
            If True, reshapes the output array to have dimensions (n_pixels, number of time windows).
            If False, returns a 1D array. Default is False.

        Returns
        -------
        cp.ndarray
            A CuPy array containing the signals for the specified channel.  The shape of the array
            depends on the `reshape` parameter.

        Raises
        ------
        RuntimeError
            If the time window has not been defined for the specified channel.
        """
        if channel > self.n_channels or self.time_windows[channel] is None:
            raise(RuntimeError(f'Time window have not been defined for channel {channel}.'))
        windows_map = np.cumsum([0]+[len(w) for w in self.time_windows])
        signals_map = windows_map*self.n_pixels
        signals = self.signals[signals_map[channel]:signals_map[channel+1]]
        if reshape:
            signals = signals.reshape(self.n_pixels,windows_map[channel+1]-windows_map[channel])
        return signals

    def _get_time_windows_parameters(self):
        windows = np.concatenate(self.time_windows)
        windows_map = np.cumsum([0]+[len(w) for w in self.time_windows], dtype=np.int32)
        return [
            cp.asarray(windows, cp.float32),
            windows_map,
            cp.asarray(windows_map, cp.int32)
        ]

    @abstractmethod
    def compute_signals(self, channels=None):
        """Method to compute signals of each pixel for the desired channels.

        Parameters
        ----------
        channels : list of channel indices
            If None compute signals of all channels. By default None.
        
        Notes
        -----
        The specific computing logic is left to the concrete implementations.
        However, implementations should ensure that the signal is only computed 
        for the specified channels and stored in the `signals` attribute array.
        """
        pass

    @abstractmethod
    def pre_trigger_action(self):
        """Computes trigger signals.

        Notes
        -----
        The specific logic is left to the concrete implementations.
        However, implementations should ensure that the signal is only computed 
        for the channels needed to generate a camera trigger.
        This method is called only if the camera trigger is enabled.
        """
        pass

    @abstractmethod
    def trigger_action(self):
        """Generates a camera trigger.

        Notes
        -----
        Concrete implementations of this method should contain the logic
        to determine when a camera trigger has been be generated.  If the
        trigger condition is met, implementations *must* ensure that:

          * the `triggered` attribute is set to `True`.
          * the `trigger_time` attribute is set to the time
            representing the moment when the trigger condition was met.
        
        This method is called only if the camera trigger is enabled.
        """
        pass

    def post_trigger_action(self):
        """Optional action that is performed right after the trigger action,
        regardless if a camera trigger is generated.
        This method is called only if the camera trigger is enabled.
        """
        pass

    @abstractmethod
    def pre_sampling_action(self):
        """Computes signals to be sampled.

        Notes
        -----
        The specific logic is left to the concrete implementations.
        However, implementations should ensure that the signals are only computed 
        for the channels that will be sampled (unless they are the same from which
        the camera trigger is generated).
        This method is called only if a trigger condition is met or if 
        the camera trigger is disabled.
        """
        pass

    @abstractmethod
    def sampling_action(self):
        """Digitise the signals.

        Notes
        -----
        The specific logic is left to the concrete implementations.
        This method is called only if a trigger condition is met or if 
        the camera trigger is disabled.
        """
        pass

    def post_sampling_action(self):
        """Optional action that is performed right after the sampling action.
        This method is called only if a trigger condition is met or if 
        the camera trigger is disabled.
        """
        pass

    def apply_ideal_discriminator_to_channel(
        self,
        channel: int,
        thresholds: cp.ndarray,
        offset: cp.ndarray,
        time_slices_over_threshold: int
    ) -> cp.ndarray:
        """Apply an ideal discriminator to a specific channel pre-computed signals.

        This method implements an ideal discriminator on the waveforms of a given
        channel.  It compares the input signal against per-pixel thresholds and
        sets the output signal based on whether the input signal exceeds the
        threshold for at least a specified number of consecutive time slices.

        Parameters
        ----------
        channel : int
            The channel number to process.
        thresholds : cp.ndarray
            A CuPy 1D array of thresholds, one for each pixel. 
            This array should have a dtype of `cp.float32`.
        offset : cp.ndarray
            A CuPy 1D array of threshold offsets, one for each pixel. 
            This array should have a dtype of `cp.float32`.
        time_slices_over_threshold : int
            The minimum number of consecutive time slices the signal must be 
            above the threshold to trigger a positive output. This value is 
            assumed for all pixels.

        Returns
        -------
        cp.ndarray
            A CuPy array of the same shape as the input signal, containing the
            output of the ideal discriminator. The output will be 0.0f where the
            signal is below the threshold (or doesn't stay above threshold long
            enough) and 1.0f where it is above the threshold.

        Examples
        --------
        .. code-block:: python

            n_pixels = camera.n_pixels
            thresholds = cp.random.rand(n_pixels).astype(cp.float32) * 10
            offset = cp.zeros((n_pixels), dtype=cp.float32)
            min_time_slices = 10
            channel_num = 0

            output_signal = camera.apply_ideal_discriminator_to_channel(channel_num, thresholds, offset, min_time_slices)
            # output_signal now contains the discriminated signal for channel 0.
        
        """

        inp_signal = self.get_channel_signals(channel, reshape=False)
        out_signal = cp.empty_like(inp_signal)
        window_size = len(self.time_windows[channel])
        args = [
            inp_signal,
            out_signal,
            thresholds,
            offset,
            cp.int32(time_slices_over_threshold),
            self.pixel_mask,
            cp.int32(window_size),
            cp.int32(self.n_pixels)
        ]
        
        block_size = self._number_of_threads(window_size) if self._adaptive_blocksize else 128
        
        ideal_discriminator((self.n_pixels,),(block_size,),args)
        return out_signal

    def apply_peak_detection_to_channel(
        self,
        peak_amplitudes: cp.ndarray,
        peaking_times: cp.ndarray,
        channel: int,
        t_start: float,
        extent: float
    ) -> None:
        """Apply peak detection to a specific channel.

        This method processes the pre-computed signals for a given channel using `peak_detection` kernel
        to identify peaks and store their amplitudes and times.

        Parameters
        ----------
        peak_amplitudes : cp.ndarray
            A CuPy array where the detected peak amplitudes will be stored.
            This array should be pre-allocated with a size equal to the number 
            of pixels and have a dtype of `cp.float32`.
            It can be allocated once as class attribute.
        peaking_times : cp.ndarray
            A CuPy array where the detected peaking times will be stored.
            This array should be pre-allocated with a size equal to the number 
            of pixels and have a dtype of `cp.float32`.
            It can be allocated once as class attribute.
        channel : int
            The channel number to process.
        t_start : float
            The starting time of the peak detection time window (in ns).
        extent : float
            The duration of the peak detection time window (in ns).

        Examples
        --------

        .. code-block:: python

            n_pixels = camera.n_pixels
            peak_amps = cp.empty((n_pixels,), dtype=cp.float32)
            peak_times = cp.empty((n_pixels,), dtype=cp.float32)
            channel_num = 0
            t_start = 0.0
            duration = 100.0
            camera.apply_peak_detection_to_channel(peak_amps, peak_times, channel_num, t_start, duration)
            # peak_amps and peak_times now contain the results for channel 0.

        """
        signals = self.get_channel_signals(channel, reshape=False)
        time_window = self._d_windows[self._windows_map[channel]:self._windows_map[channel+1]]
        mask = self.pixel_mask
        window_size = cp.int32(len(time_window))
        n_pixels = cp.int32(self.n_pixels)

        args = [
            peak_amplitudes,
            peaking_times,
            signals,
            time_window,
            cp.float32(t_start),
            cp.float32(extent),
            mask,
            window_size,
            n_pixels,
        ]

        block_size = self._number_of_threads(window_size) if self._adaptive_blocksize else 128
        peak_detection((self.n_pixels,),(block_size,),(*args,), shared_mem=8*block_size)

    def _prepare_time_windows(self):
        """Generate dynamic time windows and copy related data to device.
        """
        # Generate trigger time windows and base sampling windows
        # _prepare_time_windows has been called at the beginning of a event
        if self.triggered == False:
            n_tot = self.source[0].shape[0]
            if n_tot > 0:
                tmin = cp.min(self.source[0]).get()
                tmax = cp.max(self.source[0]).get()
            else:
                tmin = 0
                tmax = max([self.channels_time_resolution[i] for i in self.trigger_channels])
            
            self.time_windows = [None]*self.n_channels
            self._windows_map = np.empty((self.n_channels+1,), dtype=np.int32)
            windows_size = 0
            self._windows_map[0] = 0
            for i in range(self.n_channels):
                if i in self.trigger_channels:
                    t0 = tmin + self.trigger_window_start_offset[i]
                    t1 = tmax + self.trigger_window_end_offset[i]
                    self.time_windows[i] = np.arange(t0, t1, self.channels_time_resolution[i], dtype=np.float32)
                    windows_size += self.time_windows[i].shape[0]
                elif i in self.sampling_channels:
                    sampling_channel_index = self.sampling_channels.index(i)
                    sampling_window_extent = self.sampling_window_extent[sampling_channel_index]
                    self.time_windows[i] = np.arange(0, sampling_window_extent, self.channels_time_resolution[i], dtype=np.float32)
                    # If the camera trigger is disabled a trigger time must have been provided
                    if self.trigger_time is not None:
                        self.time_windows[i] += t0
                    windows_size += self.time_windows[i].shape[0]
                else:
                    auxiliary_channel_index = self.auxiliary_channels.index(i)
                    auxiliary_window_extent = self.auxiliary_window_extent[auxiliary_channel_index]
                    self.time_windows[i] = np.arange(0, auxiliary_window_extent, self.channels_time_resolution[i], dtype=np.float32)
                    windows_size += self.time_windows[i].shape[0]
                
                self._windows_map[i+1] = windows_size
            
            # Allocate space on the device for time windows
            self._d_windows = cp.empty((windows_size,), dtype=cp.float32)
            # Copy mapping to device
            self._d_windows_map = cp.asarray(self._windows_map, dtype=cp.int32)
        
        # If the camera trigger is enabled the trigger time is known
        # only if the read-out has been triggered
        if self.triggered == True:
            for i in range(self.n_channels):
                if i in self.trigger_channels:
                    continue
                elif i in self.sampling_channels:
                    sampling_channel_index = self.sampling_channels.index(i)
                    t0 = self.trigger_time + self.sampling_delay[sampling_channel_index]
                else:
                    auxiliary_channel_index = self.auxiliary_channels.index(i)
                    t0 = self.trigger_time + self.auxiliary_delay[auxiliary_channel_index]
                self.time_windows[i] += t0

    # Perform all actions
    def simulate_response(self, source=None):
        """Simulates the camera response to a given source of photo-electrons.

        This method controls the simulation process:

          1. Getting the source.
          2. Preparing time windows for trigger channels.
          3. Triggering actions (pre, trigger, post).
          4. Preparing time windows for channels to be sampled.
          5. Sampling actions (pre, sampling, post).

        If :py:attr:`enable_camera_trigger` is True, the :py:meth:`pre_trigger_action`,
        :py:meth:`trigger_action`, and :py:meth:`post_trigger_action` methods are called in
        sequence.
        If a trigger occurs (as determined by :py:meth:`trigger_action`),
        or if camera triggering is disabled, the sampling phase starts.

        Parameters
        ----------
        source : Tuple[cp.ndarray, cp.ndarray], optional
            A tuple containing:

              - **pes**: A 1D CuPy array of shape (total_n_pes,) containing the
                arrival times of all photo-electrons.

              - **pes_map**: A 1D CuPy array of shape (n_pixels + 1,) representing
                a mapping to access the arrival times for each pixel.  The arrival
                times for pixel `i` are given by ```pes[pes_map[i]:pes_map[i+1]]```.
            
            If None only the background is simulated.

        Raises
        ------
        RuntimeError
            If camera triggering is disabled (:py:attr:`enable_camera_trigger` is False)
            and :py:attr:`trigger_time` is not set (i.e., is None). This ensures that
            a valid trigger time is available for the sampling phase.

        Notes
        -----
        The method also increments an event counter (`self._event_counter`)
        after each simulation.

        If :py:attr:`increment_seed` is true, the random seed (:py:attr:`seed`) is
        incremented by :py:attr:`n_pixels` after each simulation. This helps
        ensure that the simulation of different events produces different random
        values (e.g. background and cross-talk generation).

        The following methods are called during the simulation:

            1. If camera triggering is enabled:

                a. :py:meth:`pre_trigger_action()`: Actions before the trigger.
                b. :py:meth:`trigger_action()`: Performs the trigger logic (should set :py:attr:`triggered` and :py:attr:`trigger_time` attributes).
                c. :py:meth:`post_trigger_action()`: Actions after the trigger.
            
            2. If :py:attr:`triggered` is True or camera triggering is disabled (and a custom
               trigger time is provided):

                a. :py:meth:`pre_sampling_action()`: Actions before sampling.
                b. :py:meth:`sampling_action()`: Performs the sampling.
                c. :py:meth:`post_sampling_action()`: Actions after sampling.
            
        """
        if not self._waveforms_are_initialized:
            raise(RuntimeError('Waveforms have not been initialized properly.'))
        
        # print('start')
        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t0 = time.time()
        
        self.source = source
        
        self.triggered = False
        if self.enable_camera_trigger:
            self.trigger_time = None

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t1 = time.time()
            self.timer.add_entry('simulate_response', 'get source', t1-t0)

        # print('prepering windows for trigger')
        if not self.fixed_time_windows:
            self._prepare_time_windows()
        # print('...done')

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t2 = time.time()
            self.timer.add_entry('simulate_response', 'compute trigger windows', t2-t1)

        if self.enable_camera_trigger:
            # print("Computing trigger signals")
            # Where to compute trigger signals
            self.pre_trigger_action()
            # print('...done')

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t3 = time.time()
                self.timer.add_entry('simulate_response', 'pre_trigger_action', t3-t2)

            # print("Performing trigger")
            # Where to perform trigger and update self.triggered attribute
            self.trigger_action()
            # print('...done')

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t4 = time.time()
                self.timer.add_entry('simulate_response', 'trigger_action', t4-t3)
            
            # print('Trigger post action')
            self.post_trigger_action()
            # print('...done')

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t5 = time.time()
                self.timer.add_entry('simulate_response', 'post_trigger_action', t5-t4)
        else:
            if self.timer.active:
                self.timer.add_entry('simulate_response', 'pre_trigger_action', 0)
                self.timer.add_entry('simulate_response', 'trigger_action', 0)
                self.timer.add_entry('simulate_response', 'post_trigger_action', 0)
                t5 = t2

        if not self.enable_camera_trigger or self.triggered:
            self._triggered_events.append(self._event_counter)

            if self.trigger_time is None:
                raise(RuntimeError("A trigger time must be provided if the camera trigger is disabled."))

            # print('Prepare sampling windows')
            if not self.fixed_time_windows:
                self._prepare_time_windows()
            # print('...done')

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t6 = time.time()
                self.timer.add_entry('simulate_response', 'compute sampling windows', t6-t5)

            # Where to compute sampling signals
            # print("Pre sampling action")
            self.pre_sampling_action()
            # print('...done')

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t7 = time.time()
                self.timer.add_entry('simulate_response', 'pre_sampling_action', t7-t6)
            
            # print('Sampling action')
            self.sampling_action()
            # print('...done')

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t8 = time.time()
                self.timer.add_entry('simulate_response', 'sampling_action', t8-t7)
            
            # print('Post sampling action')
            self.post_sampling_action()
            # print('...done')

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t9 = time.time()
                self.timer.add_entry('simulate_response', 'post_sampling_action', t9-t8)
        
        self._event_counter += 1

        # print('Done!\n')
        if self.increment_seed:
            self.base_seed = self.base_seed + self.n_pixels

class CherenkovSiPMCamera(CherenkovCamera):
    """
    Base class for a Cherenkov camera that uses Silicon Photo-Multipliers (SiPMs).
    Inherits from CherenkovCamera and implements virtual methods specific to SiPMs.
    """
    def __init__(
            self,
            n_pixels: int,
            waveforms: Union[List[Waveform], Tuple[Waveform]],
            trigger_channels: List[int],
            sampling_channels: List[int],
            channels_time_resolution: List[float],
            pde: PhotonDetectionEfficiency = None,
            geometry: SiPMCameraGeometry = None
        ):
        # Initialize the base class
        super().__init__(
            n_pixels,
            waveforms,
            trigger_channels,
            sampling_channels,
            channels_time_resolution
        )
        self.geometry = geometry
        self.pde = pde

        # SiPM-wise parameters
        self.cross_talk = cp.zeros((self.n_pixels,), dtype=cp.float32)
        self.sigma_ucells = cp.zeros((self.n_pixels,), dtype=cp.float32)
        self.background_rate = cp.zeros((self.n_pixels,), dtype=cp.float32)

    @property
    def cross_talk(self):
        return self._cross_talk

    @cross_talk.setter
    def cross_talk(self, xt):
        if not isinstance(xt, cp.ndarray):
            xt = cp.asarray(xt, dtype=cp.float32)
        self._cross_talk = xt

    @property
    def sigma_ucells(self):
        return self._sigma_ucells

    @sigma_ucells.setter
    def sigma_ucells(self, s_ucells):
        if not isinstance(s_ucells, cp.ndarray):
            s_ucells = cp.asarray(s_ucells, dtype=cp.float32)
        self._sigma_ucells = s_ucells

    @property
    def background_rate(self):
        return self._background_rate

    @background_rate.setter
    def background_rate(self, bkg):
        if not isinstance(bkg, cp.ndarray):
            bkg = cp.asarray(bkg, dtype=cp.float32)
        self._background_rate = bkg
        self._inv_background_rate = cp.where(bkg>1e-9, 1./bkg, 1e9)

    @property
    def pixel_mask(self):
        return self._pixel_mask

    @pixel_mask.setter
    def pixel_mask(self, mask):
        if not isinstance(mask, cp.ndarray):
            mask = cp.asarray(mask, dtype=cp.int32)
        self._pixel_mask = mask

    def compute_signals(self, channels=None):
        """Compute SiPM signals for the specified channels.

        Parameters
        ----------
        channels : List[int], optional
            Channels IDs, by default computes all channels.
        """
        # Skip computation of channels not in `channels`
        if channels is None:
            skip_channels = cp.zeros((self.n_channels,), dtype=cp.bool_)
        else:
            skip_channels = cp.asarray([i not in channels for i in range(self.n_channels)], dtype=cp.bool_)

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t0 = time.time()
            self.timer.add_section(f'compute_signals{str(channels)}')

        # Fixed time windows: copy to device all windows but only at the first event
        if self.fixed_time_windows and self._event_counter == 0:
            self._d_windows, self._windows_map, self._d_windows_map = self._get_time_windows_parameters()
        
        # Dynamic time windows
        # Windows calculation is handled by `_prepare_time_windows` base class method in two steps:
        #   1) Always at the beginning of a event:
        #       - define all non-sampling windows
        #       - define the sampling windows in a range 
        #           - [0,sampling_extent] if the camera trigger is enabled;
        #           - [trigger_time,trigger_time+sampling_extent] if the camera trigger is disabled;
        #       - define the mapping (since the size of the windows is known)
        #         on the host (`self._windows_map`) and on the device (`self._d_windows_map`)
        #   2) if the camera is triggered:
        #       - add trigger_time to the sampling time window 
        #         [0,sampling_extent] -> [trigger_time,trigger_time+sampling_extent] 
        #
        # Here we copy to device only the time windows corresponding
        # to the channels that are going to be computed
        if not self.fixed_time_windows:
            for i in channels:
                self._d_windows[self._windows_map[i]:self._windows_map[i+1]] = cp.asarray(self.time_windows[i], dtype=cp.float32)
        
        self._time_windows_params = [
            self._d_windows,
            self._d_windows_map
        ]

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t1 = time.time()
            self.timer.add_entry(f'compute_signals{str(channels)}', 'windows_parameters', t1-t0)

        # Signals
        signals_map = self._d_windows_map*self.n_pixels
        signals_n_samples = self._windows_map[-1]*self.n_pixels

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t2 = time.time()
            self.timer.add_entry(f'compute_signals{str(channels)}', 'signals mapping', t2-t1)
                
        # Allocate only if the array size is different
        # (i.e.: do not re-allocate when computing signals of the same event)
        # Maybe it would be better to allocate only if a bigger array is needed
        # and access signals only through `get_channel_signals` method
        if self.signals.shape[0] != signals_n_samples:
            self.signals = cp.empty((signals_n_samples,), dtype=cp.float32)
        
        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t3 = time.time()
            self.timer.add_entry(f'compute_signals{str(channels)}', 'signals allocation', t3-t2)

        signals_params = [
            self.signals,
            signals_map,
            skip_channels,
            cp.int32(self.n_channels)
        ]

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t4 = time.time()
            self.timer.add_entry(f'compute_signals{str(channels)}', 'signals_parameters', t4-t3)

        # SiPMs
        sipms_params = [
            self.cross_talk,
            self.sigma_ucells,
            self.pixel_mask
        ]

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t5 = time.time()
            self.timer.add_entry(f'compute_signals{str(channels)}', 'sipm_parameters', t5-t4)

        # Background
        if self.fixed_time_windows and self._event_counter == 0:
            bkg_start = min([tw[0].get() if isinstance(tw, cp.ndarray) else tw[0] for tw in self.time_windows]) - self._max_wave_extent
            bkg_end = max([tw[-1].get() if isinstance(tw, cp.ndarray) else tw[-1] for tw in self.time_windows])
            self._background_params = [
                self._inv_background_rate,
                cp.float32(bkg_start),
                cp.float32(bkg_end)
            ]

        elif not self.fixed_time_windows:
            # dynamic time windows are np.ndarrays
            t0 = min([self.time_windows[i][0] for i in self.trigger_channels])
            t1 = max([self.time_windows[i][-1] for i in self.trigger_channels])
            bkg_start = min(t0, t0+min(self.sampling_delay+self.auxiliary_delay)) - self._max_wave_extent
            bkg_end = max(t1, t0+max(self.sampling_delay+self.auxiliary_delay)+max(self.sampling_window_extent+self.auxiliary_window_extent))
            self._background_params = [
                self._inv_background_rate,
                cp.float32(bkg_start),
                cp.float32(bkg_end)
            ]

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t6 = time.time()
            self.timer.add_entry(f'compute_signals{str(channels)}', 'background_parameters', t6-t5)

        n_pixels = cp.int32(self.n_pixels)

        if self._event_counter == 0:
            self.__gains = cp.concatenate(self.channels_gain, dtype=cp.float32)

        self._params = [
            *self._time_windows_params,
            *signals_params,
            self.source[0],
            self.source[1],
            *self._waveforms_params,
            self.__gains,
            *sipms_params,
            *self._background_params,
            self.seed,
            n_pixels
        ]

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t7 = time.time()
            self.timer.add_entry(f'compute_signals{str(channels)}', 'prepare_parameters', t7-t6)

        max_window_size = max([len(self.time_windows[i]) for i in channels])
        shared_mem_size = max_window_size*4
        if self._adaptive_blocksize:
            n_threads = self._number_of_threads(max_window_size)
        else:
            n_threads = 128
        sipm_signals(
            (self.n_pixels*self.n_channels,),
            (n_threads,),
            (*self._params,),
            shared_mem=shared_mem_size
        )

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t8 = time.time()
            self.timer.add_entry(f'compute_signals{str(channels)}', 'compute_signals', t8-t7)

    def pre_trigger_action(self):
        """Compute SiPM signals for trigger channels.
        """
        self.compute_signals(self.trigger_channels)

    @abstractmethod
    def trigger_action(self):
        pass

    def pre_sampling_action(self):
        """Compute SiPM signals for sampling channels.
        """
        self.compute_signals(self.sampling_channels)

    @abstractmethod
    def sampling_action(self):
        pass
    
    def plot_modules(self, plotf, figsize=10, sep_factor=1.25, skip=None):
        """Plot a subplot for each module. See :py:func:`iactsim.visualization.plot_sipm_modules`.
        """
        from ..visualization._sipm_camera_plots import plot_sipm_modules
        return plot_sipm_modules(self, plotf, figsize, sep_factor, skip)
    
    def plot_module_pixels(self, plotf, subplot_size=4):
        """Plot a subplot for each pixel within a module. See :py:func:`iactsim.visualization.plot_sipm_module_pixels`.
        """
        from ..visualization._sipm_camera_plots import plot_sipm_module_pixels
        return plot_sipm_module_pixels(self, plotf, subplot_size)