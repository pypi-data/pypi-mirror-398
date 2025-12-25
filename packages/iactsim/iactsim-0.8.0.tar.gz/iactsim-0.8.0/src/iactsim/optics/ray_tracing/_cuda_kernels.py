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

import cupy as cp
import os as os
from pathlib import Path as Path

from ...utils._kernels import get_kernel

path = Path(__file__).parent / "ray_tracing.cu"
with open(path) as _source_file:
    source_code = _source_file.read()

include_path = ''.join([os.environ['CPATH']])

module = cp.RawModule(code=source_code, backend='nvcc', options=(''.join(['-I',include_path]),'--use_fast_math', '-std=c++11', '--extra-device-vectorization'))

ray_tracing = get_kernel(module, 'trace')
atmospheric_transmission = get_kernel(module, 'atmospheric_transmission')
trace_onto_sipm_modules = get_kernel(module, 'trace_onto_sipm_modules')
count_all_photons = get_kernel(module, 'count_all_photons')
camera_inputs = get_kernel(module, 'camera_inputs')
local_to_telescope_transform = get_kernel(module, 'telescope_transform')