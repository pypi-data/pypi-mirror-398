.. Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
.. SPDX-License-Identifier: GPL-3.0-or-later
..
.. This file is part of iactsim.
..
.. iactsim is free software: you can redistribute it and/or modify
.. it under the terms of the GNU General Public License as published by
.. the Free Software Foundation, either version 3 of the License, or
.. (at your option) any later version.
..
.. iactsim is distributed in the hope that it will be useful,
.. but WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
.. GNU General Public License for more details.
..
.. You should have received a copy of the GNU General Public License
.. along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

.. _install:

Install
=======

Requirements
~~~~~~~~~~~~
* **Python**

    3.11 or later

* **NVIDIA HPC SDK**  

    ``iactsim`` requires the NVIDIA HPC Software Development Kit to compile CUDA kernels.

* **CuPy**

    ``iactsim`` requires CuPy for GPU offloading.

* **CMake**

    >=3.15

* **A C++ compiler**
  
    ``gcc`` or ``nvcc``

Installation
~~~~~~~~~~~~

It is **recommended** to use a virtual environment. For example, using ``mamba``:

.. code-block:: bash

    mamba create -n simenv python=3.12
    mamba activate simenv

Compiler Setup
^^^^^^^^^^^^^^

You need a compiler for the C++ part. If you use HPC SDK compilers, as recommended here, you can use them with ``module load nvhpc`` before calling ``pip``.
You can choose ``gcc`` or ``nvcc`` appending ``-C cmake.args="-DCMAKE_CXX_COMPILER=<compiler_name>"`` to the install command, replacing ``<compiler_name>`` with the actual compiler name.

Install from PyPI
^^^^^^^^^^^^^^^^^

``iactsim`` source archive is available on ``PyPI``:

.. code-block:: bash

    pip install iactsim -v


Install from source (dev)
^^^^^^^^^^^^^^^^^^^^^^^^^

1. Clone the repository:

    .. code-block:: bash
    
        git clone https://gitlab.com/davide.mollica/iactsim.git
    
2. Move inside the cloned folder and install ``iactsim`` from source:

    .. code-block:: bash   

        cd iactsim
        python -m pip install . -v


For developers
--------------

You can install package locally without recompiling the C++ part (if has not changed) with the following

.. code-block:: bash

    python -m pip install --no-build-isolation -e .

To do so, you need to have all the dependencies installed in your system:

.. code-block:: bash

    pip install scikit-build-core pybind11 "setuptools_scm[toml]>=8.0" cmake ninja

zlib
^^^^

For the C++ part, by deafult `zlib-ng <https://github.com/zlib-ng/zlib-ng>`_ (*zlib data compression library for the next generation systems*) will be used (cmake will clone the repo automatically).
If you have to use `zlib <https://zlib.net/>`_ or you do not need to decompress gzip CORSIKA files, you can append ``-C cmake.args="-DUSE_ZLIBNG=OFF"`` to the install command.

NVIDIA HPC SDK
^^^^^^^^^^^^^^

`Configure the enviroment <https://docs.nvidia.com/hpc-sdk//hpc-sdk-install-guide/index.html#install-linux-end-usr-env-settings>`_ to use HPC SDK (you can download it from the `NVIDIA website <https://developer.nvidia.com/hpc-sdk>`_). 
We suggest to use `Environment Modules <https://modules.readthedocs.io/en/latest/>`_ to handle SDK configuration and then define ``NVCC`` and ``CUDA_PATH`` enviromental variables:
    
.. code-block:: bash

    module load nvhpc
    export NVCC=$NVHPC_ROOT/compilers/bin/nvcc
    export CUDA_PATH=$NVHPC_ROOT/cuda
    
With ``conda``/``mamba`` enviroments you can use the provided configuration script ``configure_conda_env``

.. code-block:: bash

    mamba activate simenv
    configure_conda_env simenv
    mamba deactivate

This adds an activation script and a deactivation script to the ``simenv`` enviroment that will automatically handle the configuration when it is activated or deactivated.

CuPy
^^^^

.. code-block:: bash

        pip install cupy-cuda<XXX>
    
Replace <XXX> with your CUDA version (e.g., ``cupy-cuda12x``).
For more detailed instructions on installing CuPy, refer to the `CuPy documentation <https://docs.cupy.dev/en/stable/install.html>`_.
