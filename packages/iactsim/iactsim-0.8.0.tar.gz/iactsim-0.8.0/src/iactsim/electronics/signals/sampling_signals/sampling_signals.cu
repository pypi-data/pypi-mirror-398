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
//                                                              //
////// Kernels                                                  //
//                                                              //
// __global__ peak_detection                                    //
// __global__ digitize                                          //
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

/**
 * @brief Detects the peak value and its corresponding time within a specified time interval for each pixel.
 *
 * This kernel function implements a parallel peak detection algorithm. The algorithm searches for the maximum
 * signal value within a *peak-detection window* for each pixel. This peak-detection window is a
 * sub-interval of the *global time window* covered by the entire signal.
 *
 * @details
 * The algorithm works as follows:
 * 
 *   1. The kernel uses one block per pixel. Each thread within a block is responsible for
 *      processing a sub-window of the global time window, defined by the `time_window` array.
 *   2. Threads within a block cooperate using shared memory. Each thread finds the maximum
 *      value within its assigned sub-window of the global time window and stores it, along with the corresponding
 *      time, in shared memory.
 *   3. A reduction is performed to find the maximum of these intermediate maxima (from shared memory) in order to 
 *      determine the global peak for the pixel within the specified peak-detection window [t_start, t_start+extent].
 *   4. For each pixel the peak value and its corresponding time are written to global memory arrays.
 *
 * The *global time window* is represented by the ```time_window``` array, which contains the time values for all signals.
 * The *peak-detection window* is defined by the ```t_start``` and ```extent``` parameters.  The peak is searched for only
 * within the interval `[t_start, t_start + extent]`.  This allows for focused peak detection within a specific region of interest.
 *
 * The global time window is divided among the available threads. Each thread finds a sub-window maximum and stores
 * it in a shared array `th_peaks_and_times`.  Thread 0 then finds the maximum of `th_peaks_and_times` and stores
 * the result in the global memory arrays ```peak_amplitudes``` and ```peak_time```. The shared array is allocated dynamically.
 * The total shared memory needed is 8 * blockDim.x bytes (2 floats per thread).
 *
 * @param peak_amplitudes Output array to store the peak signal values for each pixel.  Size: ```n_pixels```.
 * @param peak_time Output array to store the time corresponding to the peak signal for each pixel. Size: ```n_pixels```.
 * @param signals Input array containing the signal data for all pixels. The data is organized such that all time
 *                samples for pixel 0 are contiguous, followed by all time samples for pixel 1, and so on.
 *                Size: `n_pixels * time_window_size`.
 * @param time_window Input array containing the time values corresponding to each sample in the ```signals``` array.
 *                    This defines the *global time window*. Size: ```time_window_size```.
 * @param t_start The start time of the *peak-detection window*.
 * @param extent The duration (extent) of the *peak-detection window*, starting from ```t_start```. The peak is searched for
 *               within `[t_start, t_start + extent]`.
 * @param mask Input array acting as a mask. Pixels with a mask value of 1 are skipped (peak=0 and time=0). Size: ```n_pixels```.
 * @param time_window_size The number of time samples in the ```time_window``` array (and the number of samples per
 *                         pixel in the ```signals``` array). This represents the size of the *global time window*.
 * @param n_pixels The total number of pixels.
 * 
 * @warning
 *   1. The number of blocks must be at least n_pixels (i.e. a block per pixel).
 *   2. The number of threads must be a power of 2.
 *   3. The size of the dynamic shared memory buffer must be two times the number of thread assigned to each block multiplied by 4 (i.e. 8 bytes per thread).
 * 
 */
__global__ void peak_detection(
    float* peak_amplitudes,
    float* peak_times,
    const float* signals,
    const float* time_window,
    float t_start,
    float extent,
    const int* mask,
    int time_window_size,
    int n_pixels
)
{    
    // Current block
    int bid = blockIdx.x;

    // One block per pixel
    if (bid >= n_pixels) return;

    // Current thread
    int thid = threadIdx.x;
    
    // Masked pixels
    if (mask[bid] == 1) {
        if (thid == 0) {
            peak_amplitudes[bid] = 0.0f;
            peak_times[bid] = 0.0f;
        }
        return;
    }

    // Initialize shared memory where to store maxima found by all the threads
    extern __shared__ float shared_buffer[]; // 4*2*blockDim.x bytes
    float* th_peaks_and_times = shared_buffer;
    th_peaks_and_times[thid] = -1000000.0f;
    th_peaks_and_times[thid+blockDim.x] = -1000000.0f;

    // Reduce number of threads depending on the window size
    // At least one thread per time-bin for narrow global windows
    int n_threads = min(time_window_size, blockDim.x);
    
    // Prevent non-active threads to write on shared memory after initialization
    if (thid >= n_threads) return;

    // Sub-window extrema of each thread
    int extrema[2];
    get_interval(extrema, thid, n_threads, time_window_size);

    // Write maximum found by each thread into shared memory 
    for (int i=extrema[0]; i<extrema[1]; i++) {
        if (time_window[i] >= t_start & time_window[i] < t_start + extent) {
            int index = i + bid*time_window_size;
            if (th_peaks_and_times[thid] < signals[index]) {
                th_peaks_and_times[thid] = signals[index];
                th_peaks_and_times[thid+blockDim.x] = time_window[i];
            }
        }
    }
    // Wait until each thread finds a maximum
    __syncthreads();

    // Find the global maximum within the block
    for (int s = n_threads / 2; s > 0; s >>= 1) {
        if (thid < s) {
            if (th_peaks_and_times[thid] < th_peaks_and_times[thid + s]) {
                th_peaks_and_times[thid] = th_peaks_and_times[thid + s];
                th_peaks_and_times[thid + blockDim.x] = th_peaks_and_times[thid + s + blockDim.x];
            }
        }
        __syncthreads();
    }

    // Thread 0 writes the final result to global memory
    if (thid == 0) {
        peak_amplitudes[bid] = th_peaks_and_times[0] < -999999.0f ? 0.0f : th_peaks_and_times[0];
        peak_times[bid] = th_peaks_and_times[0] < -999999.0f ? 0.0f : th_peaks_and_times[blockDim.x];
    }
}

// template <typename T>
// Templates cannot be used with nvcc and cupy
// See here https://docs.cupy.dev/en/stable/user_guide/kernel.html#raw-modules

/**
 * @brief Digitizes 16-bit signals and adds digitization baseline and noise.
 *
 * This kernel performs digitization of floating-point input signals, simulating the behavior of an
 * Analog-to-Digital Converter (ADC).  It also adds digitization Gaussian noise to the digitized signal.
 * The kernel operates on a per-pixel basis, processing a time window of signal data for each pixel.
 * The time window is divided into sub-windows, one for each active thread. Each thread processes
 * its assigned sub-window, performing the noise generation, digitization and saturation steps.
 *
 * @param digitized_output Pre-allocated output array to store the digitized signals.  Size: `n_pixels * time_window_size`.
 *                         The data type is `unsigned short`, representing the 16-bit digitized values.
 *                         The array does not need to be initialized.
 * @param input_signals Input array containing the floating-point signal data for all pixels.
 *                      Size: `n_pixels * time_window_size`.
 * @param offset Input array containing the baseline of the digitised signal for each pixel.
 * @param noise Input array containing the per-pixel noise factors. Size: `n_pixels`. These values
 *              scale the standard deviation of the normally distributed noise added to each pixel.
 * @param seed Input array of seeds for the per-pixel pseudo-random number generators. Size: `n_pixels`.
 *             Using different seeds for each pixel ensures uncorrelated noise.
 * @param adc_max The maximum value that the ADC can represent (saturation level).  This should
 *                correspond to the maximum value of 2^n-1 for a n-bit ADC (up to 16-bit).
 * @param n_pixels The total number of pixels.
 * @param time_window_size The number of time samples in the time window (i.e.: the number of samples per
 *                         pixel in the `input_signals` and `digitized_output` arrays).
 *
 * @note The data (`digitized_output` and `input_signals`) is organized such that all time samples 
 *       for pixel 0 are contiguous, followed by all time samples for pixel 1 and so on.
 */
__global__ void digitize(
    unsigned short* digitized_output,
    const float* input_signals, 
    const float* offset,
    const float* noise,
    unsigned long long* seed, 
    int adc_max, 
    int n_pixels,
    int time_window_size
)
{
    // Current block
    int bid = blockIdx.x;

    // One block per pixel
    if (bid >= n_pixels) return;

    // Current thread
    int thid = threadIdx.x;
    // Reduce number of threads depending on the window size
    // At least one thread per time-bin for narrow global windows
    int n_threads = min(time_window_size, blockDim.x);
    
    // Prevent non-active threads to write on shared memory after initialization
    if (thid >= n_threads) return;

    // A seed for each pixel
    curandStatePhilox4_32_10_t state;
    curand_init(seed[bid], 0, 0, &state);

    // Sub-window extrema of each thread
    int extrema[2];
    get_interval(extrema, thid, n_threads, time_window_size);
    
    for (int i=extrema[0]; i<extrema[1]; i++) {
        int digitized_value = __float2uint_rn(input_signals[bid*time_window_size+i] + offset[bid] + curand_normal(&state)*noise[bid]);
        digitized_output[bid*time_window_size+i] = digitized_value > adc_max ? adc_max : digitized_value;
    }
}

} // extern C