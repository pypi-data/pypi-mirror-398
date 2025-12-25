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

# Find all .cpp files in the current directory (src/iactxx/src)
file(GLOB CXX_FILES *.cpp)

# Add these files to the parent scope source list variable
set(iactxx_SOURCES ${iactxx_SOURCES} ${CXX_FILES} PARENT_SCOPE)

# Debugging
message(STATUS "Found sources in src: ${CXX_FILES}")