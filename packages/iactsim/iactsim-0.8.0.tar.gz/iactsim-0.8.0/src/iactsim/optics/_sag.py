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

# Tolerance for considering a value to be zero
ZERO_TOLERANCE = 1e-6 # mm^-1, 1000 m curvature radius 

def sag(radius: np.ndarray, curvature: float, conic_constant: float, 
        aspheric_coefficients: np.ndarray, axial_z: float, is_fresnel: bool) -> np.ndarray:
    r"""
    Calculates the sagitta of an aspheric surface.

    Parameters
    ----------
    radius : numpy.ndarray
        Radial distance(s) from the optical axis (can be a scalar or a NumPy array).
    curvature : float
        Surface curvature (1/radius of curvature).
    conic_constant : float
        Conic constant.
    aspheric_coefficients : numpy.ndarray
        1D array of aspheric coefficients. The i-th element is the coefficient
        of the r**(2*(i+1)) term.
    axial_z : float
        Axial z-coordinate of the surface vertex.
    is_fresnel : bool
        Whether the surface is a Fresnel surface (or has negligible curvature).

    Returns
    -------
    numpy.ndarray
        The sagitta value(s) corresponding to the input radius/radii.
        Returns axial_z if the radius is close to zero or if it is a fresnel surface.

    Raises
    ------
    ValueError
        If the inputs have invalid shapes or if curvature is negative.

    Notes
    -----
    The sagitta is described by the equation

        .. math::

            s(r) = \frac{cr^2}{1 + \sqrt{1 - c^2r^2\left(1+k\right)}} + \sum_{i=1}A_{i-1}r^{2i} + z_0

    Examples
    --------
    
    .. code-block:: python

        radius = np.array([0.0, 1.0, 2.0])
        curvature = 0.1
        conic_constant = -1.0
        aspheric_coefficients = np.array([0.01, 0.001])
        axial_z = 10.0
        is_fresnel = False
        sag(radius, curvature, conic_constant, aspheric_coefficients, axial_z, is_fresnel)
    
    """

    if not isinstance(aspheric_coefficients, np.ndarray):
        aspheric_coefficients = np.asarray(aspheric_coefficients, dtype=np.float64)

    # Input validation
    if aspheric_coefficients.ndim != 1:
        raise ValueError("aspheric_coefficients must be a 1D array")

    # Ensure radius is an array to allow for consistent indexing, but keep track of original type
    was_list = isinstance(radius, list) 
    was_scalar = isinstance(radius, (int, float))
    original_length = len(radius) if was_list else None
    radius = np.atleast_1d(np.asarray(radius, dtype=np.float64))

    # Handle Fresnel or flat surfaces
    if is_fresnel or np.isclose(curvature, 0, atol=ZERO_TOLERANCE):
        if was_scalar:
            return axial_z
        return np.full_like(radius, axial_z, dtype=np.float64)

    # Aspheric term calculation
    powers = np.arange(1, len(aspheric_coefficients) + 1) * 2
    r_powers = radius[..., np.newaxis]**powers
    aspheric_term = np.sum(aspheric_coefficients * r_powers, axis=-1)

    # Calculate the conic term
    arg_sqrt = 1 - (1 + conic_constant) * curvature**2 * radius**2
    conic_term = curvature * radius**2 / (1 + np.sqrt(np.where(arg_sqrt<0, np.inf, arg_sqrt)))

    result = np.where(np.isclose(radius, 0, atol=ZERO_TOLERANCE), 0, conic_term+aspheric_term) + axial_z

    # Return scalar only if input was a scalar
    if was_scalar:
        result = result[0]
    return result