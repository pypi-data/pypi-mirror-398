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
import vtk

from ._vtk_utils import (
    create_aspheric_surface_actor,
    create_cylindric_surface_actor,
    quit
)

from ..optics._surface_misc import SurfaceType, SurfaceShape

from ..optics._cpu_transforms import local_to_telescope_rotation

from .._iact import IACT

from ..optics._optical_system import OpticalSystem


class VTKOpticalSystem():
    """Class to viasualize the geometry of an optical system.
    Each surface actor can be accessed from :py:attr:`actors` attribute after a :py:meth:`update` call.

    Parameters
    ----------
    optical_system : OpticalSystem or IACT
        Optical sistem for which visualize surfaces.
    resolution : float, optional
            Objects mesh resolution (in mm). By default 10 mm.

    Notes
    -----
    If you perform some operation on an actor, make sure to call :py:meth:`start_render` with ``update=False``, otherwise the actors will be replaced.
    
    """
    def __init__(self, optical_system, resolution=10):
        self.actors = {}
        """Dictionary of surface name: surface actor."""

        if issubclass(type(optical_system), OpticalSystem):
            self.os = optical_system
            self._rotation_matrix = np.eye(3)
            self._translation_vector = np.zeros(3)
        elif issubclass(type(optical_system), IACT):
            self.os = optical_system.optical_system
            self._rotation_matrix = local_to_telescope_rotation(*optical_system.pointing)
            self._translation_vector = optical_system.position
        else:
            raise(ValueError("optical system must be an instance of OpticalSystem or IACT."))

        """Optical system to be visualized."""
        
        self._default_surface_color = (0.7, 0.7, 0.75)

        self.surface_type_colors = {
            SurfaceType.REFRACTIVE: (0.6, 0.4, 1),
            SurfaceType.OPAQUE: (1, 0.3, 0.3)
        }
        """Dictionary to custumize surface colors based on surface type."""

        # Wireframe
        self.wireframe = False
        """Whether to use wireframe representation by default."""

        # Window size
        self.window_size = (1024,1024)
        """Window size in pixel."""

        self._resolution = resolution # mm
        """Objects mesh resolution (in mm)."""

        self._update()

        self._apply_global_transform()
    
    def _update(self):
        """Generate all surface actors.
        """
        self.actors = {}
        for s in self.os:
            if s._shape == SurfaceShape.ASPHERICAL:
                
                actor = create_aspheric_surface_actor(s, self._resolution)
            else:
                actor = create_cylindric_surface_actor(s, self._resolution)

            transform = vtk.vtkTransform()
            transform.Translate(*s.position)
            R = s.get_rotation_matrix()
            vtk_rotation_matrix = vtk.vtkMatrix4x4()
            for i in range(3):
                for j in range(3):
                    vtk_rotation_matrix.SetElement(i, j, R[j, i])
            transform.PreMultiply()
            transform.Concatenate(vtk_rotation_matrix)
            transform.Update()
            actor.SetUserTransform(transform)
            
            if self.wireframe:
                actor.GetProperty().SetRepresentationToWireframe()
            
            if s.type in self.surface_type_colors:
                color = self.surface_type_colors[s.type]
            else:
                color = self._default_surface_color

            actor.GetProperty().SetColor(*color)
            actor.GetProperty().SetAmbient(0.3)
            actor.GetProperty().SetDiffuse(0.5)
            actor.GetProperty().SetSpecular(0.2)
            actor.GetProperty().SetSpecularPower(10)
        
            self.actors[s.name] = actor
    
    def start_render(self, camera_position=None, focal_point=None, view_up=(0, 0, 1), orthographic=False):
        """Render the optical system geometry on a VTK window.

        Parameters
        ----------
        camera_position : tuple or list, optional
            (x, y, z) coordinates for the camera position.
        focal_point : tuple, list, or str, optional
            If tuple/list: (x, y, z) coordinates to look at.
            If str: The name of the surface in self.os to look at.
            If None: Defaults to center of system.
        view_up : tuple or list, optional
            (x, y, z) vector defining the "up" direction. Default is (0, 0, 1).
        orthographic : bool, optional
            If True, start with a parallel projection. 
            If False, start with a perspective projection. Default is False.
        """
        # Rendering
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(0.1, 0.15, 0.25)

        inf = float('inf')
        sys_bounds = [inf, -inf, inf, -inf, inf, -inf]
        has_system_actors = False

        for name, actor in self.actors.items():
            renderer.AddActor(actor)
            
            # Include this actor in the bounds calculation
            if not name.startswith("rays"):
                has_system_actors = True
                b = actor.GetBounds() # (xmin, xmax, ymin, ymax, zmin, zmax)
                sys_bounds[0] = min(sys_bounds[0], b[0])
                sys_bounds[1] = max(sys_bounds[1], b[1])
                sys_bounds[2] = min(sys_bounds[2], b[2])
                sys_bounds[3] = max(sys_bounds[3], b[3])
                sys_bounds[4] = min(sys_bounds[4], b[4])
                sys_bounds[5] = max(sys_bounds[5], b[5])

        # Display instructions
        desc = [
            "Press: 'q' to exit",
            "Press: 'r' to reset the camera zoom",
            "Press: 'o' to toggle orthographic/perspective view",
            "Press: 'l' to select/deselect actor under cursor",
            "Press: 'c' to move the focal point on selected actors",
            "Press: 'h' to hide the selected actors", 
            "Press: 'i' to isolate selected actors (and hide others)",
            "Press: 'Esc' to clear selection and actions",
            "Press: 'x', 'y' or 'z' to align the up-vector to the desired axis",
            "Press: 'w', 's' or 'p' to switch to wireframe, surface or points representation",
        ]
        textActor = vtk.vtkTextActor()
        textActor.SetInput('\n'.join(desc))
        position_coordinate = textActor.GetPositionCoordinate()
        position_coordinate.SetCoordinateSystemToNormalizedViewport()
        position_coordinate.SetValue(0.01, 0.99)
        textActor.GetTextProperty().SetJustificationToLeft()
        textActor.GetTextProperty().SetVerticalJustificationToTop()
        textActor.GetTextProperty().SetFontSize(18)
        textActor.GetTextProperty().SetColor(vtk.vtkNamedColors().GetColor3d("Gold"))
        textActor.GetTextProperty().SetFontFamily(vtk.VTK_COURIER)
        textActor.SetVisibility(False)
        renderer.AddActor2D(textActor)

        hintActor = vtk.vtkTextActor()
        hintActor.SetInput("Press '?' for instructions")
        hprop = hintActor.GetTextProperty()
        hprop.SetFontSize(16)
        hprop.SetColor(vtk.vtkNamedColors().GetColor3d("Gold"))
        hprop.SetFontFamily(vtk.VTK_COURIER)
        hprop.SetJustificationToLeft()
        hprop.SetVerticalJustificationToTop()
        hcoord = hintActor.GetPositionCoordinate()
        hcoord.SetCoordinateSystemToNormalizedViewport()
        hcoord.SetValue(0.01, 0.99)
        hintActor.SetVisibility(True)
        renderer.AddActor2D(hintActor)

        render_window = vtk.vtkRenderWindow()
        render_window.SetWindowName(self.os.name)
        render_window.AddRenderer(renderer)
        render_window.SetSize(*self.window_size)
        render_window_interactor = vtk.vtkRenderWindowInteractor()
        render_window_interactor.SetRenderWindow(render_window)

        # Camera
        cam_style = vtk.vtkInteractorStyleTrackballCamera()
        render_window_interactor.SetInteractorStyle(cam_style)

        # Axes
        axes = vtk.vtkAxesActor()
        widget = vtk.vtkOrientationMarkerWidget()
        rgba = [0] * 4
        vtk.vtkNamedColors().GetColor('Carrot', rgba)
        widget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
        widget.SetOrientationMarker(axes)
        widget.SetInteractor(render_window_interactor)
        widget.SetEnabled(1)
        widget.InteractiveOn()

        selected_actors = {}
        is_isolated = False
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)

        def perform_view_reset(up_vector):
            active_camera = renderer.GetActiveCamera()
            if not active_camera:
                return

            # Normalize up_vector
            norm_up = np.sqrt(sum(x*x for x in up_vector))
            if norm_up == 0: return
            target_up = [x/norm_up for x in up_vector]

            # Get current view plane normal
            vpn = active_camera.GetViewPlaneNormal()
            
            # Compute dot product
            dot = sum(vpn[i] * target_up[i] for i in range(3))
            
            # If dot product is near 1 or -1, vectors are parallel.
            if abs(dot) > 0.95:
                fp = active_camera.GetFocalPoint()
                dist = active_camera.GetDistance()
                
                # Move camera to a perpendicular axis based on target UP
                if abs(target_up[2]) > 0.9: 
                    active_camera.SetPosition(fp[0], fp[1] - dist, fp[2])
                elif abs(target_up[1]) > 0.9:
                    active_camera.SetPosition(fp[0] - dist, fp[1], fp[2])
                else:
                    active_camera.SetPosition(fp[0], fp[1], fp[2] + dist)

                if has_system_actors:
                    renderer.ResetCamera(sys_bounds)
                else:
                    renderer.ResetCamera()

            active_camera.SetViewUp(*up_vector)
            active_camera.OrthogonalizeViewUp() 
            render_window.Render()

        def key_press_callback(caller, event):
            interactor = caller
            key_sym = interactor.GetKeySym()
            
            if key_sym is None:
                return
            
            # Reset view ('r')
            if key_sym.lower() == 'r':
                if has_system_actors:
                    renderer.ResetCamera(sys_bounds)
                else:
                    renderer.ResetCamera()
                render_window.Render()
                interactor.SetKeySym("") 
                interactor.SetKeyCode("\0")
            
            # Instructions ('?')
            elif key_sym.lower() == 'question':
                current_vis = textActor.GetVisibility()
                # Toggle: If currently visible, make invisible.
                textActor.SetVisibility(not current_vis)
                # Hint is always the opposite of Instructions
                hintActor.SetVisibility(current_vis)
                render_window.Render()

            # Orthographic/perspective ('o')
            elif key_sym.lower() == 'o':
                cam = renderer.GetActiveCamera()
                if cam.GetParallelProjection():
                    # Switching Parallel -> Perspective
                    scale = cam.GetParallelScale()
                    fov = cam.GetViewAngle()
                    if fov > 0:
                        target_dist = scale / np.tan(np.deg2rad(fov) / 2.0)
                        fp = np.array(cam.GetFocalPoint())
                        pos = np.array(cam.GetPosition())
                        direction = fp - pos
                        dist_mag = np.linalg.norm(direction)
                        if dist_mag > 0:
                            direction_norm = direction / dist_mag
                            cam.SetPosition(fp - direction_norm * target_dist)
                    cam.SetParallelProjection(False)
                else:
                    # Switching Perspective -> Parallel
                    dist = cam.GetDistance()
                    fov = cam.GetViewAngle()
                    new_scale = dist * np.tan(np.deg2rad(fov) / 2.0)
                    cam.SetParallelScale(new_scale)
                    cam.SetParallelProjection(True)
                
                renderer.ResetCameraClippingRange()
                render_window.Render()
            
            # Selection ('l')
            elif key_sym.lower() == 'l':
                click_pos = interactor.GetEventPosition()
                picker.Pick(click_pos[0], click_pos[1], 0, renderer)
                picked_actor = picker.GetActor()
                if picked_actor:
                    if picked_actor in selected_actors:
                        # Deselect
                        original_color = selected_actors.pop(picked_actor)
                        picked_actor.GetProperty().SetColor(*original_color)
                    else:
                        # Select
                        current_color = picked_actor.GetProperty().GetColor()
                        selected_actors[picked_actor] = current_color
                        picked_actor.GetProperty().SetColor(0.0, 1.0, 0.0) # Green
                render_window.Render()
            
            # Center ('c')
            elif key_sym.lower() == 'c':
                if selected_actors:
                    # Calculate center of all selected actors
                    sel_bounds = [inf, -inf, inf, -inf, inf, -inf]
                    for actor in selected_actors:
                        b = actor.GetBounds()
                        sel_bounds[0] = min(sel_bounds[0], b[0])
                        sel_bounds[1] = max(sel_bounds[1], b[1])
                        sel_bounds[2] = min(sel_bounds[2], b[2])
                        sel_bounds[3] = max(sel_bounds[3], b[3])
                        sel_bounds[4] = min(sel_bounds[4], b[4])
                        sel_bounds[5] = max(sel_bounds[5], b[5])
                    
                    center_x = (sel_bounds[0] + sel_bounds[1]) / 2.0
                    center_y = (sel_bounds[2] + sel_bounds[3]) / 2.0
                    center_z = (sel_bounds[4] + sel_bounds[5]) / 2.0
                    
                    # Move Focal Point
                    renderer.GetActiveCamera().SetFocalPoint(center_x, center_y, center_z)
                    renderer.ResetCameraClippingRange()
                    render_window.Render()

            # Hide selected ('h')
            elif key_sym.lower() == 'h':
                for actor in list(selected_actors.keys()):
                    original_color = selected_actors.pop(actor)
                    actor.GetProperty().SetColor(*original_color)
                    actor.SetVisibility(False)
                render_window.Render()

            # Isolate selected ('i')
            elif key_sym.lower() == 'i':
                nonlocal is_isolated
                
                # If we have a selection, Isolate it and then Deselect
                if selected_actors:
                    is_isolated = True
                    # Hide everything not in selection
                    for name, actor in self.actors.items():
                        # Always keep rays visible
                        if "rays_" in name:
                            actor.SetVisibility(True)
                            continue
                        
                        if actor in selected_actors:
                            actor.SetVisibility(True)
                            # Restore color immediately
                            orig_col = selected_actors[actor]
                            actor.GetProperty().SetColor(*orig_col)
                        else:
                            actor.SetVisibility(False)
                    
                    # Clear selection since we are now in "Isolation Mode" with no active targets
                    selected_actors.clear()
                    
                # If nothing selected, 'h' acts as "Show All" if currently isolated
                elif is_isolated:
                    is_isolated = False
                    for actor in self.actors.values():
                        actor.SetVisibility(True)
                
                render_window.Render()

                # Consume the key, otherwise the axes will disappear (IDKW)
                interactor.SetKeySym("") 
                interactor.SetKeyCode("\0")

            # Clear selections ('Escape')
            elif key_sym == 'Escape':
                is_isolated = False
                # Restore colors of selected
                for actor, color in selected_actors.items():
                    actor.GetProperty().SetColor(*color)
                selected_actors.clear()
                # Ensure everything is visible
                for actor in self.actors.values():
                    actor.SetVisibility(True)
                render_window.Render()

            # Axes and modes
            elif key_sym.lower() == 'y':
                perform_view_reset((0,1,0))
            elif key_sym.lower() == 'x':
                perform_view_reset((1,0,0))
            elif key_sym.lower() == 'z':
                perform_view_reset((0,0,1))
            elif key_sym.lower() == 'w':
                for actor in renderer.GetActors():
                    actor.GetProperty().SetRepresentationToWireframe()
                render_window.Render()
            elif key_sym.lower() == 's':
                for actor in renderer.GetActors():
                    actor.GetProperty().SetRepresentationToSurface()
                render_window.Render()
            elif key_sym.lower() == 'p':
                for actor in renderer.GetActors():
                    actor.GetProperty().SetRepresentationToPoints()
                render_window.Render()
            elif key_sym.lower() == 'q':
                    quit(render_window_interactor)

        priority = 1.0
        render_window_interactor.AddObserver(vtk.vtkCommand.CharEvent, key_press_callback, priority)

        # Start
        render_window.Render()
        
        # Camera configuration
        cam = renderer.GetActiveCamera()
        
        # Apply initial projection type
        cam.SetParallelProjection(orthographic)

        if camera_position is not None:
            cam.SetPosition(*camera_position)
            cam.SetViewUp(*view_up)
            
            if focal_point is not None:
                if isinstance(focal_point, str):
                    fp = self.os[focal_point].position
                    if self._rotation_matrix is not None:
                        fp = fp @ self._rotation_matrix.T + self._translation_vector
                    cam.SetFocalPoint(*fp)
                else:
                    cam.SetFocalPoint(*focal_point)
            elif has_system_actors:
                cx = (sys_bounds[0] + sys_bounds[1]) / 2.0
                cy = (sys_bounds[2] + sys_bounds[3]) / 2.0
                cz = (sys_bounds[4] + sys_bounds[5]) / 2.0
                cam.SetFocalPoint(cx, cy, cz)
            else:
                cam.SetFocalPoint(0, 0, 0)
            
            renderer.ResetCameraClippingRange()
        else:
            if has_system_actors:
                renderer.ResetCamera(sys_bounds)
            else:
                renderer.ResetCamera()
        
        # Increase far clip plane
        rng = cam.GetClippingRange()
        cam.SetClippingRange(rng[0], rng[1] * 1000) 

        render_window.Render()
        render_window_interactor.Initialize()
        render_window_interactor.Start()

        # Stop
        quit(render_window_interactor)

    def add_rays(self, start, stop, directions=None, length=None, opacity=0.5, point_size=1.0, show_rays=True, show_hits=True):
        """
        Draw rays from start to stop positions and highlight stop points.
        
        If a stop position is NaN (indicating a miss), the ray is skipped by default.
        If 'length' and 'directions' are provided, rays with NaN stops are drawn 
        starting from 'start' along 'direction' for 'length' units (without a hit dot).
        
        Parameters
        ----------
        start : ndarray
            (n, 3) array of starting coordinates (x, y, z).
        stop : ndarray
            (n, 3) array of stopping coordinates (x, y, z).
        directions : ndarray, optional
            (n, 3) array of direction vectors. Required if plotting NaN rays with fixed length.
        length : float, optional
            If provided, rays with NaN stop will be drawn with this length using the direction vector.
        opacity : float, optional
            Transparency of the rays from 0.0 (invisible) to 1.0 (opaque). Default is 0.5.
        point_size : float, optional
            Size of the hit points. Default is 1.0
        show_rays : bool, optional
            Whether to show rays or not. Default is True.
        show_hits : bool, optional
            Whether to show hits or not. Default is True.
        """

        if not show_hits and not show_rays:
            return
        
        # Rays
        points_rays = vtk.vtkPoints()
        lines_rays = vtk.vtkCellArray()
        
        # Hits
        points_dots = vtk.vtkPoints()
        verts_dots = vtk.vtkCellArray()
        
        n = start.shape[0]
        has_directions = directions is not None

        if start.shape != stop.shape or (has_directions and start.shape != directions.shape):
            raise ValueError("Start,  stop and directions must have the same shape.")

        # Check which rays have intersected a surface
        valid_stops = ~np.any(np.isnan(stop), axis=1)
        
        for i in range(n):
            current_start = start[i]
            current_stop = stop[i]
            
            is_valid_stop = valid_stops[i]
            
            final_stop = None
            draw_hit = False
            if is_valid_stop:
                # Draw from start to stop and add a hit
                final_stop = current_stop
                draw_hit = True
            elif length is not None and has_directions:
                # Draw fixed length ray if directions are available
                final_stop = current_start + directions[i] * length
                draw_hit = False
            else:
                # Ignore not intersected ray
                continue

            ## Ray logic
            id_start = points_rays.InsertNextPoint(current_start)
            id_stop_line = points_rays.InsertNextPoint(final_stop)
            
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, id_start)
            line.GetPointIds().SetId(1, id_stop_line)
            lines_rays.InsertNextCell(line)
            
            ## Hit logic
            if draw_hit:
                id_stop_dot = points_dots.InsertNextPoint(final_stop)
                verts_dots.InsertNextCell(1)
                verts_dots.InsertCellPoint(id_stop_dot)
            
        ## Rays actor
        if show_rays:
            raysPolyData = vtk.vtkPolyData()
            raysPolyData.SetPoints(points_rays)
            raysPolyData.SetLines(lines_rays)
            
            mapper_rays = vtk.vtkPolyDataMapper()
            mapper_rays.SetInputData(raysPolyData)
            
            actor_rays = vtk.vtkActor()
            actor_rays.SetMapper(mapper_rays)
            
            actor_rays.GetProperty().SetColor(0.0, 0.7, 1.0) # Electric blue
            actor_rays.GetProperty().SetLineWidth(1.0)
            actor_rays.GetProperty().SetOpacity(float(opacity))
            
            # Make rays unpickable
            actor_rays.PickableOff()

            base_key = 'rays_lines'
            key = base_key
            count = 0
            while key in self.actors:
                key = f"{base_key}_{count}"
                count += 1
            
            self.actors[key] = actor_rays

        ## Hits actor
        if points_dots.GetNumberOfPoints() > 0 and show_hits:
            dotsPolyData = vtk.vtkPolyData()
            dotsPolyData.SetPoints(points_dots)
            dotsPolyData.SetVerts(verts_dots)
            
            mapper_dots = vtk.vtkPolyDataMapper()
            mapper_dots.SetInputData(dotsPolyData)
            
            actor_dots = vtk.vtkActor()
            actor_dots.SetMapper(mapper_dots)
            actor_dots.GetProperty().SetColor(1.0, 1.0, 0.0) # Yellow
            
            actor_dots.GetProperty().SetPointSize(point_size) 
            actor_dots.GetProperty().SetOpacity(1.0)
            
            # Make dots unpickable
            actor_dots.PickableOff()

            base_key = 'rays_dots'
            key = base_key
            count = 0
            while key in self.actors:
                key = f"{base_key}_{count}"
                count += 1
                
            self.actors[key] = actor_dots

    def _apply_global_transform(self):
        """
        Apply a global rotation and translation to all current actors.
        
        Parameters
        ----------
        R : ndarray
            (3, 3) Rotation matrix. 
        t : ndarray or list
            (3,) Translation vector (x, y, z).
        """
        # Convert numpy array to vtkMatrix4x4
        vtk_R = vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                vtk_R.SetElement(i, j, self._rotation_matrix[i, j])

        # Iterate over all actors
        for actor in self.actors.values():
            
            # Get the existing transform
            transform = actor.GetUserTransform()
            if transform is None:
                transform = vtk.vtkTransform()
                transform.SetMatrix(actor.GetMatrix())
                actor.SetUserTransform(transform)
            
            # Apply transformations
            # PostMultiply ensures we are applying this to the "Global" world coordinates
            transform.PostMultiply()
            
            # Apply rotation
            transform.Concatenate(vtk_R)
            
            # Apply translation
            transform.Translate(*self._translation_vector)