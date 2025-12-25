/*
 * Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * This file is part of iactsim.
 *
 * iactsim is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * iactsim is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with iactsim.  If not, see <https://www.gnu.org/licenses/>.
 */

#pragma once

namespace iactxx::math 
{

/**
 * @brief Template function to add two vectors an store the results into a vector.
 * 
 * @tparam T 
 * @param ptr1 
 * @param ptr2 
 * @param ptr_result 
 * @param size 
 */
template <typename T>
void add(
    T* ptr1,
    T* ptr2,
    T* ptr_result,
    size_t size
)
{
    // Let the compiler handle optimizations
    # pragma omp simd
    for (size_t i = 0; i < size; ++i) {
        ptr_result[i] = ptr1[i] + ptr2[i];
    }
}

/**
 * @brief Template function to compute a vector-scalar product and add the result to a vector.
 * 
 * @tparam T 
 * @param a 
 * @param ptr_x 
 * @param ptr_y
 * @param size 
 */
template <typename T>
void axpy(
    T a,
    T* ptr_x,
    T* ptr_y,
    size_t size
) {
    // Let the compiler handle optimizations
    #pragma omp simd
    for (size_t i = 0; i < size; ++i) {
            ptr_y[i] = a * ptr_x[i] + ptr_y[i];
    }
}

} // namespace iactxx::math 