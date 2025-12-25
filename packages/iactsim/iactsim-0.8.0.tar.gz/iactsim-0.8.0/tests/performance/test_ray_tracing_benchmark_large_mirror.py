import pytest
import cupy as cp
import iactsim
import numpy as np

@pytest.fixture(scope="module")
def telescope_setup():
    """Initializes the telescope and GPU context."""
    # Spherical mirror
    mirror_curvature_radius = 20000
    plate_scale = mirror_curvature_radius/57.296/2.
    mirror = iactsim.optics.SphericalSurface(
        half_aperture=10000., 
        curvature=1./mirror_curvature_radius,
        position=(0,0,0),
        surface_type=iactsim.optics.SurfaceType.REFLECTIVE_OUT,
        name = 'Mirror'
    )

    # Flat focal surface (5deg hexagon)
    focal_plane = iactsim.optics.FlatSurface(
        half_aperture = 5*plate_scale, 
        position = (0,0,0.5*mirror_curvature_radius),
        aperture_shape = iactsim.optics.ApertureShape.HEXAGONAL,
        surface_type=iactsim.optics.SurfaceType.SENSITIVE_IN,
        name = 'Focal Plane'
    )

    # List of segments
    segments = []

    # Segment ID
    k = 0

    # Segments on a nXn grid, 80 total
    n = 20

    segment_distance = 2*mirror.half_aperture / (n+3)

    for i in range(n+3):
        for j in range(n+3):
            offset = [-mirror.half_aperture+segment_distance*i, -mirror.half_aperture+segment_distance*j]
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
                aperture_shape=iactsim.optics.ApertureShape.SQUARE,
                tilt_angles=np.random.normal(0,0.05,3),
                scattering_dispersion=0.01
            )
            
            segment.offset = offset
            
            segments.append(segment)
            k += 1
    
    segmented_os = iactsim.optics.OpticalSystem(surfaces=[focal_plane, *segments], name='SEGMENTED-TEST-OS')
    pos = (0,0,0)
    poi = (0.,0.)
    telescope = iactsim.IACT(segmented_os, position=pos, pointing=poi)
    telescope.cuda_init()

    return telescope

def test_ray_tracing_performance_large_mirror(benchmark, telescope_setup):

    def setup_round_on_axis():
        telescope = telescope_setup
        source = iactsim.optics.sources.Source(telescope)
        source.positions.radial_uniformity = False
        source.positions.random = True
        source.positions.r_max = 11000
        source.set_target(distance=11000)
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})

    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()

    benchmark.pedantic(run_trace, setup=setup_round_on_axis, rounds=100, iterations=1)

def test_ray_tracing_performance_large_mirror_off_axis(benchmark, telescope_setup):
    
    def setup_round_off_axis():
        telescope = telescope_setup
        source = iactsim.optics.sources.Source(telescope)
        source.positions.radial_uniformity = False
        source.positions.random = True
        source.positions.r_max = 11000
        source.directions.altitude += 1
        source.set_target(distance=11000)
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})

    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()

    benchmark.pedantic(run_trace, setup=setup_round_off_axis, rounds=100, iterations=1)