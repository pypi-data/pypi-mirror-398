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

import importlib.resources
import functools

from ..utils._is_notebook import is_notebook

class MplInteractiveContext:
    """Re-enable interactive mode.
    See issue:
        matplotlib.style.context() stops plotting inline in Jupyter
        https://github.com/matplotlib/matplotlib/issues/26716
    """
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        import matplotlib.pyplot as plt
        if is_notebook():
            plt.ion()

def iactsim_style(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import matplotlib.pyplot as plt
        with MplInteractiveContext():
            with importlib.resources.path('iactsim', 'iactsim.mplstyle') as style_path:
                with plt.style.context(style_path):
                    result = func(*args, **kwargs)
        
        return result
    return wrapper