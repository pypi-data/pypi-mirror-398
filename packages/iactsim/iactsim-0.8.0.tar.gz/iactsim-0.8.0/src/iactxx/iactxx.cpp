// Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
// SPDX-License-Identifier: GPL-3.0-or-later
//
// This file is part of iactsim.
//
// iactsim is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// iactsim is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

#include <string>

// Pybind11
#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // Automatic vector conversion into a list
#include <pybind11/numpy.h>

// Local headers
#include <arrays_ops.h>
#include <IACTFile.h>

namespace py = pybind11;

using BunchPosition = iactxx::eventio::BunchPosition<iactxx::eventio::f32>;
using BunchDirection = iactxx::eventio::BunchDirection<iactxx::eventio::f32>;
using TelescopeDefinition = iactxx::eventio::TelescopeDefinition<iactxx::eventio::f32>;
using EventHeader = iactxx::eventio::EventHeader;

namespace iactxx {

inline static IACTFile read_file(
    const std::string& filepath,
    const std::vector<int> telescopes_to_skip,
    int min_n_bunches
) 
{
    IACTFile cfile;
    cfile.setTelescopesToSkip(telescopes_to_skip);
    cfile.setMinimumNumberOfBunches(min_n_bunches);
    cfile.setFilePath(filepath);
    cfile.parseBunches();
    cfile.convertBunches();
    return cfile;
}

inline static std::vector<IACTFile> read_files(
    const std::vector<std::string>& filepaths,
    const std::vector<int> telescopes_to_skip,
    int min_n_bunches
) 
{
    size_t n_files = filepaths.size();

    std::vector<IACTFile> cfiles;
    cfiles.resize(n_files);

    // default(none) has been removed in order to use std::cerr
    // shared(cfiles, filepaths, telescopes_to_skip) is implicit
    #pragma omp parallel for firstprivate(n_files, min_n_bunches) 
    for (size_t file_id=0; file_id<n_files; ++file_id)
    {
        try {
            IACTFile cfile;
            cfile.setTelescopesToSkip(telescopes_to_skip);
            cfile.setMinimumNumberOfBunches(min_n_bunches);
            cfile.setFilePath(filepaths[file_id]);
            cfile.parseBunches();
            cfile.convertBunches();
            cfiles[file_id] = std::move(cfile);
        }
        catch (const std::exception& e) { 
            #pragma omp critical (ErrorLogging)
            {
                std::cerr << "Thread " << omp_get_thread_num() 
                          << ": Exception during processing of file '" << filepaths[file_id]
                          << "':\n\t" << e.what() << std::endl;
            }
        } 
        catch (...) { 
            #pragma omp critical (ErrorLogging)
            {
                std::cerr << "Thread " << omp_get_thread_num() 
                          << ": Unknown exception during processing of file '" << filepaths[file_id]<< "'" << std::endl;
            }
        }
    }
    
    return cfiles;
}

namespace pybind
{

/**
 * @brief Create a float 3D array numpy view.
 * 
 * @tparam T Array type
 * @param ptr Array pointer
 * @param count Number of elements
 * @param owner Python object owning the memory
 * @return py::array 
 */
template <typename T>
inline py::array create_vec3f_numpy_view(
    const T* ptr,
    size_t count,
    py::object owner
) 
{
    // Check if T has a standard layout
    static_assert(
        std::is_standard_layout<T>::value,
        "Template type T must have standard layout for reliable striding."
    );

    // Handle empty/null case -> return an empty NumPy array (copy, has no owner)
    if (!ptr || count == 0) {
        std::vector<ssize_t> empty_shape = {0, 3};
        return py::array(py::dtype("f4"), empty_shape);
    }

    // Define shape and strides based on T
    std::vector<ssize_t> shape = {(ssize_t)count, 3}; // N rows, 3 columns
    std::vector<ssize_t> strides = {
        (ssize_t)sizeof(T), // Bytes to stride to get to the next T
        (ssize_t)sizeof(float) // Bytes to stride to get to the next float within T
    };

    // Create the view
    return py::array(
        py::dtype("f4"),
        shape,
        strides,
        ptr, // Pointer to the start of the first struct T
        owner // Python object owning the memory
    );
}

template <typename T>
inline py::array create_numpy_view(
    const T* ptr,
    size_t count,
    py::object owner
)
{
    const std::string format = py::format_descriptor<T>::format();
    const py::dtype dtype = py::dtype(format);

    if (!ptr || count == 0) {
        std::vector<py::ssize_t> empty_shape = {0};
        return py::array(dtype, empty_shape);
    }

    // Define shape and strides for the 1D view
    std::vector<py::ssize_t> shape = {(py::ssize_t)count};

    // Stride is the size of one element of type T
    std::vector<py::ssize_t> strides = {(py::ssize_t)sizeof(T)};

    // Create the view
    return py::array(
        dtype,   // Deduced NumPy data type
        shape,   // Shape of the array (1D)
        strides, // Strides for the array
        ptr,     // Pointer to the first element
        owner    // Python object owning the memory
    );
}

template <typename T>
py::array_t<T> add_numpy_arrays(
    py::array_t<T, py::array::c_style> arr1,
    py::array_t<T, py::array::c_style> arr2)
{
    // Request buffer information from the input arrays
    py::buffer_info buf1 = arr1.request();
    py::buffer_info buf2 = arr2.request();

    // Check if arrays have the same size in the first dimension
    if (buf1.shape.size() == 0 || buf2.shape.size() == 0 || buf1.shape[0] != buf2.shape[0]) {
         throw std::runtime_error("Input arrays must have the same size in the first dimension");
    }

    // Check for shape compatibility
    if (buf1.ndim > 1) {
        for(py::ssize_t i = 1; i < buf1.ndim; ++i) {
            if (buf1.shape[i] != buf2.shape[i]) {
                 throw std::runtime_error("Input arrays must have the same shape");
            }
        }
    }

    // Get the total number of elements
    size_t size = buf1.size;

    // Empty array case
    if (size == 0) {
        return py::array_t<T>(buf1.shape);
    }
    if (buf1.size != buf2.size) {
         throw std::runtime_error("Input arrays must have the same total number of elements");
    }

    // Create the result NumPy array with the same shape as the inputs
    py::array_t<T> result = py::array_t<T>(buf1.shape);
    py::buffer_info buf_result = result.request();

    // Get raw pointers to the buffer data
    T* ptr1 = static_cast<T*>(buf1.ptr);
    T* ptr2 = static_cast<T*>(buf2.ptr);
    T* ptr_result = static_cast<T*>(buf_result.ptr);

    iactxx::math::add(ptr1, ptr2, ptr_result, size);
    
    // Return the result array
    return result;
}

template <typename T>
void axpy_numpy_arrays(
    T scalar, // pybind will cast the scalar
    py::array_t<T, py::array::c_style> arr1,
    py::array_t<T, py::array::c_style> arr2)
{
    // Request buffer information from the input arrays
    py::buffer_info buf1 = arr1.request();
    py::buffer_info buf2 = arr2.request();

    // Check if arrays have the same size in the first dimension
    if (buf1.shape.size() == 0 || buf2.shape.size() == 0 || buf1.shape[0] != buf2.shape[0]) {
         throw std::runtime_error("Input arrays must have the same size in the first dimension");
    }

    // Check for shape compatibility
    if (buf1.ndim > 1) {
        for(py::ssize_t i = 1; i < buf1.ndim; ++i) {
            if (buf1.shape[i] != buf2.shape[i]) {
                 throw std::runtime_error("Input arrays must have the same shape");
            }
        }
    }

    // Get the total number of elements
    size_t size = buf1.size;

    // Empty array case
    if (size == 0) {
        return;
    }
    if (buf1.size != buf2.size) {
         throw std::runtime_error("Input arrays must have the same total number of elements");
    }

    // Get raw pointers to the buffer data
    T* ptr1 = static_cast<T*>(buf1.ptr);
    T* ptr2 = static_cast<T*>(buf2.ptr);

    iactxx::math::axpy(scalar, ptr1, ptr2, size);
    
    return;
}

} // namespace iactxx::pybind

} // namespace iactxx

template<typename... Ts>
void define_add_overloads(py::module_& m) {
    (
        m.def(
            "add",
            &iactxx::pybind::add_numpy_arrays<Ts>,
            "Adds two NumPy arrays element-wise.",
            py::arg("arr1").noconvert(),
            py::arg("arr2").noconvert()
        ),
        ...
    );
}

template<typename... Ts>
void define_axpy_overloads(py::module_& m) {
    (
        m.def(
            "axpy",
            &iactxx::pybind::axpy_numpy_arrays<Ts>,
            "Adds two NumPy arrays element-wise.",
            py::arg("scalar"),
            py::arg("arr1").noconvert(),
            py::arg("arr2").noconvert()
        ),
        ...
    );
}

// Define the Python module 'iactxx'
PYBIND11_MODULE(iactxx, m) {
    m.doc() = "pybind11 extension module for iactsim";

    /////////////////////////////////////////////////////
    //
    // math example submodule
    //
    /////////////////////////////////////////////////////

    // Create a submodule attached to 'm'
    py::module_ math_submodule = m.def_submodule(
        "math", // Python name of the submodule
        "Example submodule for basic math operations" // Docstring for the submodule
    );

    define_add_overloads
    <
    uint8_t, int8_t, uint16_t, int16_t,
    uint32_t, int32_t, uint64_t, int64_t,
    float, double
    >(math_submodule);

    define_axpy_overloads
    <
    uint8_t, int8_t, uint16_t, int16_t,
    uint32_t, int32_t, uint64_t, int64_t,
    float, double
    >(math_submodule);

    /////////////////////////////////////////////////////
    //
    // io submodule
    //
    /////////////////////////////////////////////////////
    PYBIND11_NUMPY_DTYPE(
        EventHeader,
        event_header,
        event_number,
        particle_id,
        total_energy,
        starting_altitude,
        first_target_id,
        first_interaction_height,
        momentum_x,
        momentum_y,
        momentum_minus_z,
        zenith,
        azimuth,
        n_random_sequences,
        random_seeds,
        run_number,
        date,
        version,
        n_observation_levels,
        observation_height,
        energy_spectrum_slope,
        energy_min,
        energy_max,
        energy_cutoff_hadrons,
        energy_cutoff_muons,
        energy_cutoff_electrons,
        energy_cutoff_photons,
        nflain,
        nfdif,
        nflpi0,
        nflpif,
        nflche,
        nfragm,
        earth_magnetic_field_x,
        earth_magnetic_field_z,
        egs4_flag,
        nkg_flag,
        low_energy_hadron_model,
        high_energy_hadron_model,
        cerenkov_flag,
        neutrino_flag,
        curved_flag,
        computer,
        theta_min,
        theta_max,
        phi_min,
        phi_max,
        cherenkov_bunch_size,
        n_cherenkov_detectors_x,
        n_cherenkov_detectors_y,
        cherenkov_detector_grid_spacing_x,
        cherenkov_detector_grid_spacing_y,
        cherenkov_detector_length_x,
        cherenkov_detector_length_y,
        cherenkov_output_flag,
        angle_array_x_magnetic_north,
        additional_muon_information_flag,
        egs4_multpliple_scattering_step_length_factor,
        cherenkov_wavelength_min,
        cherenkov_wavelength_max,
        n_reuse,
        reuse_x,
        reuse_y,
        sybill_interaction_flag,
        sybill_cross_section_flag,
        qgsjet_interaction_flag,
        qgsjet_cross_section_flag,
        dpmjet_interaction_flag,
        dpmjet_cross_section_flag,
        venus_nexus_epos_cross_section_flag,
        muon_multiple_scattering_flag,
        nkg_radial_distribution_range,
        energy_fraction_if_thinning_level_hadronic,
        energy_fraction_if_thinning_level_em,
        actual_weight_limit_thinning_hadronic,
        actual_weight_limit_thinning_em,
        max_radius_radial_thinning_cutting,
        viewcone_inner_angle,
        viewcone_outer_angle,
        transition_energy_low_high_energy_model,
        skimming_incidence_flag,
        horizontal_shower_exis_altitude,
        starting_height,
        explicit_charm_generation_flag,
        electromagnetic_subshower_hadronic_origin_output_flag,
        conex_min_vertical_depth,
        conex_high_energy_treshold_hadrons,
        conex_high_energy_treshold_muons,
        conex_high_energy_treshold_em,
        conex_low_energy_treshold_hadrons,
        conex_low_energy_treshold_muons,
        conex_low_energy_treshold_em,
        observaton_level_curvature_flag,
        conex_weight_limit_thinning_hadronic,
        conex_weight_limit_thinning_em,
        conex_weight_limit_sampling_hadronic,
        conex_weight_limit_sampling_muons,
        conex_weight_limit_sampling_em,
        augerhit_stripes_half_width,
        augerhit_detector_distance,
        augerhit_reserved,
        n_multithin,
        multithin_energy_fraction_hadronic,
        multithin_weight_limit_hadronic,
        multithin_energy_fraction_em,
        multithin_weight_limit_em,
        multithin_random_seeds,
        icecube_energy_threshold,
        icecube_gzip_flag,
        icecube_pipe_flag
    );

    // Create a submodule attached to 'm'
    py::module_ io_submodule = m.def_submodule(
        "io",
        "Submodule for io operations"
    );

    py::class_<TelescopeDefinition>
    (
        io_submodule,
        "TelescopeDefinition",
        "Represents a telescope definition with x, y, z coordinates and reference sphere radius r.",
        py::module_local()
    )    
        .def(py::init<>())
        .def_readwrite("x", &TelescopeDefinition::x, "X coordinate")
        .def_readwrite("y", &TelescopeDefinition::y, "Y coordinate")
        .def_readwrite("z", &TelescopeDefinition::z, "Z coordinate")
        .def_readwrite("r", &TelescopeDefinition::r, "Radius")
        .def("__repr__",
            [](const TelescopeDefinition &td) {
                return "<TelescopeDefinition x=" + std::to_string(td.x) +
                       ", y=" + std::to_string(td.y) +
                       ", z=" + std::to_string(td.z) +
                       ", r=" + std::to_string(td.r) + ">";
            }
        );

    py::class_<iactxx::IACTFile>(
            io_submodule,
            "IACTFile",
            R"raw(
            Class that represents a file produced by CORSIKA IACT extension.
            
            Usage
            -----

            .. code-block:: python

                filepath = "/path/to/corsika/file"
                cfile = iactxx.io.IACTFile()
                # Scan file for memory allocation
                cfile.set_filepath(filepath)
                # Decode photon bunches
                cfile.parse_bunches()
                # Convert photon bunches units into iactsim default units
                cfile.convert_bunches()
            
            Note
            ----
                Only gzip and zstd compressed files are supported.
            
            See Also
            --------
            :py:meth:`get_telescope_bunches`: returns bunches data as a list of NumPy arrays.
            :py:func:`read_corsika_file` : utility function to read, parse and covert bunches from a file.
            :py:func:`read_corsika_files` : utility function to read, parse and covert bunches from multiple files in parallel.

            )raw"
        )
        // Bind the constructor
        .def(py::init<>())

        // Set methods
        .def("set_filepath", py::overload_cast<std::string>(&iactxx::IACTFile::setFilePath), "Link to a file", py::arg("filepath"))
        .def("set_telescopes_to_skip", &iactxx::IACTFile::setTelescopesToSkip, "Set which telescopes can be skipped", py::arg("telescopes"))
        .def("set_minimum_number_of_bunches", &iactxx::IACTFile::setMinimumNumberOfBunches, "Set minimum number of bunches", py::arg("n_bunches"))

        // Read data
        .def("parse_bunches", &iactxx::IACTFile::parseBunches, "Read photon bunches")
        .def("convert_bunches", &iactxx::IACTFile::convertBunches, "Convert photon bunches units")

        // Get meothods
        .def("get_number_of_bunches", 
            [](iactxx::IACTFile& self){
                py::dict n_bunches_per_telescope;
                for (int i=0; i<self.getNumberOfTelescopes(); i++) {
                    const auto n_bunches = self.getTelescopeNumberOfBunches(i);
                    n_bunches_per_telescope[py::int_(i)] = n_bunches;
                }
                return n_bunches_per_telescope;
            },
            "Get number of bunches of all telescopes"
        )
        .def(
            "get_telescope_number_of_bunches",
            &iactxx::IACTFile::getTelescopeNumberOfBunches, 
            "Get number if bunches hitting the telescope with ID `tel_id`",
            py::arg("tel_id")
        )
        .def_property_readonly("input_card", &iactxx::IACTFile::getInputCard, "Get the the CORSIKA input card")
        .def_property_readonly("run_id", &iactxx::IACTFile::getRunID, "Get run ID")
        .def_property_readonly("min_energy", &iactxx::IACTFile::getMinEnergy, "Get minimum energy")
        .def_property_readonly("max_energy", &iactxx::IACTFile::getMaxEnergy, "Get maximum energy")
        .def_property_readonly("energy_slope", &iactxx::IACTFile::getEnergySlope, "Get energy slope")
        .def_property_readonly("particle_id", &iactxx::IACTFile::getParticleID, "Get particle ID")
        .def_property_readonly("view_cone", &iactxx::IACTFile::getViewCone, "Get view cone")
        .def_property_readonly("maximum_impact", &iactxx::IACTFile::getMaximumImpact, "Get maximum impact")
        .def_property_readonly("pointing", &iactxx::IACTFile::getPointing, "Get mean pointing direction")
        .def_property_readonly("bunch_size", &iactxx::IACTFile::getBunchSize, "Get number of photons per bunch")
        .def_property_readonly("lambda_min", &iactxx::IACTFile::getLambdaMin, "Get minimum simulated photon wavelength")
        .def_property_readonly("lambda_max", &iactxx::IACTFile::getLambdaMax, "Get minimum simulated photon wavelength")
        .def_property_readonly("zenith_range", &iactxx::IACTFile::getZenithRange, "Get minimum simulated photon wavelength")
        .def_property_readonly("azimuth_range", &iactxx::IACTFile::getAzimuthRange, "Get minimum simulated photon wavelength")
        .def_property_readonly("azimuth_offset", &iactxx::IACTFile::getAzimuthOffset, "Get azimuth offset w.r.t. CORSIKA reference system (geomagnetic north)")
        .def_property_readonly("number_of_telescopes", &iactxx::IACTFile::getNumberOfTelescopes, "Get number of simulated telescopes")
        .def_property_readonly("filesize", &iactxx::IACTFile::getFileSize, "Get file size (in byte)")
        .def_property_readonly("number_of_events", &iactxx::IACTFile::getNumberOfEvents, "Get total number of events (taking reused into account)")
        .def("get_event_number_of_bunches", &iactxx::IACTFile::getEventNumberOfBunches, "Get number of bunches of each event", py::arg("tel_id"))
        .def("get_telescope_definition", &iactxx::IACTFile::getTelescopeDefinition, "Get telescope definition", py::arg("tel_id"))
        .def("get_from_input_card", &iactxx::IACTFile::getFromInputCard, "Get a keyword from the CORSIKA input card", py::arg("keyword"))
        .def(
            "get_telescope_event_ids",
            [](iactxx::IACTFile &self, int tel_id) -> py::array_t<size_t> {
                const std::vector<size_t>& event_ids_ref = self.getTelescopeEventIDs(tel_id);
                const size_t* ptr = event_ids_ref.data();
                py::object py_self = py::cast(&self, py::return_value_policy::reference);
                py::array event_ids_view = iactxx::pybind::create_numpy_view(ptr, event_ids_ref.size(), py_self);
                return event_ids_view;
            },
            "Get identifier of all events seen by a telescope",
            py::arg("tel_id")
        )
        .def(
            "get_event_headers", 
            [](iactxx::IACTFile &self) -> py::array_t<EventHeader> {
                const std::vector<EventHeader>& events = self.getEventHeaders();
        
                auto result = py::array_t<EventHeader>(events.size());
                eventio::EventHeader* ptr = result.mutable_data();
                std::copy(events.begin(), events.end(), ptr);
        
                return result;
            },
            "Get event header of all simulated events"
        )
        .def(
            "get_telescope_event_headers", 
            [](iactxx::IACTFile &self, int tel_id) -> py::array_t<EventHeader> {
                const std::vector<EventHeader>& events = self.getTelescopeEvents(tel_id);
        
                auto result = py::array_t<EventHeader>(events.size());
                eventio::EventHeader* ptr = result.mutable_data();
                std::copy(events.begin(), events.end(), ptr);
        
                return result;
            },
            "Get event header of all events seen by a telescope",
            py::arg("tel_id")
        )
        .def(
            "get_telescope_bunches",
            [](iactxx::IACTFile &self, int tel_id) -> py::list {
                auto& bunches = self.getTelescopeBunches(tel_id);
                size_t size = bunches.n_bunches;
                const BunchPosition* pos_ptr = bunches.pos.get();
                const BunchDirection* dir_ptr = bunches.dir.get();
                const float* t_ptr = bunches.time.get();
                const float* wl_ptr = bunches.wavelength.get();
                const float* zem_ptr = bunches.zem.get();

                auto& bunches_mapping = self.getTelescopeEventMapping(tel_id);
                auto* map_ptr = bunches_mapping.data();

                // Create the non-copying NumPy array view
                // The 'base' object must be the Python object that owns
                // the 'self' C++ instance to manage lifetime correctly.
                // We get this Python object by casting the C++ reference 'self'.
                py::object py_self = py::cast(&self, py::return_value_policy::reference);

                // Create NumPy views
                py::array pos_view = iactxx::pybind::create_vec3f_numpy_view(pos_ptr, size, py_self);
                py::array dir_view = iactxx::pybind::create_vec3f_numpy_view(dir_ptr, size, py_self);
                py::array t_view = iactxx::pybind::create_numpy_view(t_ptr, size, py_self);
                py::array zem_view = iactxx::pybind::create_numpy_view(zem_ptr, size, py_self);
                py::array wl_view = iactxx::pybind::create_numpy_view(wl_ptr, size, py_self);
                py::array map_view = iactxx::pybind::create_numpy_view(map_ptr, bunches_mapping.size(), py_self);
                
                // Package them into a list
                py::list result_list;
                result_list.append(pos_view);
                result_list.append(dir_view);
                result_list.append(wl_view);
                result_list.append(t_view);
                result_list.append(zem_view);
                result_list.append(map_view);

                // Return the views
                return result_list;
            },
            R"raw(
            Returns bunches as a list of NumPy array view of photon positions, directions, 
            wavelengths, arrival times, emission altitudes and event mapping to be passed to :py:meth:`iactsim.IACT.trace_photons` method.

            For example, if ``cfile`` is a ``IACTFile`` instance and ``telescope`` a ``IACT`` instance:

                .. code-block:: python
                    
                    triggered_events = telescope.trace_photons(
                        *cfile.get_telescope_bunches(tel_id),
                        photons_per_bunch=cfile.bunch_size,
                        simulate_camera=True
                    )
            
            )raw",
            py::arg("tel_id")
        )
        .def(
            "get_event_bunches",
            [](iactxx::IACTFile &self, int tel_id, int event_idx) -> py::list {
                auto temp_bunches = self.getEventBunches(tel_id, event_idx);
                auto* heap_bunches_ptr = new iactxx::eventio::Bunches<iactxx::eventio::f32>(std::move(temp_bunches));
                
                // Owner has the ownership of the heap-allocated data
                // Data is deleted when the Numpy arrays have zero reference count
                // See https://stackoverflow.com/questions/54876346/pybind11-and-stdvector-how-to-free-data-using-capsules
                py::capsule owner(
                    heap_bunches_ptr,
                    [](void *ptr_to_delete) {
                        delete static_cast<iactxx::eventio::Bunches<iactxx::eventio::f32>*>(ptr_to_delete);
                    }
                );
                
                size_t size = heap_bunches_ptr->n_bunches;
                const BunchPosition* pos_ptr = heap_bunches_ptr->pos.get();
                const BunchDirection* dir_ptr = heap_bunches_ptr->dir.get();
                const iactxx::eventio::f32* time_ptr = heap_bunches_ptr->time.get();
                const iactxx::eventio::f32* wl_ptr = heap_bunches_ptr->wavelength.get();
                const iactxx::eventio::f32* zem_ptr = heap_bunches_ptr->zem.get();
                
                py::array pos_view = iactxx::pybind::create_vec3f_numpy_view(pos_ptr, size, owner);
                py::array dir_view = iactxx::pybind::create_vec3f_numpy_view(dir_ptr, size, owner);
                py::array t_view = iactxx::pybind::create_numpy_view(time_ptr, size, owner); 
                py::array wl_view = iactxx::pybind::create_numpy_view(wl_ptr, size, owner); 
                py::array zem_view = iactxx::pybind::create_numpy_view(zem_ptr, size, owner); 
                
                py::list result_list;
                result_list.append(pos_view);
                result_list.append(dir_view);
                result_list.append(wl_view);
                result_list.append(t_view);
                result_list.append(zem_view);

                return result_list;
            },
            R"raw(
            Returns bunches of an event as a list of NumPy array of photon positions, directions, 
            wavelengths, arrival times and emission altitudes to be passed to :py:meth:`iactsim.IACT.trace_photons` method.

            For example, if ``cfile`` is a ``IACTFile`` instance and ``telescope`` a ``IACT`` instance:

                .. code-block:: python
                    
                    telescope.trace_photons(
                        *cfile.get_event_bunches(tel_id, event_index),
                        photons_per_bunch=cfile.bunch_size,
                        simulate_camera=True
                    )
            
            )raw",
            py::arg("tel_id"),
            py::arg("event_index")
        );
    
    io_submodule.def(
        "read_corsika_file",
        &iactxx::read_file,
        R"raw(
            Read a file produced by CORSIKA IACT extension and return a :py:class:`IACTFile` 
            instance containing the photon bunches data ready to be passed to :py:meth:`iactsim.IACT.trace_photons`.

            Parameters
            ----------
            filepath : str
                Path of the CORSIKA file
            skip_telescopes : list[int]
                Telescope ID that can be skipped
            min_n_bunches : int
                Parse only events with more than `min_n_bunches` bunches
            
            Returns
            -------
            :py:class:`IACTFile`
                File handler
            
        )raw",
        py::arg("filepath"),
        py::arg("skip_telescopes")=std::vector<int>(),
        py::arg("min_n_bunches")=1,
        py::call_guard<py::gil_scoped_release>()
    );
    
    io_submodule.def(
        "read_corsika_files",
        &iactxx::read_files,
        R"raw(
            Read in parallel a list of files produced by CORSIKA IACT extension and return 
            the corresponding :py:class:`IACTFile` instances containing the photon bunches data
            ready to be passed to :py:meth:`iactsim.IACT.trace_photons`.

            Useful when multiple compressed CORSIKA files have to be read.

            Parameters
            ----------
            filepaths : list[str]
                List of CORSIKA file paths
            skip_telescopes : list[int]
                Telescope ID that can be skipped
            min_n_bunches : int
                Parse only events with more than `min_n_bunches` bunches
            
            Returns
            -------
            list[:py:class:`IACTFile`]
                List of file handlers

            Notes
            -----
            Parallel reading from HDDs can deteriorate performance.
            
        )raw",
        py::arg("filepaths"),
        py::arg("skip_telescopes")=std::vector<int>(),
        py::arg("min_n_bunches")=1,
        py::call_guard<py::gil_scoped_release>()
    );
}