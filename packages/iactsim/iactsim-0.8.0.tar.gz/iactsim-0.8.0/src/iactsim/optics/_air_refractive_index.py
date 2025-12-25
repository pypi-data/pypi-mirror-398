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

import math
from typing import Optional

constants = {
    # Saturation Vapor Pressure constants
    "K1": 1.16705214528E+03, "K2": -7.24213167032E+05, "K3": -1.70738469401E+01,
    "K4": 1.20208247025E+04, "K5": -3.23255503223E+06, "K6": 1.49151086135E+01,
    "K7": -4.82326573616E+03, "K8": 4.05113405421E+05, "K9": -2.38555575678E-01,
    "K10": 6.50175348448E+02,

    # Saturation Vapor Pressure constants for t <= 0
    "A1": -13.928169, "A2": 34.7078238,

    # Enhancement Factor constants
    "alpha": 1.00062, "beta": 3.14E-8, "gamma": 5.6E-7,

    # Ciddor calculation: dispersion constants
    "k0": 238.0185, "k1": 5792105.0, "k2": 57.362,    "k3": 167917.0,
    "w0": 295.235,  "w1": 2.6422,    "w2": -0.032380, "w3": 0.004028,

    # Ciddor calculation: compressibility constants
    "a0": 1.58123E-6, "a1": -2.9331E-8, "a2": 1.1043E-10,
    "b0": 5.707E-6,   "b1": -2.051E-8,
    "c0": 1.9898E-4,  "c1": -2.376E-6,
     "d": 1.83E-11,    "e": -0.765E-8,
     "R": 8.314462618,

    # Reference conditions and constants for Ciddor calculation
    "p_r1":   101325,       # Reference pressure (Pa)
    "T_r1":   288.15,       # Reference temperature (K)
    "Za":     0.9995922115, # Compressibility factor of reference air
    "rho_vs": 0.00985938,   # Reference density for water vapor term (kg/m^3, derived constant)
    "Mv":     18.015E-3,    # Molar mass of water vapor (kg/mol)
}

def calculate_psv(t: float) -> float:
    """Calculate the saturation vapor pressure of water.

    Uses different formulas based on whether the temperature is above
    or at/below 0 degrees Celsius.

    Parameters
    ----------
    t : float
        Temperature in degrees Celsius.

    Returns
    -------
    float
        Saturation vapor pressure in Pascals (Pa).

    """
    T_kelvin = t + 273.15
    if t > 0:
        omega = T_kelvin + constants["K9"] / (T_kelvin - constants["K10"])
        A = omega**2 + constants["K1"]*omega + constants["K2"]
        B = constants["K3"]*omega**2 + constants["K4"]*omega + constants["K5"]
        C = constants["K6"]*omega**2 + constants["K7"] * omega + constants["K8"]
        X = -B + math.sqrt(B**2 - 4*A*C)
        psv_pascal = 1e6*(2*C/X)**4
    else:
        psi = T_kelvin / 273.16 # Temperature ratio relative to triple point
        Y = constants["A1"]*(1-psi**(-1.5))+constants["A2"]*(1-psi**(-1.25))
        psv_pascal = 611.657*math.exp(Y)
    return psv_pascal

def calculate_enhancement_factor(p: float, t: float) -> float:
    """Calculate the enhancement factor for water vapor in air.

    This factor accounts for the non-ideal behavior of moist air compared
    to an ideal gas mixture.

    Parameters
    ----------
    p : float
        Pressure in Pascals (Pa).
    t : float
        Temperature in degrees Celsius.

    Returns
    -------
    float
        Enhancement factor (dimensionless).

    """
    return constants["alpha"] + constants["beta"] * p + constants["gamma"] * t**2

def calculate_xv_from_rh(rh: float, p: float, t: float) -> float:
    """Calculate the mole fraction of water vapor from relative humidity.

    Uses the saturation vapor pressure and enhancement factor.

    Parameters
    ----------
    rh : float
        Relative humidity in percent (%). Must be between 0 and 100.
    p : float
        Total air pressure in Pascals (Pa).
    t : float
        Air temperature in degrees Celsius.

    Returns
    -------
    float
        Mole fraction of water vapor (dimensionless).

    Raises
    ------
    ValueError
        If RH is outside the valid range [0, 100].

    """
    if not (0 <= rh <= 100):
        raise ValueError("RH must be between 0 and 100 percent.")
    # Calculate saturation vapor pressure at temperature t
    psv_t = calculate_psv(t)
    # Calculate enhancement factor at pressure p and temperature t
    f_pt = calculate_enhancement_factor(p, t)
    # Calculate partial pressure of water vapor
    pv = f_pt * (rh / 100.0) * psv_t
    # Calculate mole fraction
    xv = pv / p
    return xv

def calculate_ciddor_rindex(
    lambda_vac: float,
    p: float,
    t: float,
    xCO2: float,
    rh: Optional[float],
) -> float:
    """Calculate the refractive index of moist air using the Ciddor equation.

    Follows the NIST implementation described by `Jack A. Stone and
    Jay H. Zimmerman <https://emtoolbox.nist.gov/Wavelength/Documentation.asp>`_.

    Parameters
    ----------
    lambda_vac : float
        Vacuum wavelength of light in nanometers (nm).
    p : float
        Air pressure in Pascals (Pa).
    t : float
        Air temperature in degrees Celsius.
    xCO2 : float
        CO2 concentration in micromoles per mole (µmol/mol), equivalent to ppm.
    rh : Optional[float]
        Relative humidity in percent (%). If None, assumes dry air (xv = 0).

    Returns
    -------
    float
        Refractive index of air (n), dimensionless.

    """
    # Convert wavelength from nm to µm for Ciddor formula
    lambda_um = lambda_vac / 1e3
    # Wavenumber squared in um^-2
    S = 1.0 / lambda_um**2

    # Calculate refractivity of standard dry air using dispersion formula
    r_as = 1e-8*(constants['k1'] / (constants['k0'] - S) + constants['k3'] / (constants['k2'] - S))
    
    # Calculate refractivity term related to water vapor
    r_vs = 1.022e-8 * (constants['w0'] + constants['w1']*S + constants['w2']*S**2 + constants['w3']*S**3)

    # Calculate molar mass of air adjusted for CO2 concentration deviation from 400 ppm
    M_a = 0.0289635 + 1.2011e-8*(xCO2-400.)

    # Adjust standard air refractivity for CO2 concentration deviation from 450 ppm
    r_axs = r_as*(1+5.34e-7*(xCO2-450.))

    # Calculate mole fraction of water vapor (xv)
    if rh is None:
        xv = 0.0 # Assume dry air if rh is not provided
    else:
        xv = calculate_xv_from_rh(rh, p, t)

    T_kelvin = t + 273.15
    
    # Calculate compressibility factor (Z_m) for moist air
    term1_z = constants['a0'] + constants['a1'] * t + constants['a2'] * t**2
    term2_z = (constants['b0'] + constants['b1'] * t) * xv
    term3_z = (constants['c0'] + constants['c1'] * t) * xv**2
    term4_z = constants['d'] + constants['e'] * xv**2
    Z_m = 1. - (p / T_kelvin) * (term1_z + term2_z + term3_z) + term4_z*(p/T_kelvin)**2

    # Calculate reference density of standard air
    rho_axs = constants['p_r1'] * M_a / constants['Za'] / constants['R'] / constants['T_r1']

    # Calculate density of water vapor component
    rho_v = xv * p * constants['Mv'] / (Z_m * constants['R'] * T_kelvin)
    
    # Calculate density of dry air component
    rho_a = (1.-xv) * p * M_a / (Z_m * constants['R'] * T_kelvin)

    # Calculate refractive index
    n = 1. + rho_a/rho_axs*r_axs + rho_v/constants['rho_vs']*r_vs

    return n
