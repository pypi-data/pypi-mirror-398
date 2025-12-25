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
import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass, field
from tabulate import tabulate
from typing import Optional, Iterator, Dict, ClassVar, Union
import keyword

from ._air_refractive_index import calculate_ciddor_rindex

def calculate_ciddor_1996_std_air(wavelength_nm: NDArray[np.float64]) -> NDArray[np.float64]:
    """Calculates the refractive index of standard air using the Ciddor 1996 equation.
    Standard conditions: 15 °C, 101325 Pa, 0% RH, 400 ppm CO2.
    Valid for vacuum wavelength from 230 nm to 1690 nm.

    Parameters
    ----------
    wavelength_nm : NDArray[np.float64]
        Wavelength (in nm).

    Returns
    -------
    NDArray[np.float64]
        Refractive index.
    """

    # um^-2 constants
    k_0 = 238.0185
    k_1 = 5792105
    k_2 = 57.362
    k_3 = 167917
    wavelength_um = wavelength_nm / 1000.0
    inv_wavelength_um_sq = (1.0 / wavelength_um)**2

    refractivity = (k_1 / (k_0 - inv_wavelength_um_sq)) + (k_3 / (k_2 - inv_wavelength_um_sq))
    n = refractivity/1e8 + 1.
    return n

def calculate_fused_silica_sellmeier(wavelength_nm: NDArray[np.float64]) -> NDArray[np.float64]:
    """
    Calculates the refractive index of Fused Silica using the Sellmeier
    equation with coefficients from Malitson (1965).
    Valid for vacuum wavelength from 0.21 um to 3.71 um.

    Parameters
    ----------
    wavelength_nm : NDArray[np.float64]
        Wavelength (in nm).

    Returns
    -------
    NDArray[np.float64]
        Refractive index.
    """
    # Sellmeier coefficients from Malitson (1965)
    B1 = 0.6961663
    C1 = 0.0684043**2 # um^2
    B2 = 0.4079426
    C2 = 0.1162414**2 # um^2
    B3 = 0.8974794
    C3 = 9.896161**2  # um^2

    # Convert wavelength from nm to um
    wavelength_um = wavelength_nm / 1000.0
    wavelength_um_sq = wavelength_um**2

    # Calculate n^2 - 1
    term1 = B1 * wavelength_um_sq / (wavelength_um_sq - C1)
    term2 = B2 * wavelength_um_sq / (wavelength_um_sq - C2)
    term3 = B3 * wavelength_um_sq / (wavelength_um_sq - C3)
    n_sq_minus_1 = term1 + term2 + term3

    n_sq = n_sq_minus_1 + 1.0
    n = np.sqrt(np.maximum(0, n_sq))
    return n

@dataclass
class RefractiveIndexTexture:
    """
    Holds the texture object and metadata for refractive index lookups.
    It retains a reference to the underlying CUDA array to prevent
    premature garbage collection.
    """
    texture: cp.cuda.texture.TextureObject
    wavelength_start: float
    wavelength_inv_step: float
    
    _cuda_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)

@dataclass(frozen=True)
class Material:
    name: str
    value: int
    wavelength: Optional[NDArray[np.float64]] = field(default=None, repr=False) # nm
    n: Optional[NDArray[np.float64]] = field(default=None, repr=False)
    
    def __repr__(self):
        return f"<Material: {self.name} (value={self.value})>"
        
    def get_refractive_index(self, wavelength_nm: Union[float, np.ndarray]) -> Union[float, np.ndarray, None]:
        if self.wavelength is None or self.n is None:
            return None

        result = np.interp(wavelength_nm, self.wavelength, self.n, left=np.nan, right=np.nan)
        
        # If input is a scalar and the result is NaN (out of bounds), return None.
        if np.isscalar(wavelength_nm) and np.isnan(result):
            return None

        return result
    
    def get_refractive_index_texture(self):
        # Texture Setup
        width = len(self.wavelength)
        texture_data = self.n.astype(np.float32)
        
        # Create a CUDAarray for the 1D texture
        desc = cp.cuda.texture.ChannelFormatDescriptor(32, 0, 0, 0, cp.cuda.runtime.cudaChannelFormatKindFloat)
        cu_array = cp.cuda.texture.CUDAarray(desc, width)
        cu_array.copy_from(texture_data)
        
        # Create another texture object (Linear Interpolation)
        res_desc_linear = cp.cuda.texture.ResourceDescriptor(
        cp.cuda.runtime.cudaResourceTypeArray,
        cuArr=cu_array
        )
        tex_desc_linear = cp.cuda.texture.TextureDescriptor(
            addressModes = (cp.cuda.runtime.cudaAddressModeClamp,),
            filterMode = cp.cuda.runtime.cudaFilterModeLinear,
            readMode = cp.cuda.runtime.cudaReadModeElementType,
            normalizedCoords = False
        )

        wl_start = self.wavelength[0]
        wl_inv_step = 1./(self.wavelength[1]-self.wavelength[0])
        tex_obj = cp.cuda.texture.TextureObject(res_desc_linear, tex_desc_linear)

        return RefractiveIndexTexture(
            texture=tex_obj,
            wavelength_start=wl_start,
            wavelength_inv_step=wl_inv_step,
            _cuda_array=cu_array
        )

class MaterialsMeta(type):
    """
    Metaclass for the Materials class.

    Manages the registration of materials and dynamically adds registered materials as class attributes.
    Material uniqueness and overwriting are based on the standardized attribute name (e.g., 'AIR').
    """
    _registry: ClassVar[Dict[int, Material]] = {} # Maps integer value -> Material
    _name_registry: ClassVar[Dict[str, Material]] = {} # Maps standardized name string -> Material
    _next_value: ClassVar[int] = 0 # Counter for assigning unique values

    def __str__(cls):
        if not cls._registry:
            return "<Materials: (No materials registered)>"
        return ", ".join(str(material) for material in cls._members())

    def __repr__(cls):
        if not cls._registry:
            return "<Materials: (No materials registered)>"
        return f"<Materials: {', '.join(repr(material) for material in cls._members())}>"

    def _repr_html_(cls):
        if not cls._registry:
            return "<p><b>Materials:</b> (No materials registered)</p>"
        return cls._to_table(tablefmt="html")

    def _repr_markdown_(cls):
        if not cls._registry:
            return "**Materials:** (No materials registered)"
        return cls._to_table(tablefmt="pipe")

    def _to_table(cls, tablefmt="html") -> str:
        table_data = [[material.name, material.value] for material in cls._members()]
        return tabulate(table_data, headers=["Material Name (Standardized)", "Key"], tablefmt=tablefmt)
    
    def _members(cls) -> Iterator[Material]:
        """Returns an iterator over registered Material instances, sorted by value."""
        return iter(sorted(cls._registry.values(), key=lambda m: m.value))

    def register_material(cls,
                          input_name: str,
                          wavelengths_nm: NDArray[np.float64],
                          n: NDArray[np.float64],
                          overwrite: bool = False) -> Material:
        """
        Registers a new material or updates an existing one based on its
        standardized attribute name (e.g., 'AIR', 'FUSED_SILICA').

        The standardized name (uppercase, underscores) is used for uniqueness checks 
        and as the `name` attribute of the created Material object.
        If overwrite=True, it replaces the material with the same standardized name
        in the registry and updates the corresponding class attribute.

        Parameters
        ----------
        input_name : str
            The input name for the material (e.g., "Air", "Fused Silica").
            This will be standardized internally.
        wavelengths_nm : NDArray[np.float64]
            1D NumPy array of wavelengths in nanometers. Must be sorted ascending
            with uniform spacing.
        n : NDArray[np.float64]
            1D NumPy array of refractive indices corresponding to wavelengths_nm.
            Must have the same shape as wavelengths_nm.
        overwrite : bool, optional
            If True, allows overwriting an existing material with the same
            standardized name. Defaults to False.

        Returns
        -------
        Material
            The registered or updated Material instance.

        Raises
        ------
        TypeError
            If wavelengths_nm or n are not 1D NumPy arrays.
        ValueError
            If shapes mismatch, less than two data points are provided,
            wavelengths are not sorted ascending, wavelengths do not have
            uniform spacing or a valid attribute name cannot be generated.
        KeyError
            If a material with the same standardized name exists and overwrite is False.
        """
        standardized_name = cls._generate_attribute_name(input_name)

        if not isinstance(wavelengths_nm, np.ndarray) or not isinstance(n, np.ndarray):
            raise TypeError("Inputs 'wavelengths_nm' and 'n' must be NumPy arrays.")
        
        if wavelengths_nm.ndim != 1 or n.ndim != 1:
            raise ValueError("Inputs 'wavelengths_nm' and 'n' must be 1D.")
        
        if wavelengths_nm.shape != n.shape:
            raise ValueError(f"Shape mismatch: {wavelengths_nm.shape} vs {n.shape}.")
        
        if len(wavelengths_nm) < 2:
            raise ValueError("Need at least two data points for interpolation.")
        
        diffs = np.diff(wavelengths_nm)
        if not np.all(diffs > 0):
            raise ValueError("Wavelengths must be sorted in strictly ascending order.")
        
        if len(diffs) > 0 and not np.allclose(diffs, diffs[0], rtol=1e-4, atol=1e-3):
             raise ValueError(f"Wavelengths should be uniformly spaced.")

        existing_material = cls._name_registry.get(standardized_name)
        value = None

        if existing_material:
            if not overwrite:
                raise KeyError(f"Material with standardized name '{standardized_name}' (derived from '{input_name}') already exists (value={existing_material.value}). Use overwrite=True to replace.")
            else:
                value = existing_material.value
        else:
            value = cls._next_value
            cls._next_value += 1

        new_material = Material(
            name=standardized_name,
            value=value,
            wavelength=wavelengths_nm.copy(),
            n=n.copy()
        )

        cls._registry[value] = new_material
        cls._name_registry[standardized_name] = new_material

        setattr(cls, standardized_name, new_material)

        return new_material

    @staticmethod
    def _generate_attribute_name(name: str) -> str:
        """
        Generates a valid Python attribute name from a material name.
        Converts to uppercase, replaces spaces/hyphens with underscores,
        removes invalid characters, ensures it doesn't start with a digit,
        and avoids Python keywords.
        """
        if not isinstance(name, str) or not name:
             raise ValueError("Input name must be a non-empty string.")
        
        # Convert to uppercase and replace common separators
        attr_name = name.upper().replace(' ', '_').replace('-', '_')

        # Keep only alphanumeric characters and underscores
        attr_name = ''.join(c for c in attr_name if c.isalnum() or c == '_')

        # Remove leading/trailing underscores that might result from replacements
        attr_name = attr_name.strip('_')

        if not attr_name:
            raise ValueError(f"Cannot generate a valid attribute name from '{name}' after cleaning.")
        
        # Ensure it doesn't start with a digit
        if attr_name[0].isdigit():
            attr_name = '_' + attr_name
        
        # Check again just in case strip resulted in empty or invalid start
        if not (attr_name[0].isalpha() or attr_name[0] == '_'):
             raise ValueError(f"Cannot generate a valid attribute name from '{name}' (invalid start '{attr_name[0]}').")
        
        # Avoid collision with Python reserved keywords
        if keyword.iskeyword(attr_name):
            attr_name += '_'
        
        return attr_name
    
class Materials(metaclass=MaterialsMeta):
    """
    A collection of Material instances with refractive index data (wavelength in nm).
    Includes default materials: Air (Ciddor 1996) and Fused Silica (Malitson 1965).

    New materials can be added using the ``register_material()`` method:

    .. code-block::python

        Materials.register_material("MyAir", my_wavelength, my_n)
        print(Materials)
    
    You can also replace a material, for example the air refractive index:

    .. code-block::python

        Materials.register_material("Air", my_wavelength, my_n, overwrite=True)
        print(Materials)
    
    To register a refractive index for air, a ``set_atmospheric_conditions()`` method is provied.
    It uses the Ciddor equation following the NIST implementation:

    .. code-block::python

        Materials.set_atmospheric_condition(
            76.38e3, # pressure (Pa)
            20., # air temperatur (degrees Celsius)
            450., # CO2 concentration (ppm)
            10., # relative humidity (%)
            lambda_min=230., # lambda range (in nm)
            lambda_max=1700. #
        )
    
    """
    @classmethod
    def set_atmospheric_conditions(
        cls,
        pressure: float = 101325.,
        temperature: float = 20.,
        co2_concentration: float = 450.,
        relative_humidity: Optional[float] = 0.,
        lambda_min: float = 200.,
        lambda_max: float = 1700.,
    ) -> None:
        """Calculate the refractive index of moist air using the Ciddor equation and update the default air material.

        Follows the NIST implementation described by `Jack A. Stone and
        Jay H. Zimmerman <https://emtoolbox.nist.gov/Wavelength/Documentation.asp>`_.

        Parameters
        ----------
        pressure : float
            Air pressure in Pascals.
        temperature : float
            Air temperature in degrees Celsius.
        co2_concentration : float
            CO2 concentration in micromoles per mole (µmol/mol), equivalent to ppm.
        relative_humidity : Optional[float]
            Relative humidity in percent (%). If None, assumes dry air (xv = 0).
        lambda_min: float, Optional[float]
            Minimum photon wavelength (in nm).
        lambda_max: float, Optional[float]
            Maximum photon wavelength (in nm).

        Notes
        -----
            NIST implementation is valid in the range 300 nm - 1700 nm.

        """
        _wl_air_nm = np.arange(lambda_min, lambda_max+1., 1., dtype=np.float64)
        _n_air = calculate_ciddor_rindex(
            lambda_vac=_wl_air_nm,
            p=pressure,
            t=temperature,
            xCO2=co2_concentration,
            rh=relative_humidity
        )
        cls.register_material("Air", _wl_air_nm, _n_air, overwrite=True)

# Air (using Ciddor 1996 for standard air, 230 nm - 1690 nm)
_wl_air_nm = np.arange(200., 1690.+1., 1., dtype=np.float64)
_n_air = calculate_ciddor_1996_std_air(_wl_air_nm)

# Fused Silica (using Malitson 1965, 210 nm - 3710 nm)
_wl_silica_nm = np.arange(200., 3710.+1., 1., dtype=np.float64)
_n_silica = calculate_fused_silica_sellmeier(_wl_silica_nm)

Materials.register_material("Air", _wl_air_nm, _n_air)
Materials.register_material("Fused Silica", _wl_silica_nm, _n_silica)