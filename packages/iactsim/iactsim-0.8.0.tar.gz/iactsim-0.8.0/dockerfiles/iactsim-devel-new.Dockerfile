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

# NVIDIA HPC SDK image
FROM nvcr.io/nvidia/nvhpc:24.11-devel-cuda12.6-ubuntu24.04 AS runtime

# Copy HPC SDK to the runtime layer
ARG NVHPC_PATH=/opt/nvidia/hpc_sdk
# COPY --from=build /opt/nvidia/hpc_sdk $NVHPC_PATH

# Set NVHPC environment variables
ARG NVHPC_VERSION=24.11
ENV NVARCH=Linux_x86_64

ENV NVCOMPILERS=$NVHPC_PATH
ENV NVHPC_ROOT=$NVHPC_PATH/$NVARCH/$NVHPC_VERSION
ENV MANPATH=$NVHPC_ROOT/compilers/man
ENV PATH=$NVHPC_ROOT/compilers/bin:$PATH
ENV CPATH=$NVHPC_ROOT/compilers/extras/qd/include/qd
ENV CPATH=$NVHPC_ROOT/comm_libs/nvshmem/include:$CPATH
ENV CPATH=$NVHPC_ROOT/comm_libs/nccl/include:$CPATH
ENV CPATH=$NVHPC_ROOT/math_libs/include:$CPATH
ENV CXX=$NVHPC_ROOT/compilers/bin/nvc++
ENV CPP=cpp
ENV F77=/opt/nvidia/hpc_sdk/Linux_x86_64/24.7/compilers/bin/nvfortran
ENV F90=$F77
ENV FC=$F77
ENV LD_LIBRARY_PATH=$NVHPC_ROOT/comm_libs/nvshmem/lib
ENV LD_LIBRARY_PATH=$NVHPC_ROOT/comm_libs/nccl/lib:$LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=$NVHPC_ROOT/math_libs/lib64:$LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=$NVHPC_ROOT/compilers/lib:$LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=$NVHPC_ROOT/compilers/extras/qd/lib:$LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=$NVHPC_ROOT/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=$NVHPC_ROOT/cuda/lib64:$LD_LIBRARY_PATH

# MPI Environment Variables (if needed)
ENV PATH=$NVHPC_ROOT/comm_libs/mpi/bin:$PATH
ENV MANPATH=$MANPATH:$NVHPC_ROOT/comm_libs/mpi/man

# For CuPy RawModule
ENV NVCC=$NVHPC_ROOT/compilers/bin/nvcc
ENV CUDA_PATH=$NVHPC_ROOT/cuda

# Switch to root user to install packages
USER root

# Update package lists and install Python3, pip, and venv
# Using --no-install-recommends helps keep the image size smaller
# Cleaning up apt lists afterwards also reduces image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        python-is-python3 \
    && rm -rf /var/lib/apt/lists/*