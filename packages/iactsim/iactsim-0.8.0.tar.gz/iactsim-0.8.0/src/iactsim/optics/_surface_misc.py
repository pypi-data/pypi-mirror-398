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

from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import cupy as cp

from ..visualization._iactsim_style import iactsim_style, MplInteractiveContext

class SurfaceType(Enum):
    """
    Enumeration representing the different types of optical surfaces.

    The directionality of reflection and sensitivity (e.g., "from above" or 
    "from below") is defined within the *local reference frame* of the surface at the point 
    of photon incidence. As a reference:

        - the front side of a surface with negative curvature is the convex side.
        - the front side of a surface with posistive curvature is the concave side.

    Attributes
    ----------
    REFLECTIVE : int
        Represents a reflective surface (both sides).
    REFLECTIVE_IN : int
        Represents a surface that is reflective on the front side. 
        In the surface's local reference frame, only photons arriving with a negative 
        z-component of their direction vector (i.e., coming "from the front", or 
        "from above" in the context of the local frame) are reflected. 
        The curvature of the surface does not affect this behavior.
    REFLECTIVE_OUT : int
        Represents a surface that is reflective on the back side. In the surface's 
        local reference frame, only photons arriving with a positive z-component of 
        their direction vector (i.e., coming "from the back", or "from below" in the 
        context of the local frame) are reflected. The curvature of the surface 
        does not affect this behavior.
    REFRACTIVE : int
        Represents a refractive surface. The refraction is the same on both sides.
    SENSITIVE : int
        Represents the focal plane surface where photons are detected. The sensitivity
        is the same on both sides.
    SENSITIVE_IN : int
        Represents a surface that is sensitive on the front side (as defined by the 
        local reference frame's positive z-axis). In the surface's local reference 
        frame, only photons arriving with a negative z-component of their direction 
        vector (i.e., coming "from the front", or "from above" in the context of the 
        local frame) are detected. The curvature of the surface does not affect 
        this behavior.
    SENSITIVE_OUT : int
        Represents a surface that is sensitive on the back side. In the surface's 
        local reference frame, only photons arriving with a positive z-component of 
        their direction vector (i.e., coming "from the back", or "from below" in the 
        context of the local frame) are detected. The curvature of the surface 
        does not affect this behavior.
    OPAQUE : int
        Represents a surface that blocks light.
    DUMMY : int
        Represents a surface that neither reflects nor refracts light. 
        It can be used to introduce artificial absorption or scattering effects, 
        serving as a means to model specific behaviors within the optical system.
    
    """
    REFLECTIVE = 0
    REFLECTIVE_IN = 1
    REFLECTIVE_OUT = 2
    REFRACTIVE = 3
    SENSITIVE = 4
    SENSITIVE_IN = 5
    SENSITIVE_OUT = 6
    OPAQUE = 7
    DUMMY = 8
    TEST_SENSITIVE = 9
    REFLECTIVE_SENSITIVE = 10

class SurfaceShape(Enum):
    """
    Enumeration representing different types of surface shapes.

    This enum defines common surface shapes encountered in optical systems or
    other fields requiring precise geometrical definitions.

    """
    ASPHERICAL = 0
    """Represents an aspherical surface."""
    CYLINDRICAL = 1
    """Represents a cylindrical surface."""
    FLAT = 2
    """Represents a flat surface."""
    SPHERICAL = 3
    """Represents a spherical surface."""

class ApertureShape(Enum):
    """
    Enumeration representing the possible shapes of an aperture.

    Attributes
    ----------
    CIRCULAR : int
        Represents a circular aperture.
    HEXAGONAL : int
        Represents a flat-top hexagonal aperture.
    SQUARE : int
        Represents a square aperture.
    HEXAGONAL_PT : int
        Represents a pointy-top hexagonal aperture.
    """
    CIRCULAR = 0
    HEXAGONAL = 1
    SQUARE = 2
    HEXAGONAL_PT = 3

@dataclass
class OpticalTextures:
    """
    Container for GPU texture objects and the metadata required to 
    map physical values (wavelength, angle) to texture coordinates.
    It can retains a reference to the underlying CUDA arrays to prevent
    premature garbage collection.
    """
    transmittance: cp.cuda.texture.TextureObject
    reflectance: cp.cuda.texture.TextureObject
    
    # Back-side textures
    transmittance_back: cp.cuda.texture.TextureObject
    reflectance_back: cp.cuda.texture.TextureObject
    
    wavelength_start: float
    wavelength_inv_step: float
    
    angle_start: float
    angle_inv_step: float

    _t_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)
    _r_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)
    
    # references for back-side arrays (if distinct from front)
    _t_back_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)
    _r_back_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)

@dataclass
class SurfaceProperties:
    """
    Represents surface transmittance, reflectance, and absorption as a function 
    of photon wavelength and incidence angle.
    """
    transmittance: np.ndarray = field(default=None, metadata={'units': 'None'})
    """A numpy.ndarray representing the front-side transmittance (0 to 1)."""
    
    reflectance: np.ndarray = field(default=None, metadata={'units': 'None'})
    """A numpy.ndarray representing the front-side reflectance (0 to 1)."""
    
    absorption: np.ndarray = field(default=None, metadata={'units': 'None'})
    """A numpy.ndarray representing the front-side absorption (0 to 1)."""

    # Back side properties
    transmittance_back: np.ndarray = field(default=None, metadata={'units': 'None'})
    """A numpy.ndarray representing the back-side transmittance (0 to 1)."""
    
    reflectance_back: np.ndarray = field(default=None, metadata={'units': 'None'})
    """A numpy.ndarray representing the back-side reflectance (0 to 1)."""
    
    absorption_back: np.ndarray = field(default=None, metadata={'units': 'None'})
    """A numpy.ndarray representing the back-side absorption (0 to 1)."""

    wavelength: np.ndarray = field(default=None, metadata={'units': 'nanometers'})
    """A NumPy ndarray representing the wavelengths in nanometers."""

    incidence_angle: np.ndarray = field(default=None, metadata={'units': 'degrees'})
    """A NumPy ndarray representing the incidence angles in degrees."""

    def __setattr__(self, key, value):
        if value is not None:
            value = np.asarray(value)
        
        # Add back properties to the allowed set
        if key in {'transmittance', 'reflectance', 'absorption', 
                   'transmittance_back', 'reflectance_back', 'absorption_back',
                   'wavelength', 'incidence_angle'}:
            super().__setattr__(key, value)
    
    @property
    def is_defined(self):
        # Front is mandatory
        values = [self.transmittance, self.absorption, self.reflectance] 
        all_values_missing = sum([x is None for x in values]) == 3
        return not all_values_missing

    def _validate_side(self, t_arr, r_arr, a_arr, side_name="Front"):
        """Helper to validate and fill missing properties for one side."""
        if sum([x is None for x in [t_arr, r_arr, a_arr]]) > 1:
            raise(ValueError("At least two properties among transmittance, reflectance and absorption must be defined."))

        if t_arr is None:
            t_arr = 1. - r_arr - a_arr
        
        if r_arr is None:
            r_arr = 1. - t_arr - a_arr
        
        if a_arr is None:
            a_arr = 1. - t_arr - r_arr
        
        # Check for negative values
        for name, arr in [('Transmittance', t_arr), ('Reflectance', r_arr), ('Absorption', a_arr)]:
            if np.any(np.asarray(arr) < -1e-9):
                raise ValueError(f"{side_name} {name} cannot contain negative values.")
            arr[arr<0] = 0.

        # Check energy conservation
        total = t_arr + r_arr + a_arr
        if np.any(total > 1.0 + 1e-9):
            max_val = np.max(total)
            raise ValueError(f"{side_name} Energy conservation violation: r + t + a > 1 (max: {max_val:.4f})")
            
        return t_arr, r_arr, a_arr

    def _validate(self):
        """
        Validation of shapes and physical constraints. Computes missing properties if possible.
        """
        wl_arr = self.wavelength
        theta_arr = self.incidence_angle
        
        if all([x is None for x in [wl_arr, theta_arr]]):
            raise(ValueError("Wavelength and incidence angle have not been defined."))

        self.transmittance, self.reflectance, self.absorption = self._validate_side(
            self.transmittance, self.reflectance, self.absorption, side_name="Front"
        )
        
        # Check if any back property is set
        back_props = [self.transmittance_back, self.reflectance_back, self.absorption_back]
        back_is_set = not all([x is None for x in back_props])

        if back_is_set:
            # Check for shape mismatch between front and back
            front_shape = self.transmittance.shape
            for arr in back_props:
                if arr is not None and arr.shape != front_shape:
                     raise ValueError("Shape mismatch between front and back optical properties.")

            self.transmittance_back, self.reflectance_back, self.absorption_back = self._validate_side(
                self.transmittance_back, self.reflectance_back, self.absorption_back, side_name="Back"
            )

    def get_optical_textures(self, get_data=False) -> OpticalTextures:
        """
        Creates CuPy texture objects for transmission and reflection.
        
        It automatically pads the data with zeros at the boundaries (if applicable)
        so that values outside the defined range fade to zero instead of clamping
        to the edge value.
        """
        self._validate()

        # Prepare data arrays
        n_wl = len(self.wavelength) if self.wavelength is not None else 1
        n_th = len(self.incidence_angle) if self.incidence_angle is not None else 1

        def prepare_data(data):
            if data is None:
                return np.zeros((n_th, n_wl), dtype=np.float32)
            arr = np.asarray(data, dtype=np.float32)
            return arr.reshape((n_th, n_wl))

        # Front
        t_data = prepare_data(self.transmittance)
        r_data = prepare_data(self.reflectance)

        # Back
        back_is_set = self.transmittance_back is not None
        if back_is_set:
            t_back_data = prepare_data(self.transmittance_back)
            r_back_data = prepare_data(self.reflectance_back)
        else:
            t_back_data = None 
            r_back_data = None

        # Wavelength padding
        wl_start = 0.0
        wl_inv_step = 0.0
        if self.wavelength is not None and n_wl > 1:
            step = float(self.wavelength[1] - self.wavelength[0])
            if step != 0:
                wl_inv_step = 1.0 / step
                wl_start = float(self.wavelength[0]) - step
                
                pad_width = ((0, 0), (1, 1))
                t_data = np.pad(t_data, pad_width, mode='constant', constant_values=0)
                r_data = np.pad(r_data, pad_width, mode='constant', constant_values=0)
                if back_is_set:
                    t_back_data = np.pad(t_back_data, pad_width, mode='constant', constant_values=0)
                    r_back_data = np.pad(r_back_data, pad_width, mode='constant', constant_values=0)

        elif self.wavelength is not None and n_wl == 1:
            wl_start = float(self.wavelength[0])

        # Incidence angle padding
        th_start = 0.0
        th_inv_step = 0.0
        if self.incidence_angle is not None and n_th > 1:
            step = float(self.incidence_angle[1] - self.incidence_angle[0])
            if step != 0:
                th_inv_step = 1.0 / step
                
                pad_top = 1 
                pad_bottom = 1 
                if float(self.incidence_angle[0]) - step < -1e-5: pad_top = 0
                if float(self.incidence_angle[-1]) + step > 90.0 + 1e-5: pad_bottom = 0

                if pad_top == 1:
                    th_start = float(self.incidence_angle[0]) - step
                else:
                    th_start = float(self.incidence_angle[0])
                
                if pad_top > 0 or pad_bottom > 0:
                    pad_width = ((pad_top, pad_bottom), (0, 0))
                    t_data = np.pad(t_data, pad_width, mode='constant', constant_values=0)
                    r_data = np.pad(r_data, pad_width, mode='constant', constant_values=0)
                    if back_is_set:
                        t_back_data = np.pad(t_back_data, pad_width, mode='constant', constant_values=0)
                        r_back_data = np.pad(r_back_data, pad_width, mode='constant', constant_values=0)
                    
        elif self.incidence_angle is not None and n_th == 1:
            th_start = float(self.incidence_angle[0])

        # Create front textures 
        tex_transmittance, cu_array_t = self._create_texture_2d(t_data)
        tex_reflectance, cu_array_r = self._create_texture_2d(r_data)

        # Create back textures
        if back_is_set:
            tex_transmittance_back, cu_array_t_back = self._create_texture_2d(t_back_data)
            tex_reflectance_back, cu_array_r_back = self._create_texture_2d(r_back_data)
        else:
            # Use front textures if back is undefined
            tex_transmittance_back = tex_transmittance
            tex_reflectance_back = tex_reflectance
            cu_array_t_back = None 
            cu_array_r_back = None

        texture = OpticalTextures(
            transmittance=tex_transmittance,
            reflectance=tex_reflectance,
            transmittance_back=tex_transmittance_back,
            reflectance_back=tex_reflectance_back,
            wavelength_start=wl_start,
            wavelength_inv_step=wl_inv_step,
            angle_start=th_start,
            angle_inv_step=th_inv_step,
            _t_array=cu_array_t,
            _r_array=cu_array_r,
            _t_back_array=cu_array_t_back,
            _r_back_array=cu_array_r_back
        )

        if get_data: # For debugging
            return texture, t_data, r_data
        else:
            return texture

    def _create_texture_2d(self, texture_data_np):
        """
        Internal helper to create a TextureObject from a numpy array.
        """
        texture_data = texture_data_np.astype(np.float32)
        height, width = texture_data.shape
        
        desc = cp.cuda.texture.ChannelFormatDescriptor(
            32, 0, 0, 0, cp.cuda.runtime.cudaChannelFormatKindFloat
        )
        
        cu_array = cp.cuda.texture.CUDAarray(desc, width, height)
        cu_array.copy_from(texture_data)
        
        res_desc = cp.cuda.texture.ResourceDescriptor(
            cp.cuda.runtime.cudaResourceTypeArray,
            cuArr=cu_array
        )
        
        tex_desc = cp.cuda.texture.TextureDescriptor(
            addressModes=(
                cp.cuda.runtime.cudaAddressModeClamp, 
                cp.cuda.runtime.cudaAddressModeClamp 
            ),
            filterMode=cp.cuda.runtime.cudaFilterModeLinear,
            readMode=cp.cuda.runtime.cudaReadModeElementType,
            normalizedCoords=False
        )
        
        tex_obj = cp.cuda.texture.TextureObject(res_desc, tex_desc)
        return tex_obj, cu_array
    
    def __repr__(self):
        fields = [
            'transmittance', 'reflectance', 'absorption',
            'transmittance_back', 'reflectance_back', 'absorption_back',
            'wavelength', 'incidence_angle'
        ]
        
        field_info = []
        for field_name in fields:
            val = getattr(self, field_name)
            state = "set" if val is not None else "not set"
            field_info.append(f"{field_name}: {state}")
            
        return f"SurfaceProperties({', '.join(field_info)})"

    @iactsim_style
    def plot(self,
        kind: str = 'transmittance',
        heatmap: bool | None = None,
        cmap: str = "Spectral"
    ):
        """Plot the efficiency curves for the specified quantity.
        
        Parameters
        ----------
        kind : str, optional
            The quantity to plot. Must start with 't' (transmittance), 
            'r' (reflectance), or 'a' (absorption). 
            To plot back-side properties, append '_back' (e.g., 't_back', 'reflectance_back').
            Default is 'transmittance'.
        heatmap : bool, optional
            Whether to plot a 2D heat map. If `None` (default), a heatmap
            will be used when the number of wavelengths and incidence angles
            is large (greater than 11 for the smaller of the two dimensions).
            Otherwise, individual curves will be plotted.

        Returns
        -------
        matplotlib.figure.Figure, matplotlib.axes.Axes
            The matplotlib figure and axes object containing the plot.
        """
        self._validate()

        import matplotlib.pyplot as plt

        kind_lower = kind.lower()
        is_back = 'back' in kind_lower

        if kind_lower.startswith('t'):
            base_attr = 'transmittance'
        elif kind_lower.startswith('r'):
            base_attr = 'reflectance'
        elif kind_lower.startswith('a'):
            base_attr = 'absorption'
        else:
            raise ValueError(f"Argument 'kind' must start with 't', 'r', or 'a'. Got '{kind}'")

        target_attr = f"{base_attr}_back" if is_back else base_attr
        data = getattr(self, target_attr)

        if (self.incidence_angle is None and self.wavelength is None) or data is None:
            side_str = "back-side" if is_back else "front-side"
            raise RuntimeError(f"The {side_str.lower()} surface efficiency ({target_attr}) has not been initialized properly.")
        
        fig, ax = plt.subplots()

        max_n_labels = 11
        plot_wavelength = self.wavelength is not None
        plot_incidence_angle = self.incidence_angle is not None
        n_wl = len(self.wavelength) if plot_wavelength else 1
        n_th = len(self.incidence_angle) if plot_incidence_angle else 1
        values = data.flatten()

        if heatmap is None:
            heatmap = False
            if n_th > 1 and n_wl > 1 and min(n_th, n_wl) > max_n_labels:
                heatmap = True

        if not plot_wavelength or not plot_incidence_angle:
            heatmap = False

        title_suffix = " (back)" if is_back else " (front)"

        if not heatmap:
            curves = values.reshape((n_th, n_wl))
            if n_th <= n_wl:
                x_axis = self.wavelength if self.wavelength is not None else np.arange(n_wl)
                for i in range(n_th):
                    label = f'{self.incidence_angle[i]:.1f} $\\degree$' if self.incidence_angle is not None else None
                    ax.plot(x_axis, curves[i], label=label)
                ax.set_xlabel('Wavelength (nm)')
            else:
                x_axis = self.incidence_angle if self.incidence_angle is not None else np.arange(n_th)
                for i in range(n_wl):
                    label = f'{self.wavelength[i]:.1f} nm' if self.wavelength is not None else None
                    ax.plot(x_axis, curves[:, i], label=label)
                ax.set_xlabel('Incidence angle ($\\degree$)')
            
            if min(n_th, n_wl) < max_n_labels and plot_wavelength and plot_incidence_angle:
                ax.legend()
            ax.set_ylabel(f'{base_attr.title()}{title_suffix}')
            ax.grid(which='both')
        else:
            contour = ax.contourf(
                self.wavelength,
                self.incidence_angle,
                data.reshape(n_th, n_wl),
                levels=np.linspace(0, 1, 100),
                cmap=cmap
            )
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Incidence angle ($\\degree$)")
            cbar = fig.colorbar(contour, ax=ax, boundaries=np.linspace(0, 1, 100))
            cbar.set_label(f'{base_attr.title()}{title_suffix}')
        
        return fig, ax

class FresnelSurfacePropertiesGenerator:
    """
    Handles the calculation and population of SurfaceProperties objects 
    based on Fresnel equations for a given Surface instance.
    """

    @staticmethod
    def _calculate_fresnel(n1, n2, theta_deg, polarization='unpolarized'):
        """
        Perform a vectorized Fresnel calculation for a specific polarization.

        Parameters
        ----------
        n1 : np.ndarray
            Refractive index of the incident medium. Shape must be broadcastable 
            to (N_angles, N_wl).
        n2 : np.ndarray
            Refractive index of the transmission medium. Shape must be broadcastable 
            to (N_angles, N_wl).
        theta_deg : np.ndarray
            Incident angles in degrees. Shape must be broadcastable 
            to (N_angles, N_wl).
        polarization : str, optional
            The polarization mode to compute. Options are:
            - 'unpolarized': Average of s- and p-polarization.
            - 's', 'rs': s-polarization only.
            - 'p', 'rp': p-polarization only.
            Default is 'unpolarized'.

        Returns
        -------
        np.ndarray
            Reflectance matrix R with shape (N_angles, N_wl).

        Raises
        ------
        ValueError
            If an invalid polarization string is provided.
        """
        theta_i = np.radians(theta_deg)
        
        # Snell's law
        sin_theta_t = (n1 / n2) * np.sin(theta_i)

        # Total internal reflection
        tir_mask = np.abs(sin_theta_t) > 1.0

        sin_theta_t_safe = np.where(tir_mask, 0.0, sin_theta_t)
        theta_t = np.arcsin(sin_theta_t_safe)

        # Amplitude coefficients
        cos_theta_i = np.cos(theta_i)
        cos_theta_t = np.cos(theta_t)

        # Initialize result
        R_out = None

        # Calculate S-pol if needed
        if polarization in ['s', 'rs', 'unpolarized']:
            rs_num = n1 * cos_theta_i - n2 * cos_theta_t
            rs_den = n1 * cos_theta_i + n2 * cos_theta_t
            rs = np.divide(rs_num, rs_den, out=np.zeros_like(rs_num), where=rs_den!=0)
            Rs = np.abs(rs)**2
            Rs = np.where(tir_mask, 1.0, Rs)
            
            if polarization in ['s', 'rs']:
                R_out = Rs

        # Calculate P-pol if needed
        if polarization in ['p', 'rp', 'unpolarized']:
            rp_num = n2 * cos_theta_i - n1 * cos_theta_t
            rp_den = n2 * cos_theta_i + n1 * cos_theta_t
            rp = np.divide(rp_num, rp_den, out=np.zeros_like(rp_num), where=rp_den!=0)
            Rp = np.abs(rp)**2
            Rp = np.where(tir_mask, 1.0, Rp)

            if polarization in ['p', 'rp']:
                R_out = Rp

        # Unpolarized
        if polarization == 'unpolarized':
            R_out = 0.5 * (Rs + Rp)

        if R_out is None:
            raise ValueError(f"Invalid polarization mode: '{polarization}'. "
                             "Use 's', 'p', or 'unpolarized'.")

        return R_out

    def generate(self, surface, wavelengths=None, angles=None, polarization='unpolarized', inplace=False):
        """
        Generate a populated SurfaceProperties object.

        Parameters
        ----------
        surface : iactsim.optics.Surface
            The surface object containing `material_in` and `material_out` attributes,
            which must have `get_refractive_index(wavelengths)` methods.
        wavelengths : np.ndarray, optional
            1D array of wavelengths in nm. If None, defaults to `np.arange(200, 901, 1)`.
        angles : np.ndarray, optional
            1D array of incidence angles in degrees. If None, defaults to `np.arange(0, 91, 1)`.
        polarization : {'unpolarized', 's', 'p', 'rs', 'rp'}, optional
            The specific polarization to compute for reflectance and transmittance.
            Default is 'unpolarized'.
        inplace : bool, optional
            If True, modifies the provided surface's properties in place.
            Default is False.

        Returns
        -------
        iactsim.optics.SurfaceProperties
            If `inplace` is False, a populated properties object containing the calculated matrices:
            - `reflectance`, `transmittance` (Front interface)
            - `reflectance_back`, `transmittance_back` (Back interface)
            - `wavelength`, `incidence_angle` vectors.
        """
        pol_clean = polarization.lower().strip()

        # Apply defaults
        if wavelengths is None:
            wavelengths = np.arange(200, 901, 1)
        
        if angles is None:
            angles = np.arange(0, 91, 1)

        # Ensure inputs are numpy arrays
        wl = np.asarray(wavelengths)
        ang = np.asarray(angles)

        # Retrieve materials and reshape for broadcasting
        # n: (1, N_wl) | ang: (N_ang, 1)
        n_in = surface.material_in.get_refractive_index(wl).reshape(1, -1)
        n_out = surface.material_out.get_refractive_index(wl).reshape(1, -1)
        ang_reshaped = ang.reshape(-1, 1)

        # Front interface (n_in -> n_out)
        R_front = self._calculate_fresnel(n_in, n_out, ang_reshaped, pol_clean)
        
        # Cleanup
        nan_mask_f = np.isnan(R_front)
        T_front = 1.0 - R_front

        # NaNs will be treated as absorption
        R_front[nan_mask_f] = 0.0
        T_front[nan_mask_f] = 0.0

        # Back interface (n_out -> n_in)
        R_back = self._calculate_fresnel(n_out, n_in, ang_reshaped, pol_clean)
        
        # Cleanup
        nan_mask_b = np.isnan(R_back)
        T_back = 1.0 - R_back

        # NaNs will be treated as absorption
        R_back[nan_mask_b] = 0.0
        T_back[nan_mask_b] = 0.0

        # Populate Object
        surface_prop = SurfaceProperties()
        surface_prop.wavelength = wl
        surface_prop.incidence_angle = ang
        
        surface_prop.reflectance = R_front
        surface_prop.transmittance = T_front
        surface_prop.reflectance_back = R_back
        surface_prop.transmittance_back = T_back

        if inplace:
            surface.properties = surface_prop
        else:
            return surface_prop