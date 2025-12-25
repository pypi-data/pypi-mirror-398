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

import warnings

import re
from typing import Dict

import cupy as cp
import numpy as np
from tqdm.auto import tqdm

from ..optics.ray_tracing._cuda_kernels import local_to_telescope_transform
from ..optics._cpu_transforms import local_to_telescope_rotation

class CorsikaInputCard():
    """Parse the input card of a CORSIKA file.


    Parameters
    ----------
    file : str or path-like object.
        CORSIKA file path.
    
    """
    def __init__(self, file):
        self.card = self._get_input_card(file)
    
    def _from_input_card(self, param_name):
        founds = []
        found = []
        for m in re.finditer(param_name, self.card):
            start = m.start()
            end = self.card.find("\n",start)
            found = re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", self.card[start:end])
            if len(found) == 1:
                found = found[0]
            founds.append(found)
        
        if len(founds) == 0:
            raise(RuntimeError(f"No entry '{param_name}' found in the input card."))
        
        return founds if len(founds)>1 else founds[0]

    def __getitem__(self, key: str):
        """Search the input card for a specific parameter name.

        Parameters
        ----------
        param : str
            Parameter name.

        Returns
        -------
        str
            Values found on the input card line corresponding to the parameter name.
        
        Warning
        -------
            Values are returned as strings as they are in the input card.

        """
        return self._from_input_card(key)

    def _get_input_card(self, file):
        try:
            import eventio
        except(ImportError):
            raise(RuntimeError("Package 'eventio' is not installed."))

        with eventio.IACTFile(file) as cfile:
            self._raw_input_card = cfile.input_card.decode("utf-8")
            # Remove lines staring with "*"
            input_card = re.sub(r'^\*.*\n?', '', self._raw_input_card, flags=re.MULTILINE)
            # Remove inline comments starting with "//"
            input_card = re.sub(r"//(.*?)\n", '\n', input_card, flags=re.MULTILINE)
            # Remove inline comments starting with "#" 
            input_card = re.sub(r"#(.*?)\n", '\n', input_card, flags=re.MULTILINE)
        return input_card

    def get_telescopes_position(self):
        telescopes = self['TELESCOPE']
        if isinstance(telescopes[0], str):
            telescopes = [telescopes]
        return {k: np.asarray([float(pos) for pos in tel_pos[:-1]]) for k,tel_pos in enumerate(telescopes)}

    def get_telescopes_ref_sphere_radius(self):
        telescopes = self['TELESCOPE']
        if isinstance(telescopes[0], str):
            telescopes = [telescopes]
        return {k: float(tel_pos[-1]) for k,tel_pos in enumerate(telescopes)}

# Approximation used for consistency with CORSIKA IACT extension
# maybe it would be better to access the CORSIKA atmospheric model somehow
def light_speed(h_km):
    c = 299.792458 # mm/ns
    n = 1.+0.0002814*np.exp(-0.0947982*(h_km)-0.00134614*(h_km)*(h_km))
    return c/n

def corsika_bunches_to_iactsim_input(bunches, n_bunches, obs_level, z0, lmin, lmax):
    """Convert CORSIKA IACT extension bunches into iactsim input.

    Parameters
    ----------
    bunches : numpy.ndarray
        CORSIKA bunches.
    n_bunches : int
        Number of bunches.
    obs_level : float
        Observation level in m.
    z0 : float
        Telescope observation level relative to CORSIKA observation level.
    lmin : float
        Minimum wavelength, used to generate wavelengths if not available.
    lmax : float
        Maximum wavelength, used to generate wavelengths if not available.

    Returns
    -------
    list[numpy.ndarray]
        Input for :py:class:`IACT` ray-tracing.
    
    """
    vs = np.empty((n_bunches, 3), dtype=np.float32)
    ps = np.empty((n_bunches, 3), dtype=np.float32)
    wls = np.empty((n_bunches,), dtype=np.float32)
    ts = np.empty((n_bunches,), dtype=np.float32)
    zems = np.empty((n_bunches,), dtype=np.float32)

    zems[:] = bunches['zem']*10. # to mm

    ps[:,0] = bunches['x']*10. # to mm
    ps[:,1] = bunches['y']*10. # to mm

    vs[:,0] = bunches['cx']
    vs[:,1] = bunches['cy']
    vs[:,2] = -np.sqrt(1.-bunches['cx']**2-bunches['cy']**2)

    # Not clear from IACT extension manual
    # if this is the right way to get the
    # photon arrival position on the telescope 
    dist = z0 / vs[:,2] # negative distace
    ps[:,2] = z0
    ps[:,0] += dist*vs[:,0]
    ps[:,1] += dist*vs[:,1]

    ts[:] = bunches['time'] + dist/light_speed(obs_level*1e-3)

    inv_lmin = 1./lmin
    inv_lmax = 1./lmax
    if np.any(bunches['wavelength']):
        wls[:] = bunches['wavelength']
    else:
        wls[:] = 1./(np.random.random(size=wls.shape[0])*(inv_lmin-inv_lmax) + inv_lmax)

    return [ps, vs, wls, ts, zems]

class CorsikaFile():
    """Class that represents a file produced by CORSIKA IACT extension.

        Parameters
        ----------
        file : str or path-like
            CORSIKA file path.
        
    """
    def __init__(self, file):
        warnings.warn(
            "The class 'CorsikaFile' is deprecated and no longer supported. "
            "It is kept for testing purposes only and will be removed in the future.",
            DeprecationWarning,
            stacklevel=2
        )
        self._file = file

        self.n_telescopes: int = 0 #: Number of telescopes

        self.photons_position: Dict[int, cp.ndarray] = {}
        """Photon positions for each telescope."""

        self.photons_direction: Dict[int, cp.ndarray] = {}
        """Photon directions for each telescope."""

        self.photons_wavelength: Dict[int, cp.ndarray] = {}
        """Photon wavelengths for each telescope."""

        self.photons_arrival_time: Dict[int, cp.ndarray] = {}
        """Photon arrival times for each telescope."""

        self.photons_zems: Dict[int, cp.ndarray] = {}
        """Photon emission altitudes for each telescope."""

        self.mappings: Dict[int, cp.ndarray] = {}
        """Photon events mapping for each telescope."""

        self.events_id: Dict[int, np.ndarray] = {}
        """Event identifiers for each telescope."""

        self.n_events: Dict[int, int] = {}
        """Number of read events for each telescope."""
        
        self.input_card = CorsikaInputCard(file)
        """CORSIKA input card."""

        n_showers = int(self.input_card["NSHOW"])
        reuse = self.input_card["CSCAT"]
        self.total_n_showers: int = int(reuse[0]) * n_showers
        """Total number of simulated showers (including reused)."""
        
        self.telescopes_position = self.input_card.get_telescopes_position()
        """Position of each telescope."""
        
        self.n_telescopes = len(self.telescopes_position)
        """Number of telescopes."""
        
        wavelength_range = self.input_card['CWAVLG']

        self.lmin = float(wavelength_range[0])
        """Minimum simulated photon wavelength."""

        self.lmax = float(wavelength_range[1])
        """Maximum simulated photon wavelength."""

        self.observation_level = float(self.input_card['OBSLEV'])*1e-2
        """CORSIKA observation level (m)."""
        
        self.bunch_size = float(self.input_card['CERSIZ'])
        """Simulated bunch-size."""
        
        self.show_progress = False
        """Whether to show a progress bar while reading the file."""

        self.zenith_range = [float(x) for x in self.input_card['THETAP']]
        """Simulated zenith range."""

        self.azimuth_range = [float(x) for x in self.input_card['PHIP']]
        """Simulated azimuth range."""
    
    def get_pointing(self):
        return 90-np.mean(self.zenith_range),  (np.mean(self.azimuth_range) - float(self.input_card['ARRANG'])) - 180

    def get_all_events(self, min_bunches=1, ignore_telescopes=[], copy_to_device=True):
        """Read all photon bunches of all telescopes.
        The bunches are rearranged as a :py:class:`IACT` input for each telescope.
        All events are mapped, for instance:

          - photon directions for the n-th event of the k-th telescope are: 
          
          .. code-block: python

                cfile = CorsikaFile(file)
                cfile.get_all_events()
                first = cfile.mappings[k][n]
                last = cfile.mappings[k][n+1]
                vs = cfile.photons_direction[first:last,:]

        Parameters
        ----------
        min_bunches : int, optional
            Minimum number of bunches under which the event is ignored, by default 1.
        ignore_telescopes : List[int]
            List of telescopes to be ignored.
        copy_to_device : bool
            Whether to copy data to the device. 
        """
        try:
            import eventio
        except(ImportError):
            raise(RuntimeError("Package 'eventio' is not installed."))
        
        if min_bunches < 1:
            raise(ValueError("The minimum number of bunches must be greater than 0."))

        telescopes = [tel_id for tel_id in range(self.n_telescopes) if tel_id not in ignore_telescopes]

        self._bunches = {tel_id: [] for tel_id in telescopes}
        self.events_id = {tel_id: [] for tel_id in telescopes}
        self.mappings = {tel_id: [0] for tel_id in telescopes}
        self.n_events = {tel_id: 0 for tel_id in telescopes}

        with eventio.EventIOFile(self._file) as f:
            pbar = tqdm(total=self.total_n_showers, unit=' events', disable=not self.show_progress)
            for obj in f:
                if isinstance(obj, (eventio.iact.EventHeader)):
                    sub_event_id = 0
                    event_number = obj.header.id
                    # obj.parse()
                    # 'particle_id', 'total_energy', 'starting_altitude', 'first_target_id', 'first_interaction_height', 'momentum_x', 'momentum_y', 'momentum_minus_z', 'zenith', 'azimuth'

                if obj.header.only_subobjects:
                    # Unique sub-event ID
                    event_id = 100*event_number
                    for subobj in obj:
                        if isinstance(subobj, eventio.iact.Photons):
                            tel_id = subobj.telescope_id

                            if tel_id in ignore_telescopes:
                                continue

                            n_bunches = subobj.n_bunches
                            
                            # Cut on incoming photon bunches
                            if n_bunches < min_bunches:
                                continue
                        
                            data = subobj.parse_data()
                            args = corsika_bunches_to_iactsim_input(data, n_bunches, self.observation_level, self.telescopes_position[tel_id][2]*10., self.lmin, self.lmax)

                            self._bunches[tel_id].append(args)
                            self.events_id[tel_id].append(event_id + subobj.array_id)
                            self.mappings[tel_id].append(n_bunches+self.mappings[tel_id][-1])
                            self.n_events[tel_id] += 1

                        sub_event_id += 1
                    pbar.update(1)
            pbar.close()
        
        # Remove telescopes with no events
        telescopes = [tel_id for tel_id in telescopes if self.n_events[tel_id]>0]

        # Concatenate all events in a single CuPy ndarray
        self.mappings = {tel_id: np.asarray(self.mappings[tel_id], dtype=np.int32) for tel_id in telescopes}
        self.photons_zems = {tel_id: np.concatenate([arg[4] for arg in self._bunches[tel_id]]) for tel_id in telescopes}
        self.photons_position = {tel_id: np.concatenate([arg[0] for arg in self._bunches[tel_id]]) for tel_id in telescopes}
        self.photons_direction = {tel_id: np.concatenate([arg[1] for arg in self._bunches[tel_id]]) for tel_id in telescopes}
        self.photons_wavelength = {tel_id: np.concatenate([arg[2] for arg in self._bunches[tel_id]]) for tel_id in telescopes}
        self.photons_arrival_time = {tel_id: np.concatenate([arg[3] for arg in self._bunches[tel_id]]) for tel_id in telescopes}

        if copy_to_device:
            for tel_id in telescopes:
                self.mappings[tel_id] = cp.asarray(self.mappings[tel_id], dtype=cp.int32)
                self.photons_zems[tel_id] = cp.asarray(self.photons_zems[tel_id], dtype=cp.float32)
                self.photons_position[tel_id] = cp.asarray(self.photons_position[tel_id], dtype=cp.float32)
                self.photons_direction[tel_id] = cp.asarray(self.photons_direction[tel_id], dtype=cp.float32)
                self.photons_wavelength[tel_id] = cp.asarray(self.photons_wavelength[tel_id], dtype=cp.float32)
                self.photons_arrival_time[tel_id] = cp.asarray(self.photons_arrival_time[tel_id], dtype=cp.float32)
    
    def get_event(self, event, tel_id, seen_by=None):
        if len(self.events_id) == 0:
            raise(RuntimeError("No events. Did you call `get_all_events`?"))
        index = self.events_id[tel_id].index(event)
        ps, vs, wls, ts, zems = self._bunches[tel_id][index]
        ps = cp.asarray(ps, dtype=cp.float32)
        vs = cp.asarray(vs, dtype=cp.float32)
        wls = cp.asarray(wls, dtype=cp.float32)
        ts = cp.asarray(ts, dtype=cp.float32)
        zems = cp.asarray(zems, dtype=cp.float32)
        p0 = cp.full((3,), 0, dtype=cp.float32)
        if seen_by is not None:
            rot = cp.asarray(local_to_telescope_rotation(*seen_by.pointing), dtype=cp.float32)
            blocksize = 256
            n_photons = ps.shape[0]
            num_blocks = int(np.ceil(n_photons / blocksize))
            local_to_telescope_transform((num_blocks,), (blocksize,), (ps, vs, p0, rot, cp.int32(n_photons)))
        
        return ps, vs, wls, ts, zems