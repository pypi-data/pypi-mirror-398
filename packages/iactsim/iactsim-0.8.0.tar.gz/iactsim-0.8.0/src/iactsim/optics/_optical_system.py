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

from typing import List, Dict, Optional
from tabulate import tabulate

from ._surface import AsphericalSurface, Surface
from ._surface_misc import SurfaceType

# TODO: add insert e ramove methods
class OpticalSystem():
    """Represents a generic optical system.

    Parameters
    ----------
    name : str, optional
        Name of the optical system, by defaults "OS".
    surfaces : List[Surface]
        List of Surface objects representing the optical surfaces in the
        system. The order of the surfaces in the list defines the sequential
        order for ray tracing.

    Notes
    -----
    The order of surfaces for ray tracing is determined by the order of the
    objects in the `surfaces` list.
    Each surface has a `name` attribute that is used for named access. If a
    surface's name is None, a default name "Surface_i" (where i is the index)
    is assigned.

    """

    def __init__(
        self,
        surfaces: List[Surface],
        name: Optional[str] = None,
    ):
        self._name = name if name is not None else "OS"
        self._surfaces: List[Surface] = []
        self._surface_map: Dict[str, Surface] = {}

        for i, surface in enumerate(surfaces):
            if surface.name is None:
                default_name = f"Surface_{i}"
                surface.name = default_name  # Assign a name to the surface.
            else:
                default_name = surface.name

            if default_name in self._surface_map:
                raise ValueError(f"Duplicate surface name: {default_name}")

            self._surfaces.append(surface)
            self._surface_map[default_name] = surface
        
        if not any([self._is_surface_sensitive(s) for s in self]):
            raise(RuntimeError(f'No sensitive surfaces defined for OpticalSystem {self._name}.'))

    @staticmethod
    def _is_surface_sensitive(surface):
        needed = [
            SurfaceType.SENSITIVE,
            SurfaceType.SENSITIVE_IN,
            SurfaceType.SENSITIVE_OUT,
            SurfaceType.TEST_SENSITIVE
        ]
        return any([surface.type == t for t in needed])

    @property
    def name(self) -> str:
        return self._name

    def remove_surface(self, surface):
        """Remove a given surface.

        Parameters
        ----------
        surface : Surface or str
            Surface instance or name to be removed.
        """
        if isinstance(surface, str):
            if surface not in self:
                return
            surface = self[surface]
        
        self._surface_map.pop(surface.name)
        self._surfaces = list(self._surface_map.values())


    def add_surface(self, surface, replace=False):
        """Add a surface to the optical syste.

        Parameters
        ----------
        surface : Surface
            Surface to be added.
        replace : bool, optional
            Whether to replace an exisisting surface with the same name, by default False.

        Raises
        ------
        ValueError
            If the surface already exists and `replace` is `False`.
        """
        if surface in self:
            if not replace:
                raise ValueError(f"Surface '{surface.name}' already placed. If you want to overwrite it use replace=True.")
            self.remove_surface(surface)
        
        if surface.name is None:
            surface.name = f"Surface_{len(self)}"

        self._surfaces.append(surface)
        self._surface_map[surface.name] = surface

    @property
    def surfaces_dict(self) -> Dict[str, AsphericalSurface]:
        """Provides a dictionary view of the surfaces, mapping names to :py:class:`Surface` objects."""
        return self._surface_map.copy()

    def __contains__(self, x):
        if issubclass(type(x), Surface):
            x = x.name
        if x in self._surface_map.keys():
            return True

    def __iter__(self):
        """
        Returns an iterator over the optical surfaces.

        Returns
        -------
        iterator
            An iterator object that iterates through the surfaces in `self._surfaces`.
        """
        return iter(self._surfaces)

    def __len__(self):
        """
        Returns the number of optical surfaces in the system.

        Returns
        -------
        int
            The number of surfaces.
        """
        return len(self._surfaces)

    def __getitem__(self, key: str | int):
        """
        Allows accessing individual surfaces using indexing or by surface name.

        Parameters
        ----------
        key : str | int
            The name or index of the desired surface.

        Returns
        -------
        OpticalSurface
            The optical surface with the specified name or at the specified index.

        Raises
        ------
        KeyError
            If a surface with the given name is not found.
        IndexError
            If the index is out of range.
        TypeError
            If the key is neither a string nor an integer.
        """
        if isinstance(key, str):
            if key not in self._surface_map:
                raise KeyError(f"No surface found with name '{key}'")
            return self._surface_map[key]
        elif isinstance(key, int):
            return self._surfaces[key]
        else:
            raise TypeError("Key must be a string (name) or an integer (index)")

    def _get_table_data(self, tablefmt: str = "grid") -> str:
        """Constructs the data for tabulate optical system info.

        Parameters
        ----------
        tablefmt : str
            Format specifier for tabulate, by defaults "grid"

        Returns
        -------
        str
            Tabulated string representation of the optical system data
        """
        data = []
        for name, surface in self.surfaces_dict.items():
            material_in_name = (
                surface.material_in.name
                if surface.material_in is not None
                else "None"
            )
            material_out_name = (
                surface.material_out.name
                if surface.material_out is not None
                else "None"
            )
            data.append([name, f"{surface.position[2]:3.3f}", material_in_name, material_out_name, surface.type.name])

        headers = ["Surface Name", "Axial Position", "Material above", "Material below", "Surface Type"]

        return tabulate(data, headers=headers, tablefmt=tablefmt)

    def __repr__(self) -> str:
        """Returns a string representation of the optical system."""
        title = f"**Optical System: {self.name}**\n"
        return title + self._get_table_data()

    def _repr_html_(self) -> str:
        """Returns an HTML representation of the optical system for Jupyter Notebook."""
        title = f"<h5>Optical System: {self.name}</h5>"
        table = self._get_table_data(tablefmt="html")
        return title + table

    def _repr_markdown_(self) -> str:
        """Returns a Markdown representation of the optical system."""
        title = f"**Optical System: {self.name}**\n\n"
        table = self._get_table_data(tablefmt="pipe")
        return title + table