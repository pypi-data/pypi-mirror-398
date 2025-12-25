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
FROM nvcr.io/nvidia/nvhpc:24.11-devel-cuda12.6-ubuntu24.04 AS build

# Python 3.12 image
FROM python:3.12-bookworm AS runtime

# Copy HPC SDK to the runtime layer
ARG NVHPC_PATH=/opt/nvidia/hpc_sdk
COPY --from=build /opt/nvidia/hpc_sdk $NVHPC_PATH

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

# Cupy
RUN python -m pip install -U setuptools pip && \
    pip install numpy==2.0.0 && \
    pip install cupy-cuda12x && \
    pip install numba

# Install Poetry
ARG POETRY_VERSION=1.8.5
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME=/opt/poetry \
    POETRY_VERSION=${POETRY_VERSION} \
    PATH="/opt/poetry/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry self add "poetry-dynamic-versioning[plugin]"