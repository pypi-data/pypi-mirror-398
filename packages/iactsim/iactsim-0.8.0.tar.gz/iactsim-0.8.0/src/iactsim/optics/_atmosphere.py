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

from dataclasses import dataclass, field
import numpy as np

from ..visualization._iactsim_style import iactsim_style

@dataclass
class AtmosphericTransmission:
    """
    Represents atmospheric optical depth as a function of photon wavelength and emission altitude.

    Attributes:
        value: A numpy.ndarray of shape (n,m) representing the atmosphere transmission (from 0 to 1).
        wavelength: A numpy.ndarray of shape (n,) representing the wavelengths in nanometers.
        altitude: A numpy.ndarray of shape (m,) representing the emission altitude in millimeters.
    """
    value: np.ndarray = field(default=None, metadata={'units': 'None'})
    wavelength: np.ndarray = field(default=None, metadata={'units': 'nanometers'})
    altitude: np.ndarray = field(default=None, metadata={'units': 'millimeters'})

    def __repr__(self):
        field_info = []
        for field_name, field_value in self.__dict__.items():
            if field_value is None:
                field_info.append(f"{field_name}: not set")
            else:
                field_info.append(f"{field_name}: set")
        return f"AtmosphericTransmission({', '.join(field_info)})"
    
    @iactsim_style
    def plot(self, heatmap=None, depth=True):
        if self.wavelength is None or self.altitude is None or self.value is None:
            raise(RuntimeError("Atmosphere transmission has not been initialized properly."))
        
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()

        n_wl = len(self.wavelength)
        n_th = len(self.altitude)
        
        if heatmap is None:
            heatmap = True if n_th > 10 else False
        
        data = self.value.copy()

        ylabel = 'Optical Depth'
        if not depth:
            data = np.exp(-data)
            ylabel = 'Transmission'

        if not heatmap:
            data = data.flatten()
            for i in range(n_th):
                label = None
                label = f'{self.altitude[i]/1e6:.1f} km'
                plt.plot(self.wavelength, data[i*n_wl:(i+1)*n_wl], label=label)
            if n_th < 10:
                plt.legend()
            plt.xlabel('Wavelength (nm)')
            plt.ylabel(ylabel)
            if depth:
                plt.yscale('log')
            ax.grid(which='both')
        else:
            levels = np.linspace(0,1,100) if not depth else np.logspace(np.log10(data[data>0].min()),np.log10(data[data<99999].max()),100)
            contour = ax.contourf(self.wavelength, self.altitude/1e6, data, levels=levels)
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Emission altitude (km)")
            fig.colorbar(contour, ax=ax, boundaries=[0,1])

        return fig, ax
