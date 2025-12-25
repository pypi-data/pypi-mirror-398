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

from pathlib import Path
from typing import Tuple, Union, Dict, Any

import numpy as np
import yaml

from ...optics._surface_misc import SurfaceType
from ...optics._surface import AsphericalSurface, FlatSurface, SphericalSurface, CylindricalSurface, ApertureShape, SurfaceShape
from ...optics._optical_system import OpticalSystem
from ...optics._materials import Materials

from ...io._path_loader import PathLoader

class AstriOpticalSystem(OpticalSystem):
    """ASTRI optical system class.

    See Also
    --------
        :py:class:`iactsim.optics.OpticalSystem`:
    """
    def __init__(self):
        #####
        # M1
        #####
        r_1 = 2153.
        c_1 = 1/8223.
        k_1 = 0.
        A_1 = -np.array([
            0.0,
            9.610594335657154e-13,
            -5.655007251743067e-20,
            6.779846300812014e-27,
            3.895878871219899e-33,
            5.280381799628059e-40,
            -2.991060741547783e-47,
            -4.391530590471279e-53,
            -6.174332023811481e-60,
            2.7358654573036966e-66
        ])
        self.m1 = AsphericalSurface(
            r_1, c_1, k_1, A_1,
            surface_type=SurfaceType.REFLECTIVE_OUT,
            aperture_shape=ApertureShape.CIRCULAR,
            central_hole_shape=ApertureShape.HEXAGONAL,
            central_hole_half_aperture=423.,
            name='M1'
        )

        #####
        # M2
        #####
        r_2 = 900.
        c_2 = -1/2180.
        k_2 = 0.
        A_2 = -np.array([
            0.0,
            1.620759030635574e-11,
            -2.895843564948884e-17,
            8.633712193781264e-24,
            3.348558057289531e-30,
            -1.033610024069273e-36,
            -6.735253655133213e-43,
            -3.0654711881577763e-49,
            3.1716123568176433e-55,
            -3.711831037954923e-62
        ])
        self.m2 = AsphericalSurface(
            r_2, c_2, k_2, A_2,
            surface_type=SurfaceType.REFLECTIVE_IN,
            name='M2'
        )

        ###############
        # Focal Plane
        ###############
        c_fp = -1./1060.
        r_fp = 250.
        self.fp = SphericalSurface(
            half_aperture=r_fp,
            curvature=c_fp,
            surface_type=SurfaceType.SENSITIVE_OUT,
            name='FP'
        )

        # M1 at origin
        self.m1.position = (0, 0, 0)

        # M1-M2 distance
        m1_m2_d = 3108.4
        self.m2.position = (0, 0, m1_m2_d)

        # M2-FP distance
        self._back_focal_length = 519.6
        self.fp.position = (0, 0, self.m2.axial_position - self._back_focal_length)

        #######################
        # Dummy camera window
        #######################
        r_fl = 250.
        self._dummy_window = FlatSurface(
            r_fl,
            position=(0,0,self.m2.axial_position-self._back_focal_length+1),
            surface_type=SurfaceType.DUMMY,
            name=f'Window'
        )

        ##############
        # Camera body
        ##############
        self._camera_body_size = [250, 400]
        camera_body = CylindricalSurface(
            radius=self._camera_body_size[0],
            height=self._camera_body_size[1],
            surface_type=SurfaceType.OPAQUE,
            name='CameraBody'
        )
        # Top of the body on the window surface closer to M2
        camera_body.position = (0., 0., self._dummy_window.axial_position-0.5*self._camera_body_size[1])
        camera_body.tilt_angles = (0., 0., 0.)
        camera_body.top = False
        camera_body.bottom = True

        ###############
        # Central tube
        ###############
        central_tube_height = camera_body.position[2]-self._camera_body_size[1]*0.5
        central_tube = CylindricalSurface(
            radius=203.2,
            height=central_tube_height,
            position=(0,0,0.5*central_tube_height),
            has_bottom=True,
            has_top=True,
            surface_type=SurfaceType.OPAQUE,
            name='CentralTube'
        )

        #################################################
        # M2 baffle (should be updated if M2 is tilted)
        #################################################
        m2_baffle_pos = self.m2.position.copy()
        m2_baffle_pos[2] += self.m2.sagitta(900)
        m2_baffle_surface_1 = FlatSurface(
            position = m2_baffle_pos,
            half_aperture = 1070.,
            central_hole_half_aperture=900.,
            surface_type=SurfaceType.OPAQUE,
            name='M2-baffle-1'
        )

        baffle_dz = 150.4 # 3108.4-2958
        m2_baffle_surface_2 = CylindricalSurface(
            position = m2_baffle_pos-np.asarray([0,0,0.5*baffle_dz]),
            radius = 1070.,
            height = baffle_dz,
            surface_type=SurfaceType.OPAQUE,
            has_bottom=False,
            has_top=False,
            name='M2-baffle-2'
        )

        super().__init__(surfaces=[self.m1,self.m2,self._dummy_window,self.fp,camera_body,central_tube, m2_baffle_surface_1, m2_baffle_surface_2], name='ASTRI-OS')

    def build_masts(self):
        # ASTRI telescope have 3 group of masts radially simmetric
        # In the following the first group is defined and then 
        # the other two groups are generated from a rotation
        # of the first group around the optical axis.

        ##################################
        # Define the first group of masts
        ##################################

        # Main mast
        mast1_radius = 50.8
        mast1_height = 3135.28 + 100
        mast1_position = [0,-1729.66,1407.78]
        # Secondary masts
        mast2_radius = mast3_radius = 38.05
        mast2_height = 2290.78-50
        mast2_position = [0,-1214.62,1162.12]
        mast3_height = 1156.94
        mast3_position = [0,-705.21,2311.20]
        # Negligible
        hollow = True

        # Define telescope mast group (with a x-rotation)
        mast1_1 = CylindricalSurface(
            radius=mast1_radius,
            height=mast1_height,
            has_bottom=not hollow,
            has_top=not hollow,
            position=mast1_position,
            tilt_angles=((63.9-90),0,0),
            name="Mast1-1"
        )
        mast1_2 = CylindricalSurface(
            radius=mast2_radius,
            height=mast2_height,
            has_bottom=not hollow,
            has_top=not hollow,
            position=mast2_position,
            tilt_angles=((32.6-90),0,0),
            name="Mast1-2"
        )
        mast1_3 = CylindricalSurface(
            radius=mast3_radius,
            height=mast3_height,
            has_bottom=not hollow,
            has_top=not hollow,
            position=mast3_position,
            tilt_angles=((90-43.9),0,0),
            name="Mast1-3"
        )
        self.add_surface(mast1_1, replace=True)
        self.add_surface(mast1_2, replace=True)
        self.add_surface(mast1_3, replace=True)

        ####################################
        # Define the other mast groups 
        # rotating the first by 60 deg and 
        # 120 deg around the telescope axis
        ####################################
        theta = 2*np.pi/3
        for i in range(1,3):
            # z-rotation matrix
            cos_z = np.cos(i*theta)
            sin_z = np.sin(i*theta)
            z_rot = np.array([
                [ cos_z, -sin_z, 0.],
                [ sin_z,  cos_z, 0.],
                [    0.,     0., 1.],
            ])
            # New masts to be rotated
            mast_i_1 = CylindricalSurface(
                radius=mast1_radius,
                height=mast1_height,
                has_bottom=not hollow,
                has_top=not hollow,
                position=z_rot@mast1_1.position,
                name=f"Mast{i+1}-1"
            )
            mast_i_2 = CylindricalSurface(
                radius=mast2_radius,
                height=mast2_height,
                has_bottom=not hollow,
                has_top=not hollow,
                position=z_rot@mast1_2.position,
                name=f"Mast{i+1}-2"
            )
            mast_i_3 = CylindricalSurface(
                radius=mast3_radius,
                height=mast3_height,
                has_bottom=not hollow,
                has_top=not hollow,
                position=z_rot@mast1_3.position,
                name=f"Mast{i+1}-3"
            )

            # Define the first mast group then replicate the group with two consecutive 60 deg rotation around z-axis
            # rot = get_rotation_matrix().T ---> surface to telescope, the mast orientation in the telescope reference system
            # new_rot = z_rot @ rot ---> surface to telscope, rotated mast orientation in the telescope reference system
            # update_surface_rot = new_rot.T ---> telescope to surface!
            for mast_i_x, mast1_x in zip([mast_i_1,mast_i_2,mast_i_3],[mast1_1,mast1_2,mast1_3]):
                surface_to_telescope = mast1_x.get_rotation_matrix().T
                updated_surface_to_telescope = z_rot @ surface_to_telescope
                updated_telescope_to_surface = updated_surface_to_telescope.T
                mast_i_x.set_rotation_matrix(updated_telescope_to_surface)
            
            # Finally, add the rotated mast group
            self.add_surface(mast_i_1, replace=True)
            self.add_surface(mast_i_2, replace=True)
            self.add_surface(mast_i_3, replace=True)

    @property
    def camera_body_size(self):
        """Cylindrical camera body dimensions (radius and height)."""
        return self._camera_body_size
    
    @camera_body_size.setter
    def camera_body_size(self, a_size):
        if 'Window' in self:
            last_surface = self['Window']
        elif 'Window5':
            last_surface = self['Window5']
        else:
            last_surface = None
        
        self._camera_body_size = a_size
        
        if 'CameraBody' in self:
            self['CameraBody'].radius = a_size[0]
            self['CameraBody'].height = a_size[1]
            if last_surface is not None:
                p0 = last_surface.position
                fp_radius = last_surface.half_aperture
            else:
                p0 = self['FP'].position
                fp_radius = self['FP'].half_aperture
            self['CameraBody'].position = (0, 0, p0[2]-0.5*a_size[1]+17.3) # TODO:  edge between top filter and camera body

            if a_size[0]-fp_radius < 0:
                raise(ValueError("camera body size must be greater than camera window size."))
            
            if a_size[0]-fp_radius > 0.1: #mm
                top_camera_body = FlatSurface(
                    half_aperture = a_size[0],
                    central_hole_half_aperture=fp_radius,
                    surface_type=SurfaceType.OPAQUE,
                    position=(p0[0], p0[1], p0[2]+17.3), # TODO:  edge between top filter and camera body
                    name='CameraBodyTop'
                )
                self.add_surface(top_camera_body, replace=True)
        
            if 'CentralTube' in self:
                self['CentralTube'].height = self['CameraBody'].position[2]-self['CameraBody'].height*0.5
                self['CentralTube'].position = (0,0,0.5*self['CentralTube'].height)

    @property
    def camera_window_parameters(self):
        """Camera window parameterization:

            - window radius
            - SiPM window distance
            - layers thickness
            - layers separation
            - focus shift (opposite to the pointing direction)
        
        If None (or all None) a dummy flat surface is used.

        """
        return self._camera_window_parameters
    
    @camera_window_parameters.setter
    def camera_window_parameters(self, distances):
        if hasattr(distances, '__len__'):
            if all([x is None for x in distances]):
                distances = None
        if distances is None:
            for k in range(6):
                self.remove_surface(f'Window{k}')
            self.remove_surface('Window')
            self.add_surface(self._dummy_window)
            self['CameraBody'].position = (0,0,self._dummy_window.axial_position-0.5*self._camera_body_size[1]+17.3) # TODO: edge between top filter and camera body
            self['FP'].position = (0, 0, self['M2'].axial_position - self._back_focal_length)
        else:
            # Remove dummy window
            self.remove_surface('Window')
            fp_z_pos = self['M2'].axial_position - self._back_focal_length - distances[4]
            self['FP'].position = (0, 0, fp_z_pos)
            z = fp_z_pos
            dz = [
                distances[1],
                distances[2],
                distances[3],
                distances[2],
                distances[3],
                distances[2]
            ]
            for k in range(6):
                if k%2 == 0:
                    material_in = Materials.FUSED_SILICA
                    material_out = Materials.AIR
                else:
                    material_out = Materials.FUSED_SILICA
                    material_in = Materials.AIR
                z = z + dz[k]
                s = FlatSurface(
                    distances[0],
                    position=(0,0,z),
                    surface_type=SurfaceType.REFRACTIVE,
                    material_in=material_in,
                    material_out=material_out,
                    name=f'Window{k}'
                )
                self.add_surface(s, replace=True)

        # Update camera body position
        self.camera_body_size = self.camera_body_size

        self._camera_window_parameters = distances
    
    def check_surface(self, surface, n=100_000, ax=None, true_position=False, color=None, source_radius=None):
        from ..._iact import IACT
        from ...optics.sources._source import Source
        from ...optics.sources.positions._sources import UniformSphericalCap
        from ...optics.sources.directions._sources import UniformBeam
        import matplotlib.pyplot as plt

        if surface in self:
            s = self[surface]
            old_type = s.type
            old_position = s.position
            s.type = SurfaceType.TEST_SENSITIVE
            s.position = (0,0,0)
            os = OpticalSystem(surfaces=[s], name='TEST-OS')
            test = IACT(os)
            test.cuda_init()

            if source_radius is None:
                if s._shape == SurfaceShape.CYLINDRICAL:
                    source_radius = 1.1*max(s.radius, s.height)
                else:
                    source_radius = 1.1*s.half_aperture
            
            source = Source(test)
            source.positions = UniformSphericalCap(source_radius, 180)
            source.directions = UniformBeam(90,0,360)
            ps, vs, wls, ts = source.generate(n)
            test.trace_photons(ps,vs,wls,ts)
            where = ~np.isnan(ts)
            ps = ps[where]

            s.type = old_type
            s.position = old_position

            if true_position:
                ps[:,0] += s.position[0]
                ps[:,1] += s.position[1]
                ps[:,2] += s.position[2]

            if ax is not None:
                fig = plt.gcf()
            else:
                fig = plt.figure()
                ax = fig.add_subplot(projection='3d')
            
            ax.scatter(*ps.get().T/1000, s=0.1, color=color)
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')

            if not true_position:
                ax.set_xlim(-source_radius/1000, source_radius/1000)
                ax.set_ylim(-source_radius/1000, source_radius/1000)
                ax.set_zlim(-source_radius/1000, source_radius/1000)

            return fig, ax

    def configure(self, config: Union[str, Path, Dict[str, Any]]) -> None:
        """Configure the optical system with a yaml configuration file or a dictionary.

        Parameters
        ----------
        config : str, path-like, or dict
            Path to the configuration file (str or pathlib.Path),
            or a dictionary containing the configuration.
        """

        if isinstance(config, (str, Path)):
            with open(config, 'r') as file:
                os_conf = yaml.load(file, Loader=PathLoader)
        elif isinstance(config, dict):
            os_conf = config
        else:
            raise TypeError(
                "config must be a string (path), pathlib.Path, or a dictionary, "
                f"not {type(config)}"
            )

        if 'include_masts' in os_conf:
            if os_conf['include_masts'] == True:
                self.build_masts()

        if 'camera_window_parameters' in os_conf:
            values = os_conf['camera_window_parameters']
            if values is not None and len(values) < 5:
                raise(ValueError('Not enough values provided to configure the camera window (window radius, SiPM-window distance, layers thickness, layers separation and focus shift)'))
        else:
            values = None
        self.camera_window_parameters = values
        
        if 'camera_body_size' in os_conf:
            values = os_conf['camera_body_size']
            if len(values) < 1:
                raise(ValueError('Not enough values provided to configure the camera body (radius and depth.)'))
            self.camera_body_size = values

        for surface_name in ['M1', 'M2', 'Window']:
            if surface_name not in os_conf:
                continue
            
            if 'M1' not in self:
                self.add_surface(self.m1)
            
            surface_dict = os_conf[surface_name]

            eff = None
            if 'efficiency' in surface_dict:
                eff_file = surface_dict['efficiency']
                if eff_file is not None:
                    x1, x2, eff = self.load_efficiency_data(eff_file)                    
            
            scattering_dispersion = None
            if 'scattering_dispersion' in surface_dict:
                scattering_dispersion = surface_dict['scattering_dispersion']

            if surface_name == 'Window':
                if "Window5" in self:
                    s_names = ["Window1", "Window3", "Window5"]
                    if eff is not None:
                        eff = np.cbrt(eff)
                    if scattering_dispersion is not None:
                        scattering_dispersion /= np.sqrt(3)
                else:
                    s_names = ['Window']
            else:
                s_names = [surface_name]
                
            for s_name in s_names:
                if eff is not None:
                    surface_prop = self[s_name].properties
                    surface_prop.wavelength = x1
                    surface_prop.incidence_angle = x2
                    if surface_name.startswith("Win"):
                        # No window reflectance for now
                        surface_prop.transmittance = eff
                        surface_prop.absorption = 1.-eff
                        surface_prop.reflectance = eff*0.
                    else:
                        # No mirror transmittance
                        surface_prop.reflectance = eff
                        surface_prop.absorption = 1.-eff
                        surface_prop.transmittance = np.zeros_like(eff)
                        surface_prop.reflectance_back = np.zeros_like(eff)
                        surface_prop.absorption_back = np.ones_like(eff)
                        surface_prop.transmittance_back = np.zeros_like(eff)
                        # M2 is defined as a concave mirror, so front and back efficiencies must be swapped
                        if s_name == 'M2':
                            surface_prop.reflectance_back, surface_prop.reflectance = surface_prop.reflectance, surface_prop.reflectance_back
                            surface_prop.transmittance_back, surface_prop.transmittance = surface_prop.transmittance, surface_prop.transmittance_back
                            surface_prop.absorption_back, surface_prop.absorption = surface_prop.absorption, surface_prop.absorption_back

                if scattering_dispersion is not None:
                    self[s_name].scattering_dispersion = scattering_dispersion
        
        if "M1-segments" in os_conf:
            segments_conf = os_conf["M1-segments"]
            if 'use' in segments_conf and segments_conf['use']:
                for key in segments_conf:
                    if key == 'use': 
                        continue
                    segment_conf = segments_conf[key] 
                    
                    offset = segment_conf['offset']
                    if offset is None:
                        continue

                    half_aperture = segment_conf['half_aperture']
                    if half_aperture is None:
                        continue

                    shift = [0,0,0]
                    if 'position_shift' in segment_conf:
                        position_shift = segment_conf['position_shift']
                        if position_shift is not None:
                            for i in range(len(position_shift)):
                                shift[i] = position_shift[i]
                    
                    tilt_angles = [0,0,0]
                    if 'tilt_angles' in segment_conf:
                        angles = segment_conf['tilt_angles']
                        if angles is not None:
                            for i in range(len(angles)):
                                tilt_angles[i] = angles[i]
                    
                    scattering_dispersion = None
                    if 'scattering_dispersion' in segment_conf:
                        scattering_dispersion = segment_conf['scattering_dispersion']
                    if scattering_dispersion is None:
                        if 'M1' in self:
                            scattering_dispersion = self['M1'].scattering_dispersion
                        else:
                            scattering_dispersion = 0.
                    
                    curvature = None
                    if 'curvature' in segment_conf:
                        curvature = segment_conf['curvature']
                    if curvature is None:
                        if 'M1' in self:
                            curvature = self['M1'].curvature
                        else:
                            curvature = self.m1.curvature
                    
                    position = [
                        offset[0] + shift[0],
                        offset[1] + shift[1],
                        self.m1.sagitta(np.sqrt(offset[0]**2+offset[1]**2)) + shift[2],
                    ]
                    segment = AsphericalSurface(
                        conic_constant=self.m1.conic_constant,
                        aspheric_coefficients=self.m1.aspheric_coefficients,
                        half_aperture=half_aperture, 
                        curvature=curvature,
                        position=position,
                        surface_type=self.m1.type,
                        name = f'M1-segment-{key}',
                        aperture_shape=ApertureShape.HEXAGONAL,
                        tilt_angles=tilt_angles,
                        scattering_dispersion=scattering_dispersion
                    )
                    segment.offset = offset

                    if 'efficiency' in segment_conf and segment_conf['efficiency'] is not None:
                        efficiency_file = segment_conf['efficiency']
                        # No mirror transmittance
                        x1, x2, eff = self.load_efficiency_data(efficiency_file)
                        segment.properties.reflectance = eff
                        segment.properties.absorption = 1.-eff
                        segment.properties.transmittance = np.zeros_like(eff)
                        segment.properties.reflectance_back = np.zeros_like(eff)
                        segment.properties.transmittance_back = np.zeros_like(eff)
                        segment.properties.absorption_back = np.ones_like(eff)
                        segment.properties.wavelength = x1
                        segment.properties.incidence_angle = x2
                    else:
                        if 'M1' in self:
                            segment.properties = self['M1'].properties

                    self.add_surface(segment, replace=True)
                
                self.remove_surface('M1')

    @staticmethod
    def load_efficiency_data(filepath: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Loads surface efficiency data from a specially formatted text file.

        Args
        ----
            filepath: Path to the text file.

        Returns
        -------
            A tuple containing:
            - wavelengths: 1D NumPy array of wavelengths.
            - incidence_angles: 1D NumPy array of incidence angles.
            - efficiencies: 2D NumPy array of efficiencies (rows: angles, cols: wavelengths).

        Notes
        -----
            The input file must be formatted as following::
            
                # Efficiency example
                # Wavelengths (nm)
                300. 350. 450. 500. 550. 600.
                # Incidence angles (degree)
                0. 30. 60. 90.
                # Values
                # A row for each angle
                # Angle 0.
                1. 1. 1. 1. 1. 1.
                # Angle 30.
                0.9 0.9 0.9 0.9 0.9 0.9
                # etc
                0.6 0.6 0.6 0.6 0.6 0.6
                0. 0. 0. 0. 0. 0.

            The first not commented line is interpreted as wavelengths.
            The second not commented line is interpreted as incidence angles.
            The rest of the lines are interpreted as the efficiency values.
            Empty lines are allowed to be present only to indicate that a dependecy is missing::

                # Efficiency example
                # Wavelengths (nm)
                300. 350. 450. 500. 550. 600.
                # Incidence angles
                
                # Values
                1. 1. 1. 1. 1. 1.
            
        
        """
        lines = []
        empties = 0
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line.startswith('#'):
                    if line == "":
                        empties += 1
                        if empties > 1:
                            raise(RuntimeError(f"{filepath}: at most one empty line is allowed in an efficiency file."))
                    lines.append(line)
        
        wavelengths = np.fromstring(lines[0], sep=' ')
        if wavelengths.shape[0] == 1 and wavelengths[0] == -1:
            wavelengths = None
        
        incidence_angles = np.fromstring(lines[1], sep=' ')
        if incidence_angles.shape[0] == 1 and incidence_angles[0] == -1:
            incidence_angles = None
        
        if incidence_angles is None and wavelengths is None:
            raise(RuntimeError(f"{filepath}: no wavelength or incidence angle found."))

        efficiencies = np.array([np.fromstring(line, sep=' ') for line in lines[2:]])

        return wavelengths, incidence_angles, efficiencies  