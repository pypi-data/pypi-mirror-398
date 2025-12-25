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

# Use module __getattr__ and __dir__ for lazy submodule imports.
# Follwing PEP 562 (https://peps.python.org/pep-0562/)

import importlib as _importlib

try:
    from iactsim import utils
    from iactsim import _version
    __version__ = _version.version
except ImportError as e:
    msg = "The `iactsim` install you are using seems to be broken, " + \
            "(extension modules cannot be imported), " + \
            "please try reinstalling."
    raise ImportError(msg) from e

submodules = [
    'electronics',
    'optics',
    'utils',
    'visualization',
    'io',
    'models',
    'iactxx',
]

main = {
    'IACT': 'iactsim._iact',
}

__all__ = submodules + list(main)

def __dir__():
    return __all__

def __getattr__(name):
    if name in submodules:
        return _importlib.import_module(f'iactsim.{name}')
    elif name in main:
        module = _importlib.import_module(main[name])
        return getattr(module, name)
    else:
        raise AttributeError(f"Module 'iactsim' has no attribute '{name}'")