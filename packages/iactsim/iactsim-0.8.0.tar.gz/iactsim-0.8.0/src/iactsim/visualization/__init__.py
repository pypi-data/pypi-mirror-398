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

_functions = {
    'scatter': 'iactsim.visualization._scatter_plot',
    'histogram2d': 'iactsim.visualization._histogram2d',
    'plot_sipm_module_pixels': 'iactsim.visualization._sipm_camera_plots',
    'plot_sipm_modules': 'iactsim.visualization._sipm_camera_plots',
    'VTKOpticalSystem': 'iactsim.visualization._vtk_optical_system',
}

_all = _functions

import importlib as _importlib

def __getattr__(name):
    if name not in _all:
        raise AttributeError(f"Module 'iactsim.visualization' has no attribute '{name}'")
    
    _sub_module = _importlib.import_module(_all[name])

    return getattr(_sub_module, name)

__all__ = list(_all) + [s for s in dir() if not s.startswith('_')]
def __dir__():
    return __all__