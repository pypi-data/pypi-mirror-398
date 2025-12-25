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

def pointing_dir(altitude: float, azimuth: float) -> np.ndarray:
    """Telescope pointing direction in the corsika-like local reference frame.

    *   North -> (0, 0) : x-axis
    *   East -> (0, 90)
    *   South -> (0, 180)
    *   West -> (0, 270) : y-axis
    *   Zenith -> (90, any) : z-axis

    Parameters
    ----------
    altitude : float
        Altitude angle in degrees.
    azimuth : float
        Azimuth angle in degrees. Measured from North, increasing towards East (clockwise).

    Returns
    -------
    direction : ndarray, shape (3,)
        Pointing unit vector in the local reference frame (North-East-Up).
    """
    azimuth_rad = np.deg2rad(azimuth)
    altitude_rad = np.deg2rad(altitude)
    return np.array([
        np.cos(altitude_rad) * np.cos(azimuth_rad),
        -np.cos(altitude_rad) * np.sin(azimuth_rad),
        np.sin(altitude_rad),
    ])

def local_to_pointing_rotation(altitude: float, azimuth: float) -> np.ndarray:
    """Compute the rotation matrix to transform from the local reference frame (North-East-Up) to the pointing reference frame.

    This reference frame is defined such that when the telescope is
    pointing at the horizon towards the North (i.e. alt: 0, az: 0), the axes are aligned as follows:

    *   z-axis: aligned with the telescope's optical axis, pointing North.
    *   x-axis: perpendicular to the optical axis, pointing downward.
    *   y-axis: perpendicular to the optical axis, pointing west.

    Parameters
    ----------
    altitude : float
        Altitude angle of the telescope pointing, in degrees.
    azimuth : float
        Azimuth angle of the telescope pointing, in degrees. Measured from North, increasing towards East.

    Returns
    -------
    R : ndarray, shape (3, 3)
        Rotation matrix. When a vector in the local reference frame is multiplied by this matrix
        it is transformed into the telescope reference frame.

    Notes
    -----
    This is a simple rotation of the CORSIKA reference frame that move the up-vector (z) into the telescope direction.

    """
    theta = np.radians(90-altitude)
    phi = -np.radians(azimuth)

    ct = np.cos(theta)
    st = np.sin(theta)
    cp = np.cos(phi)
    sp = np.sin(phi)

    # pointing north (0,0)
    #  z axis is pointing north (local x axis)
    #  x axis is pointing down (opposite to local z axis)
    #  y axis is pointing west (local y axis)
    R = np.array([
        [ct*cp, ct*sp, -st],
        [  -sp,    cp,   0],
        [st*cp, st*sp,  ct]
    ])
    return R.T

# TODO: the default custom roration is the ASTRI one. Maybe this should be removed
def local_to_telescope_rotation(altitude: float, azimuth: float, custom_rotation=None) -> np.ndarray:
    """Compute the rotation matrix to transform from the local reference frame (North-West-Up) to the telescope reference frame.

    The telescope reference frame is defined such that when the telescope is
    pointing at the horizon towards the North (i.e. alt: 0, az: 0), the axes are aligned as follows:

    *   z-axis: Aligned with the telescope's optical axis and pointing North.
    *   x-axis: Perpendicular to the optical axis, lying in the horizontal plane and pointing West.
    *   y-axis: Perpendicular to the optical axis, pointing upwards.

    Parameters
    ----------
    altitude : float
        Altitude angle of the telescope pointing, in degrees.
    azimuth : float
        Azimuth angle of the telescope pointing, in degrees. Measured from North, increasing towards East.

    Returns
    -------
    R : ndarray, shape (3, 3)
        Rotation matrix. When a vector in the local reference frame is multiplied by this matrix
        it is transformed into the telescope reference frame.
    """
    # Rotation into the local reference frame
    R = local_to_pointing_rotation(altitude, azimuth).T

    # Rotation around the new z axis
    if custom_rotation is None:
        # Pointing north (0,0):
        #  z axis is pointing north (local x axis)
        #  x axis is pointing west (local y axis)
        #  y axis is pointing up (local z axis)
        custom_rotation = np.array([
            [ 0, 1, 0],
            [-1, 0, 0],
            [ 0, 0, 1]
        ])

    # rot @ R transforms from the telescope to the local frame
    # and we want the opposite
    return (custom_rotation @ R).T

def photon_to_local_rotation(a: np.ndarray) -> np.ndarray:
    """Compute the rotation matrix to transform from the photon reference frame to the local reference frame.

    The photon reference frame is defined as follows:
    ...TODO...
    
    Parameters
    ----------
    a : ndarray, shape (3,)
        Photon direction unit vector in the local reference frame.

    Returns
    -------
    R : ndarray, shape (3, 3)
        Rotation matrix. When a vector in the photon reference frame is multiplied by this matrix
        it is transformed into the local reference frame.
    """
    # Rotate `a` into [0,0,1]
    R = np.array([
        [1 + a[2] - a[0]**2, -a[0] * a[1], a[0] + a[0] * a[2]],
        [-a[0] * a[1], 1 + a[2] - a[1]**2, a[1] + a[1] * a[2]],
        [-a[0] - a[0] * a[2], -a[1] - a[1] * a[2], 1. + a[2] - a[0]**2 - a[1]**2]
    ]) / (1. + a[2])
    return R.T

def local_to_telescope_transform(
        ps: list | tuple | np.ndarray,
        vs: list | tuple | np.ndarray,
        altitude: float, azimuth: float,
        p0: list | tuple | np.ndarray
    ):
    """Transform positions and directions from the local reference frame 
    into the telescope reference frame given the telescope pointing direction and position.

    Parameters
    ----------
    ps : list, tuple, or numpy.ndarray
        Photon positions.
    vs : list, tuple, or numpy.ndarray
        Photon directions.
    altitude : float
        Telescope altitude angle in degree.
    azimut : float
        Telescope azimuth angle in degree.
    p0 : list, tuple, or numpy.ndarray
        Telescope position.
    
    Returns
    -------
    tel_ps : numpy.ndarray
        Array of transformed photon positions in the telescope coordinate system.
    tel_vs : numpy.ndarray
        Array of transformed photon direction vectors in the telescope coordinate system.

    """
    tel_ps = np.array(ps, copy=True)
    dtype = tel_ps.dtype
    tel_vs = np.array(vs, copy=True, dtype=dtype)
    tel_p0 = np.array(p0, copy=True, dtype=dtype)

    R = local_to_telescope_rotation(altitude, azimuth).astype(dtype)
    tel_ps -= tel_p0
    tel_ps = tel_ps @ R
    tel_vs = tel_vs @ R

    return tel_ps, tel_vs

def telescope_to_local_transform(
        ps: list | tuple | np.ndarray,
        vs: list | tuple | np.ndarray,
        altitude: float, azimuth: float,
        p0: list | tuple | np.ndarray
    ):
    """Transform positions and directions from the telescope reference frame 
    into the local reference frame given the telescope pointing direction and position.

    Parameters
    ----------
    ps : list, tuple, or numpy.ndarray
        Photon positions.
    vs : list, tuple, or numpy.ndarray
        Photon directions.
    altitude : float
        Telescope altitude angle in degree.
    azimut : float
        Telescope azimuth angle in degree.
    p0 : list, tuple, or numpy.ndarray
        Telescope position.
    
    Returns
    -------
    loc_ps : numpy.ndarray
        Array of transformed photon positions in the local coordinate system.
    loc_vs : numpy.ndarray
        Array of transformed photon direction vectors in the local coordinate system.

    """
    loc_ps = np.array(ps, copy=True)
    dtype = loc_ps.dtype
    loc_vs = np.array(vs, copy=True, dtype=dtype)
    loc_p0 = np.array(p0, copy=True, dtype=dtype)

    R = local_to_telescope_rotation(altitude, azimuth).T.astype(dtype)
    loc_ps = loc_ps @ R
    loc_vs = loc_vs @ R
    loc_ps += loc_p0

    return loc_ps, loc_vs

def moller_hughes_rotation(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Moller-Hughes rotation matrix to rotate the versor `a` into a nearly parallel versor `b`.

    This function computes a rotation matrix that rotates a vector `a` into
    another vector `b`, where `a` and `b` are expected to be nearly parallel.
    It uses the Moller-Hughes algorithm, which is numerically stable for this
    specific case.

    Parameters
    ----------
    a : ndarray, shape (3,)
        The initial unit vector (versor) to be rotated.
    b : ndarray, shape (3,)
        The target unit vector (versor) onto which `a` should be rotated.

    Returns
    -------
    R : ndarray, shape (3, 3)
        Rotation matrix that describes the rotation transform: `R @ a` will be
        approximately equal to `b`.

    Raises
    ------
    RuntimeError
        If the algorithm fails to find a suitable rotation axis, which can happen
        if the input vectors are not nearly parallel or if they are not normalized.
    """
    # Check for normalization
    if not np.isclose(np.linalg.norm(a), 1.0) or not np.isclose(np.linalg.norm(b), 1.0):
        raise ValueError("Input vectors 'a' and 'b' must be unit vectors.")

    if (np.abs(a[0]) < np.abs(a[1])) and (np.abs(a[0]) < np.abs(a[2])):
        p = np.array([1., 0., 0.])
    elif (np.abs(a[1]) < np.abs(a[0])) and (np.abs(a[1]) < np.abs(a[2])):
        p = np.array([0., 1., 0.])
    # Maybe get rid of this since this function is always called for directions near to (0,0,-1)
    elif (np.abs(a[2]) < np.abs(a[0])) and (np.abs(a[2]) < np.abs(a[1])):
        p = np.array([0., 0., 1.])
    else:
        raise RuntimeError(
            f"Moller-Hughes algorithm failed to find a suitable rotation axis. "
            f"Input vectors: a = {a}, b = {b}. "
            f"This might be due to the vectors not being nearly parallel or an issue with the choice of 'p'."
        )

    u = p - a
    v = p - b
    u2 = np.dot(u, u)
    v2 = np.dot(v, v)
    uv = np.dot(u, v)
    R = np.identity(3) - 2. / u2 * np.outer(u, u) - 2. / v2 * np.outer(v, v) + 4. * uv / u2 / v2 * np.outer(v, u)
    return R