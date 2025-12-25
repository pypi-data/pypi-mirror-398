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

import os as os
from pathlib import Path as Path
import cupy as cp
from ....utils._kernels import get_kernel

include_path = ''.join([os.environ['CPATH']])

path = Path(__file__).parent / "topological_trigger_logic.cu"
with open(path) as _source_file:
    source_code = _source_file.read()

module = cp.RawModule(
    code=source_code,
    backend='nvcc',
    options=(''.join(['-I',include_path]),'--use_fast_math', '-std=c++11', '--extra-device-vectorization', '-O3'),
    enable_cooperative_groups=True
)

topological_camera_trigger = get_kernel(module, 'topological_camera_trigger')
count_topological_camera_triggers = get_kernel(module, 'count_topological_camera_triggers')

# TODO: write an iterative implementation
# Increase the stack size of each GPU thread for contiguous pixels search recursion.
# With 2*1024 bytes the supported number of contiguous pixel can be set up to 18.
cp.cuda.runtime.deviceSetLimit(cp.cuda.runtime.cudaLimitStackSize, 2*1024)