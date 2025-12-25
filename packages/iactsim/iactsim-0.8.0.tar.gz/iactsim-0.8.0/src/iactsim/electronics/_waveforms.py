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

import numpy as np
import cupy as cp

from ..visualization._iactsim_style import iactsim_style

class Waveform:
    """
    Represents the normalized output signal of the electronics in response to a single photon 
    detection as a function of the time from its arrival time.
    Is assumed to be 0 outside the defined time window.

    Parameters
    ----------
    time : numpy.ndarray
        Array of time values corresponding where the waveform is defined, must be monotonically increasing.
    amplitude : numpy.ndarray
        Array of waveform amplitudes corresponding to the time array.
    coupling : str
        Coupling of the signal. Must be "AC" or "DC" (case insensitive).
        It is only used when calling `normalize()` method without a normalization value:

          - "AC": normalize by the waveform peak;
          - "DC": normalize by the waveform integral.
    
    Notes
    -----
        A "dummy" waveform can be created using the default `None` arguments:

        .. code-block::`pyhton`

            dummy_wave = Waveform()
        

    Raises
    ------
    TypeError
        If the input argument are not Numpy ndarray.
    ValueError
        If the input argument have more than one dimension.
    ValueError
        If the input argument do not have the same length. 
    ValueError
        If the time array is not monotonically increasing. 
    ValueError
        If the time array is not equispaced. 
    ValueError
        If the signal coupling is not valid.
    """

    def __init__(self, time: np.ndarray = None, amplitude: np.ndarray = None, coupling: str = None):
        
        if all([x is None for x in [time, amplitude, coupling]]):
            self._time = None
            self._amplitude = None
            self._coupling = None
            return

        if not isinstance(time, np.ndarray) or not isinstance(amplitude, np.ndarray):
            raise TypeError("time and amplitude must be NumPy arrays")
        
        if time.ndim != 1 or amplitude.ndim != 1:
            raise ValueError("time and amplitude must be 1D arrays")
        
        if len(time) != len(amplitude):
            raise ValueError("time and amplitude arrays must have the same length")

        if not np.all(np.diff(time) > 0):
            raise ValueError("time array must be monotonically increasing")

        if not isinstance(coupling, str) or coupling.lower() not in ['ac', 'dc']:
            raise(ValueError(f"Invalid signal coupling '{coupling}'. Accepted amplitudes are 'AC' and 'DC' (case insensitive)."))

        time_diffs = np.diff(time)
        tolerance = 1e-3 
        if not np.allclose(time_diffs, time_diffs[0], atol=tolerance):
            raise ValueError("time array must be equispaced")

        self._time = time
        self._amplitude = amplitude
        self._coupling = coupling.lower()
        self._extent = self._time[-1] - self.time[0]
        self.normalize()

    @property
    def time(self):
        """
        Returns the time array.
        """
        return self._time
    
    @property
    def amplitude(self):
        """
        Returns the amplitude array.
        """
        return self._amplitude
    
    @property
    def coupling(self):
        """
        Returns the signal coupling.
        """
        return self._coupling
    
    def get_peak_time(self) -> float:
        """
        Returns the time corresponding to the peak amplitude of the waveform.
        """
        peak_index = np.argmax(self._amplitude)
        return self._time[peak_index]

    def get_peak_amplitude(self) -> float:
        """
        Returns the peak amplitude of the waveform.
        """
        return np.max(self._amplitude)

    def get_integral(self) -> float:
        """
        Returns the approximate integral of the waveform using the trapezoidal rule.
        """
        return np.trapezoid(self._amplitude, x=self._time)

    def get_squared_integral(self) -> float:
        """
        Returns the approximate integral of the squared waveform using the trapezoidal rule.
        """
        return np.trapezoid(self._amplitude**2, x=self._time)
    
    def get_size(self) -> int:
        """
        Returns the waveform number of time bins.
        """
        if len(self._time) != len(self._amplitude):
            raise(RuntimeError("The number of amplitude amplitudes must be equal to the number of time-bins"))
        return len(self._time)
    
    def get_extent(self) -> float:
        """
        Returns the waveform time-extent.
        """
        return self._extent
    
    def normalize(self, norm=None):
        """Normalize the waveform amplitude.

        Parameters
        ----------
        norm : float, optional
            Normalization factor. If None, it is determined based on the
            coupling type. For 'AC' coupling, the waveform is normalized to
            the peak amplitude. For 'DC' coupling it's normalized
            to the integral. By default, None.
        """
        if norm is None:
            if self.coupling == 'ac':
                norm = 1./self.get_peak_amplitude()
            else:
                norm = 1./self.get_integral()
        self._amplitude *= norm

    @iactsim_style
    def plot(self):
        if self.time is None or self.amplitude is None:
            raise(RuntimeError("Waveform has not been initialized."))
        
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        plt.plot(self.time, self.amplitude, color='black')
        plt.xlabel('Time (ns)')
        plt.ylabel('Signal amplitude')
        ax.grid(which='both')
        return fig, ax

    def get_waveform_texture(self):
        # Texture Setup
        width = len(self.time)
        texture_data = self.amplitude.astype(np.float32)
        
        # Create a CUDAarray for the 1D texture
        desc = cp.cuda.texture.ChannelFormatDescriptor(32, 0, 0, 0, cp.cuda.runtime.cudaChannelFormatKindFloat)
        cu_array = cp.cuda.texture.CUDAarray(desc, width)
        cu_array.copy_from(texture_data)
        
        # Create another texture object (Linear Interpolation)
        res_desc_linear = cp.cuda.texture.ResourceDescriptor(
        cp.cuda.runtime.cudaResourceTypeArray,
        cuArr=cu_array
        )
        tex_desc_linear = cp.cuda.texture.TextureDescriptor(
            addressModes = (cp.cuda.runtime.cudaAddressModeClamp,),
            filterMode = cp.cuda.runtime.cudaFilterModeLinear,
            readMode = cp.cuda.runtime.cudaReadModeElementType,
            normalizedCoords = False
        )
        return cp.cuda.texture.TextureObject(res_desc_linear, tex_desc_linear), 1./(self.time[1]-self.time[0]), self.time[0] 