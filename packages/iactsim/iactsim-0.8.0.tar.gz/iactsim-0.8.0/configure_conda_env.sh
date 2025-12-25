#!/usr/bin/bash

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

target_env=$1

env=`echo "$CONDA_PREFIX" | rev | cut -d"/" -f1  | rev`

if [[ "$env" != "$target_env" ]]; then
    echo "The environment $target_env is not active"
    exit 1
fi

activate_dir=$CONDA_PREFIX/etc/conda/activate.d
deactivate_dir=$CONDA_PREFIX/etc/conda/deactivate.d

# Write a script that is sourced at each activation
# NVHPC_ROOT is defined when calling module load nvhpc
# NVCC and CUDA_PATH are defined by this activation script
# CUDA_PATH is assumed to be $NVHPC_ROOT/cuda
mkdir -p $activate_dir
cat << END > "$activate_dir/set_vars.sh"
#!/bin/sh
module load nvhpc
export NVCC=$NVHPC_ROOT/compilers/bin/nvcc
export CUDA_PATH=$NVHPC_ROOT/cuda
END

# Write a script that is sourced at each deactivation
mkdir -p $deactivate_dir
cat << END > "$deactivate_dir/unset_vars.sh"
#!/bin/sh
unset NVCC
unset CUDA_PATH
module purge
END