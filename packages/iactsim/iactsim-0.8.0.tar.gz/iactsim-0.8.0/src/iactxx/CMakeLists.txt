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

cmake_minimum_required(VERSION 3.15 FATAL_ERROR)

project(iactxx LANGUAGES CXX)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Configure C++ Project
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

###############
# Dependencies
###############

# Variables to store dependency information for the core library
set(IACTXX_CORE_DEP)
set(IACTXX_CORE_INC)

# Find Python
find_package(Python REQUIRED COMPONENTS Interpreter Development)
message(STATUS "Python version: ${Python_VERSION_STRING}")
message(STATUS "Python interpreter: ${Python_EXECUTABLE}")
message(STATUS "Python includes: ${Python_INCLUDE_DIRS}")
message(STATUS "Python libraries: ${Python_LIBRARIES}")

# Find pybind11
find_package(pybind11 REQUIRED)
message(STATUS "pybind11 version: ${pybind11_VERSION}")
message(STATUS "pybind11 includes: ${pybind11_INCLUDE_DIRS}")

# OpenMP flags
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    list(APPEND IACTXX_CORE_DEP OpenMP::OpenMP_CXX) # add to the core library dependencies
else()
    message(STATUS "OpenMP not found.")
endif()

find_package(zstd)
if(zstd_FOUND)
    list(APPEND IACTXX_CORE_DEP zstd::libzstd_shared) # add to the core library dependencies
else()
    message(STATUS "ZSTD not found.")
endif()


# Find ZLIB or clone ZLIB-NG (adapted from https://github.com/zlib-ng/minizip-ng)
option(USE_ZLIBNG "Build and use zlib-ng instead of system ZLIB" ON)
if(USE_ZLIBNG)
    message(STATUS "############## Fetching zlib-ng")
    message(STATUS "############## ")

    include(clone-repo.cmake)

    set(ZLIB_ENABLE_TESTS OFF CACHE BOOL "Build zlib-ng tests" FORCE)
    set(ZLIB_COMPAT ON CACHE BOOL "Enable zlib compatibility")
    set(WITH_NATIVE_INSTRUCTIONS ON CACHE BOOL "Compiles with full instruction set supported on this host (gcc -march=native)")

    clone_repo(zlib https://github.com/zlib-ng/zlib-ng stable)

    # Don't automatically add all targets to the solution
    add_subdirectory(${ZLIB_SOURCE_DIR} ${ZLIB_BINARY_DIR} EXCLUDE_FROM_ALL)

    list(APPEND IACTXX_INC ${ZLIB_SOURCE_DIR})
    list(APPEND IACTXX_INC ${ZLIB_BINARY_DIR})

    # Have to add zlib to install targets
    if(ZLIB_COMPAT AND (NOT DEFINED BUILD_SHARED_LIBS OR NOT BUILD_SHARED_LIBS))
        message(STATUS "Adding zlibstatic to dependencies")
        list(APPEND IACTXX_CORE_DEP zlibstatic)
    else()
        message(STATUS "Adding zlib to dependencies")
        list(APPEND IACTXX_CORE_DEP zlib)
    endif()

    if(EXISTS "${ZLIB_BINARY_DIR}/zlib-ng.h")
        message(STATUS "ZLIB repository detected as ZLIBNG")
        set(ZLIB_COMPAT OFF)
    else()
        message(STATUS "ZLIB repository detected as ZLIB")
        set(ZLIB_COMPAT ON)
    endif()
    message(STATUS "##############")
    message(STATUS "############## Fetching zlib-ng done")
else()
    find_package(ZLIB)
    list(APPEND IACTXX_CORE_DEP ZLIB::ZLIB)
endif()

#############################
# Define Core Static Library
#############################
add_subdirectory(src) # look for src/iactxx/src/CMakeLists.txt

# This library contains the main C++ logic, shared between the Python module and executables
add_library(iactxx_core STATIC
    ${iactxx_SOURCES}
)
set_target_properties(iactxx_core PROPERTIES CXX_STANDARD ${CMAKE_CXX_STANDARD})
target_include_directories(iactxx_core
    PRIVATE
        src
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
        ${IACTXX_CORE_INC}
)
target_link_libraries(iactxx_core PUBLIC ${IACTXX_CORE_DEP})

if(OpenMP_CXX_FOUND)
    target_compile_definitions(iactxx_core PUBLIC USE_OPENMP)
endif()

if(zstd_FOUND)
    target_compile_definitions(iactxx_core PUBLIC USE_LIBZSTD)
endif()

#################
# Compiler flags
#################

message(STATUS "Detecting compiler for flags: ${CMAKE_CXX_COMPILER_ID}")

# Define flags based on compiler
set(CMAKE_CXX_FLAGS_DEBUG "-pg -O0")
set(CMAKE_CXX_FLAGS_RELEASE "")

if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message(STATUS "Setting GCC specific flags")
    set(CMAKE_CXX_FLAGS_RELEASE "-Ofast -march=native -Wall -Wextra -Wpedantic -Wno-format-truncation") #-fopt-info-vec
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "NVHPC")
    message(STATUS "Setting NVHPC specific flags")
    set(CMAKE_CXX_FLAGS_RELEASE "-Ofast -march=native -Wall -Wextra -Wpedantic -Minfo=time") #loop,mp,opt,vect,
else()
    message(WARNING "Compiler ${CMAKE_CXX_COMPILER_ID} not explicitly recognized. Applying generic flags.")
    set(IACTXX_RELEASE_FLAGS "-O3")
    set(IACTXX_DEBUG_FLAGS "-g")
endif()

# Apply flags
target_compile_options(iactxx_core PRIVATE
    $<$<CONFIG:Debug>:${DEBUG_FLAGS}>
    $<$<CONFIG:Release>:${RELEASE_FLAGS}>
)

################################
# pybind11 Python module iactxx
################################

# Create pybind11 module
pybind11_add_module(iactxx SHARED
    iactxx.cpp
)

# Link module dependencies
target_link_libraries(iactxx PRIVATE
    iactxx_core        # link the static core library
    pybind11::module   # link pybind11
)

# Configure include directories
target_include_directories(iactxx PRIVATE
    ${pybind11_INCLUDE_DIRS} # pybind11 headers
    ${Python_INCLUDE_DIRS}   # Python C API headers
    # The public headers from iactxx_core are automatically added
    # because iactxx links publicly against iactxx_core include directories
)

#########################
# Executables definition
#########################

# # Example standalone C++ executable
# add_executable(
#     test.exe
#     test.cpp 
# )

# # Link dependencies
# target_link_libraries(test.exe PRIVATE
#     iactxx_core # link the static core library
# )

# # No include directories
# # The public headers from iactxx_core are automatically added via linking

# # Set C++ standard for the executable
# set_target_properties(test.exe PROPERTIES CXX_STANDARD ${CMAKE_CXX_STANDARD})
# target_compile_options(test.exe PRIVATE
#     $<$<CONFIG:Debug>:${DEBUG_FLAGS}>
#     $<$<CONFIG:Release>:${RELEASE_FLAGS}>
# )

###############
# Installation
###############

# Install Python module
# Install the compiled module file into the Python package directory (site-packages/iactsim)
# scikit-build-core maps CMAKE_INSTALL_PREFIX to the root of the site-packages installation.
# The module will be imported by the iactsim __init__.py
install(
    TARGETS iactxx
    LIBRARY DESTINATION iactsim # install to <prefix>/iactsim/
)

# # Install example C++ executable
# install(
#     TARGETS test.exe
#     RUNTIME DESTINATION iactsim/bin # Installs to <prefix>/iactsim/bin
# )

# Install public headers (maybe useful in the future)
# install(
#     DIRECTORY ${PROJECT_SOURCE_DIR}/include/ # the directory containing public headers
#     DESTINATION include/iactsim # installs headers to <prefix>/include/iactsim
#     FILES_MATCHING PATTERN "*.h" # pattern to match header files
# )

message(STATUS "CMake configuration finished.")