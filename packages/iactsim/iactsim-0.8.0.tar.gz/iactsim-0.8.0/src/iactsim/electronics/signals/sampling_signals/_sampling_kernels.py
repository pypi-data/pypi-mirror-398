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

path = Path(__file__).parent / "sampling_signals.cu"
with open(path) as _source_file:
    source_code = _source_file.read()

include_path = ''.join([os.environ['CPATH']])

module = cp.RawModule(code=source_code, backend='nvcc', options=(''.join(['-I',include_path]),'--use_fast_math', '-std=c++11', '--extra-device-vectorization'))

peak_detection = get_kernel(module, 'peak_detection')

digitize = get_kernel(module, 'digitize')