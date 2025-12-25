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

//////////////////////////////////////////////////////////////////
//////////////////////////// Content /////////////////////////////
//                                                              //
////// Kernels                                                  //
//                                                              //
// __global__ generate_map                                      //
// __global__ generate_arrival_times                            //
//                                                              //
//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////

#include <curand.h>
#include <curand_kernel.h>

extern "C" {

/**
 * @brief Extract the number of Poisson Photo-Electrons (PEs) arrival times to generate per pixel.
 * 
 * @param pe_per_pixel Array of `n_pixels+1` of number of PEs to generate per pixel.
 *                     `pe_per_pixel[1]` contains the number of PEs for the pixel 0. The first element is always 0.
 * @param mean Mean number of PEs per pixel.
 * @param seed Random number generator seed.
 * @param n_pixels Total number of pixels
 */
__global__ void generate_map(
    int *pe_per_pixel,
    float* mean,
    unsigned long long seed,
    int n_pixels
) 
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid <= n_pixels) {
        if (tid == 0) {
            pe_per_pixel[tid] = 0;
        }
        else {
            curandStatePhilox4_32_10_t state;
            curand_init(seed, (unsigned long long)tid, 0, &state);
            float random_num = curand_poisson(&state, mean[tid-1]);
            pe_per_pixel[tid] = __float2int_rn(random_num);
        }
    }
}

/**
 * @brief Generate Poisson arrival times in a time window which is equal for all pixels.
 * 
 * @param pe_arrival_times Photo-electrons discharge times. 
 *                         These are mapped into pixels by the cumulative sum of `pe_per_pixel` of the `generate_map` kernel.
 * @param t_start Start time from which generate arrival times.
 * @param duration Duration of the flash.
 * @param seed Random number generator seed.
 * @param n_pes Total number of photo-electrons to generate (the last element of the cumulative sum of `pe_per_pixel`).
 * 
 */
__global__ void generate_arrival_times(
    float* pe_arrival_times,
    float t_start,
    float duration,
    unsigned long long seed,
    int n_pes
)
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid < n_pes) {
        curandStatePhilox4_32_10_t state;
        curand_init(seed, (unsigned long long)tid, 0, &state);
        pe_arrival_times[tid] = t_start+curand_uniform(&state)*duration;
    }
}

} // extern "C"