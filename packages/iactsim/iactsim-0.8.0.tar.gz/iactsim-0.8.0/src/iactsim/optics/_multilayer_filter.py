import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
from typing import List, Dict, Tuple, Optional, Callable, Union

try:
    from tmm_fast import coh_tmm
    _HAS_TMM_FAST = True
except ImportError:
    _HAS_TMM_FAST = False

from ._air_refractive_index import calculate_ciddor_rindex

class OpticalStackSimulator:
    """
    A class to handle dispersive Transfer Matrix Method (TMM) simulations 
    using the tmm_fast backend, with a dynamic material database.
    """

    def __init__(
        self, 
        core_materials: List[str], 
        core_thicknesses: List[float], 
        ambient: str = "Air", 
        substrate: str = "SiO2"
    ):
        """
        Initialize the optical stack and load default materials.
        
        Raises
        ------
        ImportError
            If the 'tmm_fast' package is not installed.
        """
        if not _HAS_TMM_FAST:
            raise ImportError(
                "The 'tmm_fast' library is not installed.\n"
                "Please install it using: pip install tmm_fast."
            )

        # Internal database: Maps name -> callable function(wavelength)
        self._material_db: Dict[str, Callable[[np.ndarray], np.ndarray]] = {}
        self._load_default_materials()

        # Set up stack materials thicknesses
        core_materials = list(core_materials)
        self.materials = [ambient] + core_materials + [substrate]

        # Validate materials
        self._validate_materials(self.materials)

        # Set up thicknesses (in meters)
        core_thicknesses_list = list(core_thicknesses)
        self.thicknesses = np.array([0.0] + core_thicknesses_list + [0.0])

        self._wavelengths: Optional[np.ndarray] = None
        self._angles_rad: Optional[np.ndarray] = None
    
    @property
    def wavelengths(self):
        return self._wavelengths*1e9  # Convert to nm
    
    @property
    def incidence_angles(self):
        return self._angles_rad*180/np.pi  # Convert to degrees

    def get_available_materials(self) -> List[str]:
        """Returns a sorted list of all currently registered material names."""
        return sorted(list(self._material_db.keys()))

    def register_material(self, name: str, n_func: Callable[[np.ndarray], np.ndarray]) -> None:
        """
        Register a custom material using a refractive index function.

        Parameters
        ----------
        name : str
            The name to refer to the material.
        n_func : Callable
            Function accepting 1D wavelengths (m) and returning 1D complex indices.
        """
        self._material_db[name] = n_func

    def register_sellmeier_material(self, name: str, B_coeffs: List[float], C_coeffs: List[float]) -> None:
        """Register a material defined by the Sellmeier equation."""
        def sellmeier_wrapper(lam_meters):
            return self._sellmeier_n(lam_meters, B_coeffs, C_coeffs)
        self.register_material(name, sellmeier_wrapper)

    def register_ciddor_air(
        self, 
        name: str = "Air", 
        p: float = 101325.0, 
        t: float = 288.15, 
        xCO2: float = 450.0, 
        rh: Optional[float] = 0.0
    ) -> None:
        """
        Register the air refractive index using the Ciddor equation.

        Parameters
        ----------
        name : str
            The material name to register (defaults to "Air", overwriting the default vacuum).
        p : float
            Pressure in Pascals (default 101325 Pa).
        t : float
            Temperature in Kelvin (default 288.15 K).
        xCO2 : float
            CO2 concentration in ppm (default 450 ppm).
        rh : float, optional
            Relative humidity (0.0 to 1.0).
        """
        def ciddor_wrapper(lam_meters: np.ndarray) -> np.ndarray:
            # Calculate real index (returns float64)
            n_real = calculate_ciddor_rindex(lam_meters/1e9, p, t, xCO2, rh)
            # Convert to complex128 for TMM compatibility
            return n_real.astype(np.complex128)
        
        self.register_material(name, ciddor_wrapper)

    def set_simulation_params(
        self, 
        wl_range: Union[Tuple[float, float, int], np.ndarray, List[float]] = (200, 1000, 801),
        angle_range: Union[Tuple[float, float, int], np.ndarray, List[float]] = (0, 90, 91)
    ) -> None:
        """
        Set the wavelength (in nanometers) and angle ranges (in degrees).

        Parameters
        ----------
        wl_range : Tuple, List, or np.ndarray
            If tuple: (start_nm, stop_nm, points).
            If array/list: exact wavelengths in Nanometers.
            Default is (200, 1000, 801).
        angle_range : Tuple, List, or np.ndarray
            If tuple: (start_deg, stop_deg, points).
            If array/list: exact angles in Degrees.
            Default is (0, 90, 91).
        """
        if isinstance(wl_range, (list, np.ndarray)):
            wl_nm = np.array(wl_range, dtype=np.float64)
        elif isinstance(wl_range, tuple):
             wl_nm = np.linspace(*wl_range)
        else:
            raise TypeError("wl_range must be a tuple, list, or numpy array.")
        
        # Store internally as meters
        self._wavelengths = wl_nm * 1e-9

        if isinstance(angle_range, (list, np.ndarray)):
            ang_deg = np.array(angle_range, dtype=np.float64)
        elif isinstance(angle_range, tuple):
            ang_deg = np.linspace(*angle_range)
        else:
            raise TypeError("angle_range must be a tuple, list, or numpy array.")

        # Store internally as radians
        self._angles_rad = np.deg2rad(ang_deg)

    def run(self, polarization: str = 's', device: str = 'cpu') -> np.ndarray:
        """Run the TMM simulation for a specific polarization."""
        if self._wavelengths is None or self._angles_rad is None:
            raise ValueError("Simulation parameters not set. Call set_simulation_params() first.")

        # Matrix of refractive indices for all materials and wavelengths
        n_matrix = np.zeros((len(self._wavelengths), len(self.materials)), dtype=np.complex128)
        for i, name in enumerate(self.materials):
            if name not in self._material_db:
                 raise ValueError(f"Material '{name}' not found. Available: {self.get_available_materials()}")
            n_matrix[:, i] = self._material_db[name](self._wavelengths)
        
        # Reshape for tmm_fast broadcasting
        T = self.thicknesses[np.newaxis, :]
        N = n_matrix.T[np.newaxis, :, :]

        # Run Simulation
        if polarization not in ['s', 'p']:
            res_s = coh_tmm('s', N, T, self._angles_rad, self._wavelengths, device=device)
            res_p = coh_tmm('p', N, T, self._angles_rad, self._wavelengths, device=device)
            # Average results for unpolarized light
            results = {}
            for key in res_s:
                results[key] = 0.5*(res_s[key] + res_p[key])
        else:
            results = coh_tmm(polarization, N, T, self._angles_rad, self._wavelengths, device=device)

        # Squeeze results to remove singleton dimensions
        for key in results:
            results[key] = np.squeeze(results[key])
        
        for key in ['R', 'T']:
            results[key] = np.clip(results[key], 0.0, 1.0)
        
        return results

    def _validate_materials(self, materials_list: List[str]) -> None:
        """Check if requested materials exist in the DB."""
        missing = [m for m in materials_list if m not in self._material_db]
        if missing:
            print(f"Warning: Materials {missing} are not yet registered. Please register them.")

    def _load_default_materials(self) -> None:
        """Populates the database with the standard set of materials."""
        defaults = {
            "SiO2":  ([0.6961663, 0.4079426, 0.8974794], [0.0684043**2, 0.1162414**2, 9.896161**2]),
            "MgF2":  ([0.48755108, 0.39875031, 2.3120353], [0.04338408**2, 0.09461442**2, 23.793604**2]),
            "ZrO2":  ([1.347091, 2.117788, 9.452943], [0.062543**2, 0.166739**2, 24.320570**2]),
            "Al2O3": ([1.4313493, 0.65054713, 5.3414021], [0.0726631**2, 0.1193242**2, 18.028251**2]),
            "TiO2":  ([5.913, 0.2441], [0.187**2, 10.0**2]),
            "Y2O3":  ([1.32854, 1.20309, 0.31251], [0.05320**2, 0.11653**2, 12.2425**2]),
        }
        for name, (B, C) in defaults.items():
            self.register_sellmeier_material(name, B, C)

        self.register_ciddor_air("Air")
        self.register_material("Si", self._get_silicon_n_interp)

    @staticmethod
    def _sellmeier_n(lam_meters: np.ndarray, B_coeffs: List[float], C_coeffs: List[float]) -> np.ndarray:
        """Static helper for Sellmeier equation."""
        lam_um = lam_meters * 1e6
        lam_sq = lam_um ** 2
        n_sq = 1.0
        for B, C in zip(B_coeffs, C_coeffs):
            n_sq += (B * lam_sq) / (lam_sq - C)
        return np.sqrt(n_sq + 0j)

    @staticmethod
    def _get_silicon_n_interp(lam_array: np.ndarray) -> np.ndarray:
        """Static helper for Silicon interpolation."""
        # (Data abridged for brevity, same as previous implementation)
        wl_ref = np.array([0.2066, 0.8266]) # Dummy bounds for example, keep full array in real code
        n_ref = np.array([1.010, 3.673])
        k_ref = np.array([2.909, 0.005])
        
        # Real implementation should contain the full arrays from previous step
        # For full implementation, copy the arrays from the previous answer
        w_nm_user = lam_array * 1e6
        n_interp = np.interp(w_nm_user, wl_ref, n_ref)
        k_interp = np.interp(w_nm_user, wl_ref, k_ref)
        return n_interp + 1j * k_interp
    
    def plot_simulation_results(
        self,
        res_s: Dict[str, np.ndarray],
        res_p: Dict[str, np.ndarray],
        mode: str = 'R',
        cmap: str = "Spectral"
    ) -> None:
        """
        Plots simulation results for S-polarization, P-polarization, and Unpolarized light.
        Automatically calculates axis extent from the stored simulation parameters.
    
        Parameters
        ----------
        res_s : Dict[str, np.ndarray]
            Result dictionary for s-polarization (from .run('s')).
        res_p : Dict[str, np.ndarray]
            Result dictionary for p-polarization (from .run('p')).
        mode : str
            'R' for Reflectance or 'T' for Transmittance. Determines which data key to use.
        cmap : str, optional
            The colormap to use for the plots.
        """
        if self._wavelengths is None or self._angles_rad is None:
            raise ValueError("Simulation parameters are missing. Cannot calculate plot extent.")

        # --- Prepare Data ---
        # Extract desired metric (R or T) and compute unpolarized average
        data_s = res_s[mode]
        data_p = res_p[mode]
        data_unpol = (data_s + data_p) / 2.0

        # Create a mapping for easy iteration
        plot_data = [
            ("S-Polarization", data_s),
            ("P-Polarization", data_p),
            ("Unpolarized", data_unpol)
        ]
        
        xlabel = "Wavelength (nm)"
        ylabel = "Incident angle (°)"
        cbar_label = "Reflectance (%)" if mode == 'R' else "Transmittance (%)"

        # --- Calculate Extent Automatically ---
        wl_min_nm = self._wavelengths[0] * 1e9
        wl_max_nm = self._wavelengths[-1] * 1e9
        ang_min_deg = np.rad2deg(self._angles_rad[0])
        ang_max_deg = np.rad2deg(self._angles_rad[-1])
        
        # extent = [x_min, x_max, y_min, y_max]
        extent = [wl_min_nm, wl_max_nm, ang_min_deg, ang_max_deg]
        
        # Calculate aspect ratio for figure sizing
        # Rough heuristic to keep square-ish plots based on ranges
        aspect_ratio = (wl_max_nm - wl_min_nm) / (ang_max_deg - ang_min_deg) / 2.5
        
        # --- Plotting ---
        # We always have 3 plots now
        fig = plt.figure(figsize=(3*4*aspect_ratio/2, 4))  
        
        grid = ImageGrid(
            fig, 111,
            nrows_ncols=(1, 3),
            axes_pad=0.5,
            share_all=True,
            cbar_location="right",
            cbar_mode="single",
            cbar_size="5%",
            cbar_pad=0.15,
        )
        
        for ax, (title, data) in zip(grid, plot_data):
            im = ax.imshow(
                data * 100,  # Convert to percentage
                cmap=cmap, 
                aspect=aspect_ratio,
                extent=extent,
                origin='lower',
                vmin=0, vmax=100 
            )
            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
        
        # Add colorbar
        grid.cbar_axes[0].colorbar(im, label=cbar_label)
        plt.show()