.. Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
.. SPDX-License-Identifier: GPL-3.0-or-later
..
.. This file is part of iactsim.
..
.. iactsim is free software: you can redistribute it and/or modify
.. it under the terms of the GNU General Public License as published by
.. the Free Software Foundation, either version 3 of the License, or
.. (at your option) any later version.
..
.. iactsim is distributed in the hope that it will be useful,
.. but WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
.. GNU General Public License for more details.
..
.. You should have received a copy of the GNU General Public License
.. along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

.. _about:

Overview
========

`iactsim` is a Python package designed for simulating the response of Imaging Atmospheric Cherenkov Telescopes (IACTs). 
It exploits the computational power of GPUs to accelerate computationally intensive tasks such as ray-tracing and SiPM response simulation. 
This project aims to provide a fast, flexible, and user-friendly simulation framework for IACT performance studies, instrument design and data analysis.
  
  - `Software documentation <https://iact-sim-49dba6.gitlab.io/>`_
  - `Source code <https://gitlab.com/davide.mollica/iactsim>`_


Usage examples
--------------

Optical system definition
"""""""""""""""""""""""""

  .. code-block:: python

        import iactsim
        import matplotlib.pyplot as plt

        from iactsim.optics import (
            ApertureShape,
            SurfaceType,
            OpticalSystem
        )

        plt.style.use('iactsim.iactsim')

        # Spherical mirror
        mirror_curvature_radius = 20000
        plate_scale = mirror_curvature_radius/57.296/2.
        mirror = iactsim.optics.SphericalSurface(
            half_aperture=10000., 
            curvature=1./mirror_curvature_radius,
            position=(0,0,0),
            surface_type=REFLECTIVE_OUT, # reflective in the pointing direction
            name = 'Mirror'
        )

        # Flat focal surface (5deg hexagon)
        focal_plane = iactsim.optics.FlatSurface(
            half_aperture = 5*plate_scale, 
            position = (0,0,0.5*mirror_curvature_radius),
            aperture_shape = ApertureShape.HEXAGONAL,
            surface_type=SurfaceType.SENSITIVE_IN, # sensitive surface opposite to the pointing direction
            name = 'Focal Plane'
        )

        # Optical system
        os = OpticalSystem(surfaces=[focal_plane, mirror], name='TEST-OS')

        # Telescope position
        pos = (0,0,0)

        # Telescope pointing (alt,az)
        poi = (0.,0.)

        # IACT
        telescope = iactsim.IACT(os, position=pos, pointing=poi)

        # Copy data to the device
        telescope.cuda_init()

        # Photon source initialized on-axis 
        source = iactsim.optics.sources.Source(telescope)
        source.positions.radial_uniformity = False
        source.positions.random = False

        # Plot spot diagram at different off-axis angles
        n_plots = 5
        fig, axes = plt.subplots(1,n_plots,figsize=(3.5*n_plots,3.5))

        source.directions.altitude -= 2.
        for ax in axes:
            # Adjust photon position to match the mirror position
            source.set_target('Mirror')
            
            # Generate photons
            ps, vs, wls, ts = source.generate(10000)
            
            # Perform ray-tracing
            telescope.trace_photons(ps, vs, wls, ts)
            
            # Plot spot diagram
            iactsim.visualization.scatter(
                ps,
                s=0.2,
                ax=ax,
                color='black',
                alpha=0.5,
                scale=plate_scale
            )
            ax.set_xlabel('X (deg)')
            ax.set_ylabel('Y (deg)')
            ax.grid(ls='--')

            # Move the source
            source.directions.altitude += 1. # degree

        plt.tight_layout()
        plt.show()

.. image:: /images/psf.png
   :width: 720

Mirrors segmentation
""""""""""""""""""""

The following code provides an example of how to segment a surface (``AsphericalSurface``, ``SphericalSurface`` or ``FlatSurface``) starting from a mother surface (in this case ``mirror``).
Note that each segment is an independent surface and does not need a mother surface, which is used here simply for convenience.

    .. code-block:: python

        import numpy as np

        # List of segments
        segments = []

        # Segment ID
        k = 0

        # Segments on a 10X10 grid, 80 total
        n = 10

        segment_distance = 2*mirror.half_aperture / (n+3)

        for i in range(n+3):
            for j in range(n+3):
                offset = [
                    -mirror.half_aperture+segment_distance*i,
                    -mirror.half_aperture+segment_distance*j
                ]
                r_segment = np.sqrt(offset[0]**2+offset[1]**2)
                
                # Do not create segments outside the original mirror aperture
                if r_segment > mirror.half_aperture-segment_distance*np.sqrt(2):
                    continue

                # Ideal segment position
                segment_position = [
                    offset[0],
                    offset[1],
                    mirror.sagitta(r_segment),
                ]
                
                # Create the surface
                segment = iactsim.optics.SphericalSurface(
                    curvature=mirror.curvature,
                    half_aperture=0.45*segment_distance, 
                    position=segment_position,
                    surface_type=mirror.type,
                    name = f'Segment-{k}',
                    aperture_shape=ApertureShape.SQUARE,
                    tilt_angles=np.random.normal(0,1,3), # Big random dispersion
                    scattering_dispersion=0.05
                )
                
                # Specify the segment offset
                # When a segment is created in this way:
                #  - it will be oriented with the same surface normal 
                #    of the mother surface at the specified offset 
                #  - `tilt_angles` attribute will define a deviation from this orientation.
                segment.offset = offset
                
                segments.append(segment)
                k += 1

        # Optical system
        segmented_os = OpticalSystem(
            surfaces=[focal_plane, *segments],
            name='SEGMENTED-TEST-OS'
        )

        # IACT
        segmented_telescope = iactsim.IACT(segmented_os)
        segmented_telescope.cuda_init()

        # Plot spot diagram at different off-axis angles
        n_plots = 5
        fig, axes = plt.subplots(1,n_plots,figsize=(3.5*n_plots,3.5))

        # Photon source initialized on-axis 
        source = iactsim.optics.sources.Source(segmented_telescope)
        source.positions.radial_uniformity = False
        source.positions.random = False
        source.positions.r_max = mirror.half_aperture*1.5

        source.directions.altitude -= 2.
        for ax in axes:
            # Adjust photon position to match the mirror position
            source.set_target()
            
            # Generate photons
            ps, vs, wls, ts = source.generate(10000)
            
            # Perform ray-tracing
            segmented_telescope.trace_photons(ps, vs, wls, ts)
            
            # Plot spot diagram
            iactsim.visualization.scatter(
                ps,
                s=0.2,
                ax=ax,
                color='black',
                alpha=0.5,
                scale=plate_scale
            )
            ax.set_xlabel('X (deg)')
            ax.set_ylabel('Y (deg)')
            ax.grid(ls='--')

            # Move the source
            source.directions.altitude += 1. # degree

        plt.tight_layout()
        plt.show()

.. image:: /images/segmented_psf.png
   :width: 720

Visualize your geometry
"""""""""""""""""""""""

For optical systems with complex geometry, it is often useful to perform a visual check of the geometry. To do so, a `VTK <https://docs.vtk.org/en/latest/getting_started/index.html>`_ visualizer is provided:

    .. code-block:: python
        
        from iactsim.visualization import VTKOpticalSystem
        renderer = VTKOpticalSystem(segmented_telescope.optical_system)
        renderer.start_render()

.. image:: /images/vtk_os.png
   :align: center
   :width: 400

Visualize ray-tracing
"""""""""""""""""""""

.. code-block:: python

    segmented_telescope.visualize_ray_tracing(*source.generate(10000))

.. image:: /images/iactsim_visualize_raytracing.png
   :align: center
   :width: 400