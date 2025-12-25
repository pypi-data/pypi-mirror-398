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
class PhotonDetectionEfficiency:
    """
    Represents SiPM photon-detection efficiency as a function of photon wavelength.

    Attributes:
        value: A numpy.ndarray of shape (n,) representing the photon detection efficiency (from 0 to 1).
               Each element [i] corresponds to the value at wavelength[i].
        wavelength: A numpy.ndarray of shape (n,) representing the wavelengths in nanometers.
    """
    value: np.ndarray = field(default=None, metadata={'units': 'None'})
    wavelength: np.ndarray = field(default=None, metadata={'units': 'nanometers'})

    def __repr__(self):
        field_info = []
        for field_name, field_value in self.__dict__.items():
            if field_value is None:
                field_info.append(f"{field_name}: not set")
            else:
                field_info.append(f"{field_name}: set")
        return f"PhotonDetectionEfficiency({', '.join(field_info)})"
    
    @iactsim_style
    def plot(self):
        if self.wavelength is None or self.value is None:
            raise(RuntimeError("Photon-detection efficiency has not been initialized properly."))
        
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        plt.plot(self.wavelength, self.value, color='black')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Photon-detection efficiency')
        ax.grid(which='both')
        return fig, ax