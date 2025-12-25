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

from pathlib import Path as _Path
from typing import (
    Tuple as _Tuple,
    List as _List,
    Union as _Union,
    Dict as _Dict,
    Any as _Any
)

import numpy as _np
import yaml as _yaml

from ...io._path_loader import PathLoader

from ._os import AstriOpticalSystem
from ._camera import AstriCameraGeometry, AstriCherenkovCamera
from ..._iact import IACT as _IACT

class AstriTelescope(_IACT):
    """ASTRI telescope.

    See Also
    --------
        :py:class:`iactsim.IACT`:
    """
    def __init__(
        self,
        optical_system = None,
        camera: AstriCherenkovCamera = None,
        position: _Tuple[float, float, float] | _List[float] | _np.ndarray = (0.,0.,0.),
        pointing: _Tuple[float, float] | _List[float] | _np.ndarray = (0,0),
    ):
        if optical_system is None:
            optical_system = AstriOpticalSystem()
        if camera is None:
            camera = AstriCherenkovCamera()
        super().__init__(
            optical_system = optical_system,
        )
        self.position = position
        self.pointing = pointing
        self.camera = camera
    
    def load_atmospheric_transmission(self, filepath: str):
        wavelength, height, value = self.optical_system.load_efficiency_data(filepath)
        self.atmospheric_transmission.altitude = height
        self.atmospheric_transmission.wavelength = wavelength
        self.atmospheric_transmission.value = value

    def configure(self, config: _Union[str, _Path, _Dict[str, _Any]]) -> None:
        """Configure the telescope with a yaml configuration file or dictionaries.
        The configuration files can contain more than a document to initialize also
        the optical system and the Cherenkov camera::

            ----
            # Telescope configuration
            # ...
            # ...
            ----
            # Optical system configuration
            # ...
            # ...
            ----
            # Camera configuration
            # ...
            # ...

        Parameters
        ----------
        config : str, path-like, or dict
            Path to the configuration file (str or pathlib.Path),
            or a dictionary containing the configuration.
        """
        configs = [None]*3

        if isinstance(config, (str, _Path)):
            with open(config, 'r') as file:
                tel_conf = _yaml.load_all(file, Loader=PathLoader)
                for i,d in enumerate(tel_conf):
                    configs[i] = d
        elif isinstance(config, list):
            for i,d in enumerate(config):
                configs[i] = d
        elif isinstance(config, dict):
            configs[0] = config
        else:
            raise TypeError(
                "config must be a string (path), pathlib.Path, a list of dictionaries or a dictionary, "
                f"not {type(config)}"
            )

        n_documents = sum(d is not None for d in configs)

        if n_documents > 3:
            raise(RuntimeError('The configuration file can contain at most 3 document in the following order: telescope, optical system and camera.'))

        if n_documents == 0:
            raise(RuntimeError('The configuration file is empty.'))
        
        self._configure(configs[0])

        if configs[1] is not None:
            self.optical_system.configure(configs[1])
        
        if configs[2] is not None:
            self.camera.configure(configs[2])
        
        self.cuda_init()

    def _configure(self, tel_conf: _Dict[str, _Any]) -> None:
        """Configure the telescope with a dictionary.
        """
        # Assign only these
        assign_directly = [
            'altitude',
            'azimuth',
            'show_progress'
        ]

        for name in tel_conf.keys():
            value = tel_conf[name]
            if value is not None:
                if name in assign_directly:
                    setattr(self, name, value)
                if name == 'atmospheric_transmission':
                    self.load_atmospheric_transmission(value)