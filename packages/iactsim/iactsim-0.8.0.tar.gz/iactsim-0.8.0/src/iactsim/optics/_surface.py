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
from tabulate import tabulate
from typing import Tuple, Optional, Any
from numpy.typing import ArrayLike

from ._sag import sag
from ._surface_misc import SurfaceType, ApertureShape, SurfaceProperties, SurfaceShape
from ._materials import Material, Materials

class Surface:
    """Represents an optical surface.

        Parameters
        ----------
        type : SurfaceType
            Type of surface (reflective, refractive, opaque, dummy)
        position : array-like, optional
            Position of the surface center [x, y, z], by default None
        tilt_angles : array-like, optional
            Tilt angles (clockwise x-tilt, y-tilt and z_tild) in degrees, by default no tilt.
        scattering_dispersion : float, optional
            Standard deviation of Gaussian scattering after reflection/transmission, by default 0.0
        properties : SurfaceProperties, optional
            Reflectance/transmittance properties of the surface, by default None
        material_in : material, optional
            Material of the space before the surface front side. I.e. the material in which
            photons arriving with a negative z-component of their direction vector are travelling, 
            by default standard air.
        material_out : material, optional
            Material of the space after the surface back side. I.e. the material in which
            photons arriving with a positive z-component of their direction vector are travelling, 
            by default standard air.
        name : str, optional
            Surface name
    """

    def __init__(self,
                 surface_type: SurfaceType,
                 position: ArrayLike = np.array([0., 0., 0.]),
                 tilt_angles: ArrayLike = np.array([0., 0., 0.]),
                 scattering_dispersion: float = 0.0,
                 properties: Optional[SurfaceProperties] = None,
                 material_in: Material = Materials.AIR,
                 material_out: Material = Materials.AIR,
                 name: Optional[str] = None):
        self.type = surface_type
        self.position = position
        self.tilt_angles = tilt_angles
        self.scattering_dispersion = scattering_dispersion
        self.properties = properties if properties is not None else SurfaceProperties()
        self.material_in = material_in
        self.material_out = material_out
        self.name = name

        self._custom_rotation_matrix = None

    @property
    def axial_position(self) -> float:
        return self._axial_position

    @axial_position.setter
    def axial_position(self, value: float):
        self._axial_position = value
        self._position[-1] = value

    @property
    def position(self) -> np.ndarray:
        return self._position

    @position.setter
    def position(self, value: np.ndarray):
        self._position = np.asarray(value)
        self._axial_position = value[-1]
    
    def get_rotation_matrix(self) -> np.ndarray:
        """
        Calculates the 3D rotation matrix to transform into the surface reference system.
        The computation is based on surface tilt angles and assumes rotations 
        are applied in the order (last first): Z @ Y @ X. Each rotation and follow the right-hand rule. 
        Tilt angles are expected in degrees.

        A custom rotation matrix will be used if it has been set using :py:meth:`set_rotation_matrix` method.
        
        Returns
        -------
            np.ndarray: A 3x3 rotation matrix.
        """
        # Return the custom rotation matrix if has been defined
        if self._custom_rotation_matrix is not None:
            return self._custom_rotation_matrix

        x_tilt_rad, y_tilt_rad, z_tilt_rad = np.deg2rad(self.tilt_angles)
        cos_x = np.cos(x_tilt_rad)
        sin_x = np.sin(x_tilt_rad)
        cos_y = np.cos(y_tilt_rad)
        sin_y = np.sin(y_tilt_rad)
        cos_z = np.cos(z_tilt_rad)
        sin_z = np.sin(z_tilt_rad)

        x_rot = np.array([
            [1.0,    0.,     0.],
            [ 0., cos_x, -sin_x],
            [ 0., sin_x,  cos_x]
        ])

        y_rot = np.array([
            [ cos_y,  0., sin_y],
            [    0.,  1.,    0.],
            [-sin_y,  0., cos_y]
        ])

        z_rot = np.array([
            [ cos_z, -sin_z, 0.],
            [ sin_z,  cos_z, 0.],
            [    0.,     0., 1.],
        ])

        return  (z_rot @ y_rot @ x_rot).T
    
    def set_rotation_matrix(self, a_matrix):
        """Set a custom rotation matrix instead of deriving it from tilt angles.
        To use tilt angles set it to ``None``.

        Parameters
        ----------
        a_matrix : np.ndarray
            3D rotation matrix to transform from telescope to surface reference frame.
        """
        self._custom_rotation_matrix = a_matrix
    
    def __repr__(self) -> str:
        """Returns a string representation of the AsphericalSurface object."""
        return f"{self.__class__.__name__}(half_aperture={self.type}, ...)"
    
    def _table_data(self) -> list[list[Any]]:
        """Helper function to generate data for table representation."""
        table = []
        if self.name is not None:
            table.append(["Name", self.name])
        table += [
            ["Surface Type", self.type],
            ["Position", ', '.join([f'{x:.2f}' for x in self.position])],
            ["Tilt Angles", ', '.join([f'{x:.2f}' for x in self.tilt_angles])],
            ["Scattering Sigma", self.scattering_dispersion],
            ["Properties wavelegth", "set" if self.properties.wavelength is not None else "not set"],
            ["Properties incidence angle", "set" if self.properties.incidence_angle is not None else "not set"],
            ["Transmittance value", "set" if self.properties.transmittance is not None else "not set"],
            ["Reflectance value", "set" if self.properties.reflectance is not None else "not set"],
            ["Absorption value", "set" if self.properties.absorption is not None else "not set"],
        ]
        return table

    def __str__(self) -> str:
        """Returns a string representation of the AsphericalSurface object formatted as a table."""
        return tabulate(self._table_data(), headers=["Attribute", "Value"], tablefmt="fancy_grid")
    
    def _repr_markdown_(self) -> str:
        """Returns a Markdown representation of the AsphericalSurface object."""
        return tabulate(self._table_data(), headers=["Attribute", "Value"], tablefmt="pipe")

    def _repr_html_(self) -> str:
        """Returns an HTML representation of the AsphericalSurface object."""
        return tabulate(self._table_data(), headers=["Attribute", "Value"], tablefmt="html")

class AsphericalSurface(Surface):
    """Represents an aspherical optical surface.

        Parameters
        ----------
        half_aperture : float
            Half-aperture of the surface.
        curvature : float
            Surface curvature (1/radius of curvature)
        conic_constant : float
            Conic constant
        aspheric_coefficients : array-like
            Array of aspheric coefficients
        central_hole_half_aperture : float, optional
            Half-aperture of the central hole (0.0 if no hole), by default 0.0
        aperture_shape : ApertureShape, optional
            Shape of the aperture (circular, hexagonal or rectangular), by default ApertureShape.CIRCULAR
        is_fresnel : bool, optional
            Whether the surface is an ideal Fresnel lens/mirror, by default False
        surface_type : SurfaceType, optional
            Type of surface (reflective, refractive, opaque, dummy), by default SurfaceType.REFLECTIVE
        position : array-like, optional
            Position of the surface center [x, y, z], by default None
        tilt_angles : array-like, optional
            Tilt angles (clockwise x-tilt, y-tilt and z_tild) in degrees, by default no tilt.
        scattering_dispersion : float, optional
            Standard deviation of Gaussian scattering after reflection/transmission, by default 0.0
        properties : SurfaceProperties, optional
            Reflectance/transmittance properties of the surface, by default None
        material_in : material, optional
            Material of the space before the surface front side. I.e. the material in which
            photons arriving with a negative z-component of their direction vector are travelling, 
            by default standard air.
        material_out : material, optional
            Material of the space after the surface back side. I.e. the material in which
            photons arriving with a positive z-component of their direction vector are travelling, 
            by default standard air.
        name : str, optional
            Surface name
    """

    def __init__(self,
                 half_aperture: float,
                 curvature: float,
                 conic_constant: float,
                 aspheric_coefficients: ArrayLike,
                 central_hole_half_aperture: float = 0.0,
                 aperture_shape: ApertureShape = ApertureShape.CIRCULAR,
                 central_hole_shape: ApertureShape = ApertureShape.CIRCULAR,
                 is_fresnel: bool = False,
                 surface_type: SurfaceType = SurfaceType.REFLECTIVE,
                 position: ArrayLike = np.array([0., 0., 0.]),
                 tilt_angles: ArrayLike = np.array([0., 0., 0.]),
                 scattering_dispersion: float = 0.0,
                 properties: Optional[SurfaceProperties] = None,
                 material_in: Material = Materials.AIR,
                 material_out: Material = Materials.AIR,
                 name: Optional[str] = None):
        super().__init__(
            surface_type,
            position,
            tilt_angles,
            scattering_dispersion,
            properties,
            material_in,
            material_out,
            name
        )
        self.half_aperture = half_aperture
        self.curvature = curvature
        self.conic_constant = conic_constant
        self.aspheric_coefficients = np.asarray(aspheric_coefficients)
        self.central_hole_half_aperture = central_hole_half_aperture
        self.central_hole_shape = central_hole_shape
        self.aperture_shape = aperture_shape
        self.is_fresnel = is_fresnel
        self.offset = np.array([0.,0.])
        """Treat the surface as a segment centered at these aperture coordinates."""
        self._shape = SurfaceShape.ASPHERICAL

    def _validate(self):
        """Validates the internal consistency of the surface parameters."""
        name_str = "-".join([self.name,""]) if self.name is not None else ""
        if not self.half_aperture > 0:
            raise ValueError("".join([name_str, "Half-aperture must be positive."]))
        if not self.central_hole_half_aperture >= 0:
            raise ValueError("".join([name_str, "Half-aperture of the central hole cannot be negative."]))
        if not self.central_hole_half_aperture < self.half_aperture:
            raise ValueError("".join([name_str, "Half-aperture of the central must be less than surface half-aperture."]))
        if not self.aspheric_coefficients.ndim == 1:
            raise ValueError("".join([name_str, "Aspheric coefficients must be a 1D array."]))

    @property
    def aspheric_coefficients(self) -> np.ndarray:
        return self._aspheric_coefficients

    @aspheric_coefficients.setter
    def aspheric_coefficients(self, value: np.ndarray):
        if not isinstance(value, np.ndarray):
            value = np.asarray(value, dtype=np.float64)
        if len(value) > 10:
            raise(ValueError("Aspheric surfaces can be defined by a maximum of 10 aspheric coefficients."))
        self._aspheric_coefficients = value

    def sagitta(self, r: np.ndarray) -> np.ndarray:
        """Calculate the sagitta of the aspheric surface at a given radial distance in the surface refrence frame.

        Parameters
        ----------
        r : np.ndarray, list or scalar
            Radial distance(s) from the optical axis.

        Returns
        -------
        np.ndarray
            Sagitta value(s) at the given radial distance(s).
        """

        return sag(r, self.curvature, self.conic_constant, self.aspheric_coefficients, 0., self.is_fresnel)

    def get_surface_normal_vector(self, x: float, y: float) -> np.ndarray:
        """Calculate the upward-going normal unit vector at a given surface point (x,y) in the surface reference frame.

        Parameters
        ----------
        x : float
            x coordinate of the point.
        y : float
            y coordinate of the point.

        Returns
        -------
        np.ndarray
            Normal unit vector.
        """
        n = np.array([0,0,1.])

        # Flat
        if (np.abs(self.curvature) < 1e-10): 
            return n
        
        r2 = x*x+y*y

        # Aspheric component
        tot_aspher = 0.
        for i in range(len(self.aspheric_coefficients)):
            tot_aspher += 2 * (i+1) * self.aspheric_coefficients[i] * np.power(r2, i)

        arg_sqrt = 1-(1.0 + self.conic_constant) * self.curvature*self.curvature * r2
        if arg_sqrt < 0:
            raise(ValueError('Surface not well defined at the given point.'))
        
        fact = self.curvature / np.sqrt(arg_sqrt) + tot_aspher

        n[0] = - fact * x
        n[1] = - fact * y
        norm = np.sqrt(n[0]*n[0]+n[1]*n[1]+1.)

        return n/norm
    
    def __repr__(self) -> str:
        """Returns a string representation of the AsphericalSurface object."""
        return f"{self.__class__.__name__}(half_aperture={self.half_aperture}, curvature={self.curvature}, ...)"
    
    def _table_data(self) -> list[list[Any]]:
        """Helper function to generate data for table representation."""
        table = []
        if self.name is not None:
            table.append(["Name", self.name])
        table += [
            ["Half-Aperture", f'{self.half_aperture:.2f}'],
            ["Curvature", f'{self.curvature:.9f}'],
            ["Conic Constant", f'{self.conic_constant:.2f}'],
            ["# Aspheric Coefficients", len(self.aspheric_coefficients)],
            ["Central Hole Half-Aperture", f'{self.central_hole_half_aperture:.2f}'],
            ["Aperture Shape", self.aperture_shape],
            ["Central Hole Shape", self.central_hole_shape],
            ["Is Fresnel", self.is_fresnel],
            ["Surface Type", self.type],
            ["Position", ', '.join([f'{x:.2f}' for x in self.position])],
            ["Tilt Angles", ', '.join([f'{x:.2f}' for x in self.tilt_angles])],
            ["Scattering Sigma", f'{self.scattering_dispersion:.3f}'],
            ["Properties wavelegth", "set" if self.properties.wavelength is not None else "not set"],
            ["Properties incidence angle", "set" if self.properties.incidence_angle is not None else "not set"],
            ["Transmittance value", "set" if self.properties.transmittance is not None else "not set"],
            ["Reflectance value", "set" if self.properties.reflectance is not None else "not set"],
            ["Absorption value", "set" if self.properties.absorption is not None else "not set"],
        ]
        return table

class FlatSurface(AsphericalSurface):
    """Represents a flat optical surface.

        Parameters
        ----------
        half_aperture : float
            Half-aperture of the surface.
        central_hole_half_aperture : float, optional
            Half-aperture of the central hole (0.0 if no hole), by default 0.0
        aperture_shape : ApertureShape, optional
            Shape of the aperture (circular, hexagonal or rectangular), by default ApertureShape.CIRCULAR
        surface_type : SurfaceType, optional
            Type of surface (reflective, refractive, opaque, dummy), by default SurfaceType.REFLECTIVE
        position : array-like, optional
            Position of the surface center [x, y, z], by default None
        tilt_angles : array-like, optional
            Tilt angles (clockwise x-tilt, y-tilt and z_tild) in degrees, by default no tilt.
        scattering_dispersion : float, optional
            Standard deviation of Gaussian scattering after reflection/transmission, by default 0.0
        properties : SurfaceProperties, optional
            Reflectance/transmittance properties of the surface, by default None
        material_in : material, optional
            Material of the space before the surface front side. I.e. the material in which
            photons arriving with a negative z-component of their direction vector are travelling, 
            by default standard air.
        material_out : material, optional
            Material of the space after the surface back side. I.e. the material in which
            photons arriving with a positive z-component of their direction vector are travelling, 
            by default standard air.
        name : str, optional
            Surface name
    """

    def __init__(self,
                 half_aperture: float,
                 central_hole_half_aperture: float = 0.0,
                 aperture_shape: ApertureShape = ApertureShape.CIRCULAR,
                 central_hole_shape: ApertureShape = ApertureShape.CIRCULAR,
                 surface_type: SurfaceType = SurfaceType.REFLECTIVE,
                 position: ArrayLike = np.array([0., 0., 0.]),
                 tilt_angles: ArrayLike = np.array([0., 0., 0.]),
                 scattering_dispersion: float = 0.0,
                 properties: Optional[SurfaceProperties] = None,
                 material_in: Material = Materials.AIR,
                 material_out: Material = Materials.AIR,
                 name: Optional[str] = None):
        super().__init__(
            half_aperture,
            0,
            0,
            [0],
            central_hole_half_aperture,
            aperture_shape,
            central_hole_shape,
            False,
            surface_type,
            position,
            tilt_angles,
            scattering_dispersion,
            properties,
            material_in,
            material_out,
            name
        )
        self._shape = SurfaceShape.ASPHERICAL

class SphericalSurface(AsphericalSurface):
    """Represents a spherical optical surface.

        Parameters
        ----------
        half_aperture : float
            Half-aperture of the surface.
        curvature : float
            Surface curvature (1/radius of curvature)
        central_hole_half_aperture : float, optional
            Half-aperture of the central hole (0.0 if no hole), by default 0.0
        aperture_shape : ApertureShape, optional
            Shape of the aperture (circular, hexagonal or rectangular), by default ApertureShape.CIRCULAR
        is_fresnel : bool, optional
            Whether the surface is an ideal Fresnel lens/mirror, by default False
        surface_type : SurfaceType, optional
            Type of surface (reflective, refractive, opaque, dummy), by default SurfaceType.REFLECTIVE
        position : array-like, optional
            Position of the surface center [x, y, z], by default None
        tilt_angles : array-like, optional
            Tilt angles (clockwise x-tilt, y-tilt and z_tild) in degrees, by default no tilt.
        scattering_dispersion : float, optional
            Standard deviation of Gaussian scattering after reflection/transmission, by default 0.
        properties : SurfaceProperties, optional
            Reflectance/transmittance properties of the surface, by default None
        material_in : material, optional
            Material of the space before the surface front side. I.e. the material in which
            photons arriving with a negative z-component of their direction vector are travelling, 
            by default standard air.
        material_out : material, optional
            Material of the space after the surface back side. I.e. the material in which
            photons arriving with a positive z-component of their direction vector are travelling, 
            by default standard air.
        name : str, optional
            Surface name
    """

    def __init__(self,
                 half_aperture: float,
                 curvature: float,
                 central_hole_half_aperture: float = 0.,
                 aperture_shape: ApertureShape = ApertureShape.CIRCULAR,
                 central_hole_shape: ApertureShape = ApertureShape.CIRCULAR,
                 is_fresnel: bool = False,
                 surface_type: SurfaceType = SurfaceType.REFLECTIVE,
                 position: ArrayLike = np.array([0., 0., 0.]),
                 tilt_angles: ArrayLike = np.array([0., 0., 0.]),
                 scattering_dispersion: float = 0.,
                 properties: Optional[SurfaceProperties] = None,
                 material_in: Material = Materials.AIR,
                 material_out: Material = Materials.AIR,
                 name: Optional[str] = None):
        super().__init__(
            half_aperture,
            curvature,
            0,
            [0],
            central_hole_half_aperture,
            aperture_shape,
            central_hole_shape,
            is_fresnel,
            surface_type,
            position,
            tilt_angles,
            scattering_dispersion,
            properties,
            material_in,
            material_out,
            name
        )
        self._shape = SurfaceShape.ASPHERICAL


class CylindricalSurface(Surface):
    """Represents a cylindrical optical surface.

        Parameters
        ----------
        radius : float
            Radius of the cylinder.
        height : float
            Height of the cylinder.
        position : array-like, optional
            Position of cylinder center [x, y, z] (half-height on the cylinder axis), by default None.
        tilt_angles : array-like, optional
            Tilt angles (clockwise x-tilt, y-tilt and z_tild) in degrees, by default no tilt.
        surface_type : SurfaceType, optional
            Type of surface (opaque or sensitive), by default SurfaceType.OPAQUE.
        name : str, optional
            Surface name
    """

    def __init__(self,
                 radius: float,
                 height: float,
                 has_top: bool = True,
                 has_bottom: bool = True,
                 position: ArrayLike = np.array([0., 0., 0.]),
                 tilt_angles: ArrayLike = np.array([0., 0., 0.]),
                 surface_type: SurfaceType = SurfaceType.OPAQUE,
                 name: Optional[str] = None):

        scattering_dispersion = 0.
        properties = None
        material_in = Materials.AIR
        material_out = Materials.AIR
        super().__init__(
            surface_type,
            position,
            tilt_angles,
            scattering_dispersion,
            properties,
            material_in,
            material_out,
            name
        )
        self.surface_type = surface_type
        self.radius = radius
        self.height = height
        self.top = has_top
        self.bottom = has_bottom
        self._shape = SurfaceShape.CYLINDRICAL

    @property
    def surface_type(self) -> np.ndarray:
        return self._surface_type

    @surface_type.setter
    def surface_type(self, value: SurfaceType):
        if value not in [SurfaceType.OPAQUE, SurfaceType.SENSITIVE, SurfaceType.TEST_SENSITIVE]:
            raise(ValueError("Cylindical surfaces can be only `SurfaceType.OPAQUE` or `SurfaceType.SENSITIVE`."))
        self._surface_type = value
        
    def _validate(self):
        """Validates the internal consistency of the surface parameters."""
        name_str = "-".join([self.name,""]) if self.name is not None else ""
        if not self.radius > 0:
            raise ValueError("".join([name_str, "Cylinder radius must be positive."]))
        if not self.height > 0:
            raise ValueError("".join([name_str, "Cylinder height must be positive."]))
    
    def __repr__(self) -> str:
        """Returns a string representation of the AsphericalSurface object."""
        return f"{self.__class__.__name__}(radius={self.radius}, height={self.height}, top={self.top}, bottom={self.bottom}...)"
    
    def _table_data(self) -> list[list[Any]]:
        """Helper function to generate data for table representation."""
        table = []
        if self.name is not None:
            table.append(["Name", self.name])
        table += [
            ["Radius", f'{self.radius:.2f}'],
            ["Height", f'{self.height:.2f}'],
            ["Has top", self.top],
            ["Has bottom", self.bottom],
            ["Surface Type", self.type],
            ["Position", ', '.join([f'{x:.2f}' for x in self.position])],
            ["Tilt Angles", ', '.join([f'{x:.2f}' for x in self.tilt_angles])],
        ]
        return table