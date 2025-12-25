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

import numpy as np

def normalize_aspheric_coefficients(coefficients: np.ndarray | list | tuple, half_aperture: float) -> np.ndarray:
    """Rewrite aspheric coefficients for float32 calculations.

    This function normalizes aspheric coefficients to ensure numerical stability
    when using single-precision calculations. It scales the coefficients
    based on the surface aperture radius to prevent potential overflow or
    underflow issues during calculations involving powers of the radial distance.

    Parameters
    ----------
    coefficients : numpy.ndarray | list | tuple
        The aspheric coefficients. It can be a NumPy array, a list or a tuple.
    half_aperture : float
        The half-aperture of the surface.

    Returns
    -------
    new_coefficients : numpy.ndarray
        A new array containing the normalized aspheric coefficients.

    Notes
    -----
    The normalization is done by multiplying each coefficient A[i] by ra^(2*(i+1)).
    This scaling ensures that the coefficients are adjusted appropriately for
    calculations involving the radial distance, which is typically normalized by
    the surface half-aperture.
    """
    new_coefficients = np.array(coefficients, copy=True)  # Convert to NumPy array if it is a list or tuple
    for i in range(new_coefficients.shape[0]):
        new_coefficients[i] = new_coefficients[i] * half_aperture**(2*(i+1))
    return new_coefficients