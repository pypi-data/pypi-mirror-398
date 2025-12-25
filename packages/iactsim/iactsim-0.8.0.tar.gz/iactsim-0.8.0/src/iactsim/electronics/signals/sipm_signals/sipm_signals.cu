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
////// Device functions                                         //
//                                                              //
// __device__ get_interval                                      //
// __device__ interp1d                                          //
// __device__ borel_pmf                                         //
// __device__ borel_generator                                   //
// __device__ waveform_normalization                            //
// __device__ poisson_interarrival_time                         //
//                                                              //
////// Kernels                                                  //
//                                                              //
// __global__ sipm_signals                                      //
//                                                              //
//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////

#include <curand_kernel.h>

extern "C"{

/**
 * @brief Calculates the sub-window interval for a given thread.
 *
 * This function determines the start and end indices (inclusive) of a sub-window
 * within a larger window of size `width`. The sub-window is assigned to a
 * specific thread identified by `thid`, given a total number of threads `n_threads`.
 * The function divides the work (`width`) amongst the threads as evenly as possible.
 *
 * @param extrema An array of size 2. On return, `extrema[0]` will contain the
 *               starting index (inclusive) of the sub-window, and `extrema[1]`
 *               will contain the ending index (inclusive) of the sub-window.
 * @param thid   The ID of the current thread. Threads are assumed to be
 *               numbered from 0 to `n_threads` - 1.
 * @param n_threads The total number of threads processing the entire window.
 * @param width  The total width (size) of the overall window being processed.
 *
 * @return void (The function modifies `extrema` in place).
 *
 * @details
 * The sub-window size for each thread is calculated as `ceil(width / n_threads)`.
 * This ensures that the entire window is covered, even if `width` is not
 * perfectly divisible by `n_threads`. The last few threads may have slightly
 * smaller sub-windows due to integer division.
 * 
 */
__device__ void get_interval(int* extrema, int thid, int n_threads, int width) 
{
    if (width <= n_threads) {
        extrema[0] = thid;
        extrema[1] = thid < width ? thid+1 : thid;
        return;
    }
    // else {
    //     extrema[0] = __mul24(width,thid) / n_threads;
    //     extrema[1] = __mul24(width,thid+1) / n_threads;
    // }
    int size_per_thread = (width + n_threads -1) / n_threads;
    extrema[0] = min(width, __mul24(size_per_thread,thid));
    extrema[1] = min(width, __mul24(size_per_thread,thid+1));
}

__device__ float interp1d_text(float x, float inv_dx, float start_x, cudaTextureObject_t& tex) {
    float u = (x-start_x)*inv_dx;
    return tex1D<float>(tex, u+0.5f);
}

/**
 * @brief Performs linear interpolation on a 1D dataset containing multiple curves.
 *
 * This function performs linear interpolation to estimate the value of a function at a given point `x0`,
 * based on a set of known data points (`xs`, `ys`) that represent multiple curves. The specific curve
 * to use for interpolation is defined by `start_x`, `start_y`, and `n_points`.
 *
 * @param x0 The x-coordinate at which to interpolate the value.
 * @param xs An array of x-coordinates of the known data points for multiple curves.
 *           The x-coordinates for each curve must be sorted in ascending order.
 * @param ys An array of y-coordinates (function values) corresponding to the `xs` values for multiple curves.
 * @param n_points The number of data points in the specific curve to be used for interpolation.
 * @param inv_dx The inverse of the spacing between consecutive x-coordinates in the curve (1 / (xs[i+1] - xs[i])).
 *               Assumes uniform spacing between points within each curve.
 * @param start_index The starting index in the `xs` and `ys` arrays for the curve to be used.
 *
 * @return The interpolated value at `x0`. Returns 0.f if `x0` is outside the range of the specified curve or if any error occurs.
 */
__device__ float 
interp1d(
    float x0,
    const float* xs,
    const float* ys,
    int n_points,
    float inv_dx,
    int start_index
)
{
    // Distance the first input position
    float dx = x0 - xs[start_index];

    if (dx < 0.f) return 0.f;
    
    // Index of the nearest lower neighbor
    int xi = __float2int_rz(dx * inv_dx);

    if (xi>=n_points-1) return 0.f;

    // Values of the nearest neighbors
    float f0 = ys[start_index+xi];
    float f1 = ys[start_index+xi+1];

    // Calculate weights for linear interpolation
    float t = dx * inv_dx - truncf(dx * inv_dx);

    // Linear interpolation
    // See https://en.wikipedia.org/wiki/Linear_interpolation#Programming_language_support
    return fmaf(t, f1, fmaf(-t, f0, f0));
}

/**
 * @brief Calculates the Borel probability mass function (PMF).
 *
 * This function computes the probability mass function of the Borel
 * distribution at a given value of `k` and with parameter `l` (lambda).
 * The Borel distribution is a discrete probability distribution arising
 * in the context of branching processes and queueing theory.
 *
 * @param k The non-negative integer value at which to evaluate the PMF.  Must be >= 0.
 * @param l The parameter of the Borel distribution (lambda). Must be in the range (0, 1).
 *
 * @return The probability mass function value at `k`, given parameter `l`. Returns a float.
 *          Returns 0 if k < 0.  Returns 0 if l <=0 or l >= 1.
 *
 * @details
 * The Borel distribution's PMF is given by:
 *   P(K = k) = (exp(-lambda * k) * (lambda * k)^(k-1)) / k!   for k = 1, 2, 3,...
 *          and 0 for k = 0.
 *
 * This implementation uses the following formula for numerical stability,
 * avoiding potential overflow or underflow with large factorials:
 *
 *   log(P(K=k)) = (k-1) * log(l*k) - l*k - lgamma(k+1)
 *   P(K=k) = exp(log(P(K=k)))
 *
 * where `lgamma(k+1)` is the natural logarithm of the gamma function of (k+1), which is equal to log(k!).
 *
 * @warning The input `l` must be within the range (0, 1). Values outside this range
 *          will return 0.  Input `k` should be a non-negative integer.
 *
 */
__device__ float borel_pmf(float k, float l)
{
    float logbr = fmaf(k-1.f, __logf(fmaf(l, k, 0.f)), -fmaf(l, k, lgammaf(k+1.f)));
    return __expf(logbr);
}

/**
 * @brief Generates a random variate from the Borel distribution using inversion sampling.
 *
 * This function implements the inversion sampling method to generate a random
 * number from the Borel distribution with parameter `l` (lambda).
 *
 * @param l The parameter of the Borel distribution (lambda).  Must be in the range (0, 1).
 * @param s A reference to a `curandStatePhilox4_32_10_t` object, representing the
 *          state of the Philox4x32-10 pseudo-random number generator. This state
 *          must be initialized before calling this function.
 *
 * @return A random float from the Borel distribution with parameter `l`.
 *          Returns 1.0f if `l` is very small (< 1e-4f).
 *
 */
__device__ float borel_generator(float l, curandStatePhilox4_32_10_t &s)
{
    if (l<1e-4f) return 1.f;
    
    float u = curand_uniform(&s);

    float p1 = 0.f;
    float k = 0.f;
    while (true) {
        float p2 = p1 + borel_pmf(k+1.f, l);
        if ( ((u > p1) & (u <= p2)) | (p2-p1<1e-9f) ) {
            return k + 1.f;
        }
        p1 = p2;
        k += 1.f;
    }
}

/**
 * @brief Calculates a normalization factor for a waveform, accounting for prompt cross-talk and micro-cells gain dispersion.
 *
 * This function simulates the effects of cross-talk and variations in micro-cell gain
 * on the overall normalization of a waveform.
 *
 * @param state A reference to a `curandStatePhilox4_32_10_t` object, representing the
 *              state of the Philox4x32-10 pseudo-random number generator.  This state
 *              must be initialized before calling this function.
 * @param n_discharges  The number of events to simulate (main discharge + xt discharges).  This effectively controls
 *              how many random samples are summed to produce the normalization factor.
 * @param std_ucells The standard deviation of the micro-cell gain.  This parameter
 *                   scales the contribution of each random sample.
 *
 * @return The calculated normalization factor (a float).
 *
 * @details
 * The normalization factor is computed as the sum of `n_discharges` independent random
 * variables, each drawn from a normal distribution with mean 1.0 and standard
 * deviation `std_ucells`.
 *
 */
__device__ float waveform_normalization(curandStatePhilox4_32_10_t &state, float n_discharges, float std_ucells)
{
    float normalization_factor = 0.0f;
    for (int k=0; k<(int)n_discharges; k++) normalization_factor += fmaf(curand_normal(&state), std_ucells, 1.0f);
    return normalization_factor;
}

/**
 * @brief Generates a Poisson inter-arrival time.
 *
 * This function calculates a random inter-arrival time from an exponential
 * distribution, which is equivalent to the inter-arrival times in a Poisson process.
 *
 * @param state A reference to a `curandStatePhilox4_32_10_t` object, representing the
 *              state of the Philox4x32-10 pseudo-random number generator. This state
 *              must be initialized before calling this function.
 * @param inv_bkg_rate The inverse of the background rate of the Poisson process.
 *                     This represents the mean inter-arrival time.
 *
 * @return A random float representing the inter-arrival time.
 * 
 */
__device__ float poisson_interarrival_time(curandStatePhilox4_32_10_t &state, float inv_bkg_rate)
{
    return -fmaf(__logf(curand_uniform(&state)),  inv_bkg_rate, 0.f);
}

/**
 * @brief Computes the formed SiPM signals.
 *
 * This kernel function simulates the response of Silicon Photo-Multipliers (SiPMs)
 * by superimposing single photo-electron (PE) waveforms based on PE arrival time,
 * SiPM cross-talk, SiPM microcells gain dispersion and SiPM PE-background noise.  
 * It operates on a per-pixel and per-channel basis, assigning a CUDA block per pixel per channel.
 *
 * @param windows Array of time windows for each channel.  Defines the time ranges
 *                over which signals are computed. `windows[windows_map[channel] : windows_map[channel+1]]`
 *                is the time window for `channel`.
 * @param windows_map Array indicating the starting  and ending index of the time window for each channel
 *                      within the `windows` array.
 * @param signals Output array where the computed SiPM signals are stored.  The signal for
 *                a given channel and pixel is stored in a contiguous block.
 *                `signals[start_signals[channel] + pixel_id * n_window : start_signals[channel] + (pixel_id + 1) * n_window]`
 *                where n_window = windows_map[channel+1] - windows_map[channel].
 *                The array does not need to be initialized before the kernel invocation.
 * @param signals_map Array indicating the starting index and ending index of each channel inside the array signals.
 * @param n_channels Number of channels.
 * @param t0s Array of discharge times for each pixel.
 * @param map Array that maps pixel indices to the range of their corresponding
 *            discharge times in the `t0s` array.  Specifically, `t0s[map[pixel_id]:map[pixel_id+1]]`
 *            provides the discharge times for `pixel_id`.
 * @param waveforms Array containing the texture pointer of all channel waveforms.
 * @param inv_dt_waveforms Array containing the inverse of the time spacing (dt) for each
 *                         waveform.
 * @param t_start_waveforms Array indicating the starting time of each waveform.
 * @param gains Array containing the pulse peak amplitued for each pixel for each channel (n_pixels*n_channels size)
 * @param xt Array of cross-talk probabilities for each pixel.  This represents the probability
 *           that a discharge in one microcell will trigger a discharge in an adjacent microcell.
 * @param std_ucells Array of microcell gain dispersions for each pixel. This models the
 *                   variation in the charge produced by different microcells for a single photon.
 * @param mask Array indicating whether a pixel is masked (1) or active (0). Masked pixels
 *             will have zero signal.
 * @param inv_bkg_rate Array of inverse background rates for each pixel (in units of time).  This is
 *                     used to generate background noise events.
 * @param bkg_start Start time for background noise generation.
 * @param bkg_end End time for background noise generation.
 * @param seed Array of random number generator seeds, one for each pixel.
 * @param n_pixels Number of pixels.
 *
 * 
 * @warning
 *   1. The number of blocks must be at least n_pixels*n_channels (i.e. a block per pixel per channel)
 *   2. The size of the shared memory buffer must be equal to the size of the widest time window 
 *      multiplied by 4 (i.e. 4 bytes per time bin).
 *
 * @details
 * The kernel is launched with a 1D grid of blocks, where each block is responsible for
 * computing the signal for a single (pixel, channel) combination.  Each block uses
 * shared memory (`shared_buffer`) to store the intermediate signal, improving performance
 * by reducing global memory accesses.
 * 
 * The signal computation involves the following steps:
 * 
 * 1. Determine the block assigned channel and pixel. Initialize the shared memory buffer to zero.
 * 2. Initialize a ```curandStatePhilox4_32_10_t``` random number generator for the pixel using the provided seed.
 *    Each pixel has a unique seed per event. This allows the signals of each channel to be computed in different stages.
 * 3. Iterate through the photon arrival times associated with the current pixel. For each photon:
 * 
 *      - calculate the number of cross-talk photons using a Borel distribution;
 *      - calculate the microcell gain variation, incorporating gain dispersion using a normal distribution;
 *      - superimpose the single-photon waveform onto the shared memory buffer, interpolating the channel waveform.
 * 
 * 4. Generate background noise events with Poissonian interarrival times with the specified inverse of the background rate.
 *    For each background event:
 * 
 *      - calculate cross-talk and gain variation as in the signal photon loop;
 *      - superimpose the single-photon waveform onto the shared memory buffer.
 * 
 * 5. Copy the computed signal from the shared memory buffer to the appropriate location in the global ```signals``` array.
 * 
 */
__global__ void sipm_signals(
    // Time windows
    const float* windows, // windows where to compute the signals for each channel
    const int* windows_map, // where the window of each channel starts and ends in the `windows` array
    // Channels signals
    float* signals, // computed signals
    const int* signals_map, // where the signals of each channel starts and ends in `signals`
    bool* skip_channel,
    int n_channels, // number of channels
    // Arrival times
    const float* t0s, // discharge times
    const int* map, // discharge times of pixel n: t0s[map[n]:map[n+1]]
    // Waveforms
    const unsigned long long* textures, // one for each channel
    const float* inv_dt_waveforms, // invers of the x-spacing of each waveform
    const float* t_start_waveforms, // start time of each waveform
    const float* gains,
    // SiPM details
    const float* xt, // cross-talk of each pixel
    const float* std_ucells, // ucells gain dispersion of each pixel
    const int* mask, // pixel mask
    // Background
    const float* inv_bkg_rate, // inverse of the background rate for each pixel
    float bkg_start, // time from which generate backgorund
    float bkg_end, // time at which stop background generation
    // Random seed
    unsigned long long* seed, // seed for each pixel
    // Number of pixels
    int n_pixels
)
{
    // Current block
    int bid = blockIdx.x;

    // A block for each pixel channel -> n_pixels*n_channels blocks
    if (bid > __mul24(n_channels, n_pixels) - 1) return;

    // Current thread
    int thid = threadIdx.x;

    // Channel assigned to this block
    int channel = bid / n_pixels;

    if (skip_channel[channel] == true) return;

    // Pixel assigned to this block
    int pixel_id = bid - n_pixels*channel;
    
    // Current channel window length
    int n_window = windows_map[channel+1] - windows_map[channel];

    // Pointer to the current channel signal
    float* y = &signals[signals_map[channel]];

    // Pointer to the current channel time-window
    const float* t = &windows[windows_map[channel]];

    // Number of threads that will compute the waveform
    int n_threads = blockDim.x;
    
    // Pixel signal on shared memory (total amount of shared memory must be dictated by the wider window)
    extern __shared__ float shared_buffer[];
    float* sm_signal = shared_buffer;

    // Compute the signal
    // 1- get the sub-window extrema of each thread
    int extrema[2];
    get_interval(extrema, thid, n_threads, n_window);
    if (extrema[0] == extrema[1]) return;

    // 2- initialize shared waveform to 0 (no need to sync since each thread has is own sub-window)
    for (int i=extrema[0]; i<extrema[1]; i++) {
        sm_signal[i] = 0.0f;
    }

    // 3- write into global memory zero-filled waveforms for masked pixels
    if (mask[pixel_id] == 1) {
        for (int i=extrema[0]; i<extrema[1]; i++) {
            int index = __mul24(pixel_id, n_window) + i;
            y[index] = sm_signal[i];
        }
        return;
    }

    // 4- initialize a random generator for cross-talk, microcells gain dispersion and background photo-electrons (same seed for all threads)
    curandStatePhilox4_32_10_t state;
    curand_init(seed[pixel_id], 0, 0, &state);

    float local_xt = xt[pixel_id];
    float local_std_ucells = std_ucells[pixel_id];

    cudaTextureObject_t current_waveform_texture = textures[channel];
    float inv_dt_waveform = inv_dt_waveforms[channel];
    float t_start_waveform = t_start_waveforms[channel];

    // 5- Loop over source photo-electrons arrival time
    int j_start = map[pixel_id];
    int j_end = map[pixel_id+1];
    for (int j=j_start; j<j_end; j++)
    {
        // Get arrival time index
        float t0 = t0s[j];
        
        // Number of cross-talk photo-electrons
        float n_xt = borel_generator(local_xt, state);

        // Add micro-cells gain dispersion
        float xt_pe = waveform_normalization(state, n_xt, local_std_ucells);
        
        // Update waveform at the current thread time slices
        for (int i=extrema[0]; i<extrema[1]; i++) {
            
            // Check if the waveform contributes in the subwindow
            float tdiff = t[i] - t0;

            // Overimpose waveforms
            float single_waveform = interp1d_text(
                tdiff,
                inv_dt_waveform,
                t_start_waveform,
                current_waveform_texture
            );
            sm_signal[i] += single_waveform*xt_pe;
        }
    }

    // 6- define the time from which generate background discharge
    //    do not generate background if it is lower than 1e-6 discarges per ns
    float local_inv_bkg_rate = inv_bkg_rate[pixel_id];
    float t_noise = local_inv_bkg_rate > 1e6f ? bkg_end+1.f : bkg_start;

    // 7- add background photo-electrons (with Poissonian inter-arrival times)
    while (true) {    
        // Next background photo-electron arrival time
        t_noise += poisson_interarrival_time(state, local_inv_bkg_rate);

        // End of the background window reached, stop generating background pe's
        if (t_noise > bkg_end) break;

        // Number of cross-talk photo-electrons
        float n_xt = borel_generator(local_xt, state);

        // Add micro-cells gain dispersion
        float xt_pe = waveform_normalization(state, n_xt, local_std_ucells);
        
        // Update the waveform
        for (int i=extrema[0]; i<extrema[1]; i++) {
            // Check if the waveform contributes in the subwindow
            float tdiff = t[i] - t_noise;

            // Skip time-slice if it is before the arrival time
            if (tdiff < 0.0f) continue;
            
            // Skip all the time slices after the first one 
            // that is beyond the maximum waveform extent
            // if (tdiff > waveform_extent) break;

            // Overimpose waveforms
            float single_waveform = interp1d_text(
                tdiff,
                inv_dt_waveform,
                t_start_waveform,
                current_waveform_texture
            );
            sm_signal[i] += single_waveform*xt_pe;
        }
    }
    
    float local_gain = gains[bid];
    // 8- write results back to the global signal array
    for (int i=extrema[0]; i<extrema[1]; i++) {
        int index = __mul24(pixel_id, n_window) + i;
        y[index] = sm_signal[i]*local_gain;
    }
}

} // extern C