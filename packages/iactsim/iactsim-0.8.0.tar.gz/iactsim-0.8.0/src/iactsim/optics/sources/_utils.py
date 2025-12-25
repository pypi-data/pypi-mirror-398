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

def _disk_picking(umin: float, umax: float, n: int, seed: int = None, radial_uniformity: bool = False, dtype: type = cp.float32) -> cp.ndarray:
    """Generate `n` points uniformly distributed within a disk.

    This function generates points within a disk in the x-y plane, centered at (0, 0, 0).
    The distribution of points can be either uniform across the disk's area or uniform across
    the radius.

    Parameters
    ----------
    umin : float
        The minimum normalized radius of the disk.
    umax : float
        The maximum normalized radius of the disk.
    n : int
        The number of points to generate.
    seed : int, optional
        Seed for the random number generator. If None, a random seed will be used.
    radial_uniformity : bool, optional
        If False, the points are distributed uniformly across the disk's area.
        If True, the points are distributed uniformly along the radius.
        Defaults to True.
    dtype : type, optional
        The desired data type of the returned array. Defaults to `cp.float32`.

    Returns
    -------
    ps : cp.ndarray, shape (n, 3)
        A CuPy array containing the generated points. Each row represents a point (x, y, z),
        where z is always 0.

    Notes
    -----
    - If `radial_uniformity` is False, the radial distance of the points from the center is proportional to the square root of a uniform random variable.
    This ensures a uniform distribution of points across the disk's area.
    - If `radial_uniformity` is True, the radial distance is directly proportional to the uniform random variable.
    - The angular coordinate of the points is uniformly distributed between 0 and 2*pi.
    """
    rng = cp.random.default_rng(cp.random.Philox4x3210(seed))

    u = rng.random(n, dtype=dtype) 
    if not radial_uniformity:
        u = cp.sqrt(u*(umax**2 - umin**2) + umin**2) 
    else:
        u = u*(umax - umin) + umin

    v = rng.random(n, dtype=dtype) * 2. * cp.pi

    ps = cp.empty((u.shape[0], 3), dtype=dtype)
    ps[:, 0] = u * cp.cos(v)
    ps[:, 1] = u * cp.sin(v)
    ps[:, 2] = 0.
    return ps
