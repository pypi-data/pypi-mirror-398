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
// __global__ ideal_discriminator                               //
// __global__ count_pixel_triggers                              //
//                                                              //
//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////

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
    int size_per_thread = (width + n_threads -1) / n_threads;
    extrema[0] = min(width, __mul24(size_per_thread,thid));
    extrema[1] = min(width, __mul24(size_per_thread,thid+1));
}

/**
 * @brief Simulates an ideal discriminator response.
 *
 * This kernel processes an input signal and generates a discriminator output signal
 * based on a given threshold.  It also applies a minimum pulse width filter.
 *
 * @param input_signal Input signal data with n_pixels X time_window_size elements.
 * @param output_signal Output discriminator signal data.
 *                      This array should be pre-allocated with the same size as 
 *                      the relevant portion of the input signal.
 *                      The array does not need to be initialized.
 * @param threshold Threshold value for each pixels. The length of this array should equal `n_pixels`.
 * @param offset Discriminator offset for each pixel. The length of this array should equal `n_pixels`.
 * @param time_slices_over_threshold Minimum number of consecutive time slices that the
 *                                   input signal must be above the threshold to be generate a trigger signal.
 * @param mask Array indicating whether a pixel is masked (1) or active (0).
 *             Masked pixels will not generate triggers.
 * @param time_window_size The number of time slices in the signal time window.
 * @param n_pixels The total number of pixels.
 *
 * @details
 * The kernel operates with one block per pixel. Each thread within a block processes a portion of the pixel time window.
 *
 * Discriminator Logic:
 *   
 *   - If the `input_signal` is above the pixel ```threshold``` AND the pixel is not masked (```mask[bid] == 0```) 
 *     the `output_signal` for that time slice is set to 1.0; otherwise the `output_signal` is set to 0.0.
 *
 * Pulse Width Filter:
 * 
 *   - After the initial discriminator signal is computed, a pulse-width filter is applied within each block (pixel) 
 *     to search for consecutive time slices where the `output_signal` is 1.0. If the number of consecutive slices 
 *     over threshold is less than ```time_slices_over_threshold```, those slices in the `output_signal` are reset to 0.0. 
 *     This effectively removes short pulses.
 *
 * Assumptions/Approximations:
 * 
 *   - Zero rising and falling time.
 * 
*/
__global__ void ideal_discriminator(
    const float* input_signal,
    float* output_signal,
    const float* threshold,
    const float* offset,
    int time_slices_over_threshold,
    const int* mask,
    int time_window_size,
    int n_pixels
)
{    
    // Current block
    int bid = blockIdx.x;

    // One block per pixel
    if (bid > n_pixels-1) return;

    // Number of threads that will compute the signal
    int n_threads = blockDim.x;

    // Current thread
    int thid = threadIdx.x;
    
    // Sub-window extrema of each thread
    int extrema[2];
    get_interval(extrema, thid, n_threads, time_window_size);

    float disc_threshold = threshold[bid] + offset[bid];
    
    // Compute discriminator signal
    for (int i=extrema[0]; i<extrema[1]; i++) {
        int index = bid*time_window_size + i;
        if (input_signal[index] > disc_threshold & mask[bid] == 0) {
            output_signal[index] = 1.0f;
        }
        else {
            output_signal[index] = 0.0f;
        }
    }
    
    // Wait until all the signals are computed then remove signals
    // with a duration shorter than `time_slices_over_threshold`
    __syncthreads();
    if (thid == 0) {
        if (time_slices_over_threshold <= 1) return;
        int i = 0;
        while (i < time_window_size) {
            if (output_signal[bid*time_window_size+i] < 0.5f) {
                i += 1;
                continue;
            }
            int k = 1;
            while (i+k<time_window_size && output_signal[bid*time_window_size+i+k] > 0.0f) 
                k += 1;
            if (k < time_slices_over_threshold) {
                for (int j=i; j<i+k; j++)
                    output_signal[bid*time_window_size+j] = 0.0f;
            }
            i += k;
        }
    }
}


/**
 * @brief Counts the number of rising edges (pixel triggers) in a discriminator signal.
 *
 * This kernel function takes an array of signals and counts the number of times
 * the signal crosses a threshold (0.5) from below to above, indicating a rising edge
 * or pixel trigger.  It operates on a per-pixel basis, processing a window of
 * the signal for each pixel. The kernel assumes ideal rising edges with negligible rising time.
 *
 * @param counts An output array of integers, where the count of rising edges for
 *               each pixel will be stored.  This array should have a size of
 *               `n_pixels`.  The counts are added to the existing values in
 *               this array.
 * @param signals A constant input array of floats representing the signals for
 *                each pixel. This array should contain ``n_pixels`` X ``window_size`` 
 *                elements, where each pixel signal occupies a contiguous block 
 *                of ``window_size`` elements.
 * @param window_size An integer representing the size of the window for each pixel signal.
 * @param n_pixels An integer representing the number of pixels to process.
 *
*/
__global__ void count_pixel_triggers(
    int* counts,
    const float* signals,
    int window_size,
    int n_pixels
)
{
    int bid = blockIdx.x;
    if (bid >= n_pixels) return;
    
    // Current thread
    int thid = threadIdx.x;

    // Initialize shared memory where to store the temporary pixel trigger signal
    // and number of rising edge found by each thread.
    // Rising edge are assumed ideal and with 0 rising time.
    extern __shared__ float shared_buffer[]; // 4*(window_size+blockDim.x) bytes
    float* pixel_trigger = shared_buffer;
    int* tmp_counts = (int*)&pixel_trigger[window_size];
    tmp_counts[thid] = 0;
    
    if (thid < window_size) {
        // Reduce number of threads depending on the window size
        // At least one thread per time-bin
        int n_threads = min(window_size, blockDim.x);
        
        // Sub-window extrema for each thread
        int extrema[2];
        get_interval(extrema, thid, n_threads, window_size);
        if (extrema[0] == extrema[1]) return;

        // Initialize thread counts and shared signal
        
        for (int i=extrema[0]; i<extrema[1]; i++) {
            pixel_trigger[i] = signals[bid*window_size + i];
        }
        __syncthreads();

        // Check for rising edges
        for (int i=extrema[0]; i<extrema[1]; i++) {
            if (i == 0) continue;
            if ((pixel_trigger[i-1]<0.5f) && (pixel_trigger[i]>0.5f)) tmp_counts[thid] += 1;
        }
    
    } // thid < windows_size

    // Sync all threads and sum all counts
    __syncthreads();
    for (unsigned int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (thid < s) {
            tmp_counts[thid] += tmp_counts[thid + s];
        }
        __syncthreads();
    }

    // Update global count
    if (thid==0) counts[bid] += tmp_counts[0];
}

/**
 * @brief Counts clock cycles between the last pixel trigger and the camera trigger.
 * 
 * This function simulates a time-to-digital converter (TDC) counter to measure the time
 * between the last trigger of each pixel and the camera trigger.
 *
 * The trigger time for each pixel is determined by counting the number of clock cycles
 * (time bins) between the camera trigger and the last rising edge of the pixel
 * discriminator signal. The counting starts from the beginning of the window and continues 
 * up to ``stop_clock`` cycles after the camera trigger clock ``camera_trigger_time_index``.
 *
 * The result, representing the time difference, is stored as an integer in an array
 * that emulates a register with ``register_n_bits`` bits (maximum of 32).
 *
 * @param trigger_times Output array of integers. Stores the calculated trigger times for each pixel.
 *                      The size of this array should be equal to `n_pixels`.  Each element
 *                      represents the time difference in clock cycles, mapped to the range
 *                      of the `register_n_bits`-bit register.  A value of 0 indicates no trigger
 *                      was found within the search window. A value of ``(2^register_n_bits) - 1``
 *                      indicates an overflow.
 * @param signals Input array of floats representing the discriminator signals for each pixel.
 *                The size of this array should be ``n_pixels * window_size``. The signal for
 *                pixel `i` is stored in `signals[i * window_size]` to `signals[(i + 1) * window_size - 1]`.
 *                A rising edge (transition from < 0.5 to > 0.5) indicates a trigger.
 * @param camera_trigger_time_index Integer representing the clock cycle index at which the camera
 *                                  trigger occurs. This serves as the reference time (time 0+2^(register_n_bits-1)))
 *                                  for all pixel trigger time calculations.
 * @param stop_clock Integer representing the number of clock cycles after the camera trigger
 *                   during which the function will search for pixel triggers. The search window
 *                   for each pixel is from `camera_trigger_time_index` to
 *                   `camera_trigger_time_index + stop_clock`.
 * @param register_n_bits Integer representing the number of bits in the simulated TDC register.
 *                        This determines the range of values that can be stored in `trigger_times`.
 *                        Valid values are between 1 and 32 (inclusive).
 * @param window_size Integer representing the number of time bins in the discriminator signal
 *                    for each pixel.
 * @param n_pixels Integer representing the total number of pixels.
 *
 * @note - The function assumes ideal rising edges with a negligible rise time (<<clock).
 *       
 *       - The function uses shared memory for inter-thread communication within a block.
 *       
 *       -The size of the shared memory required is ``4 * (window_size + blockDim.x)`` bytes.
 */
__global__ void last_trigger_time_counter_from_camera_trigger(
    int* trigger_times,
    const float* signals,
    int camera_trigger_time_index,
    int stop_clock,
    int register_n_bits,
    int window_size,
    int n_pixels
)
{
    int bid = blockIdx.x;
    if (bid >= n_pixels) return;
    
    // Current thread
    int thid = threadIdx.x;

    // Initialize shared memory where to store the temporary pixel trigger signal
    // and number of rising edge found by each thread.
    // Rising edge are assumed ideal and with 0 rising time.
    extern __shared__ float shared_buffer[]; // 4*(window_size+blockDim.x) bytes
    float* pixel_trigger = shared_buffer;
    int* tmp_times = (int*)&pixel_trigger[window_size];
    tmp_times[thid] = -1;
    
    if (thid < window_size) {
        // Reduce number of threads depending on the window size
        // At least one thread per time-bin
        int n_threads = min(window_size, blockDim.x);
        
        // Sub-window extrema for each thread
        int extrema[2];
        get_interval(extrema, thid, n_threads, window_size);
        if (extrema[0] == extrema[1]) return;

        // Initialize shared signal
        for (int i=extrema[0]; i<extrema[1]; i++) {
            if (i > camera_trigger_time_index + stop_clock) {
                pixel_trigger[i] = 0.f;
            }
            else {
                pixel_trigger[i] = signals[bid*window_size + i];
            }
        }
        __syncthreads();

        // Check for rising edges
        for (int i=extrema[0]; i<extrema[1]; i++) {
            if (i == 0) continue;
            if ((pixel_trigger[i-1]<0.5f) && (pixel_trigger[i]>0.5f)) {
                tmp_times[thid] = i;
            }
        }
        __syncthreads();
    
    } // thid < windows_size

    // Find the global maximum within the block
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (thid < s) {
            if (tmp_times[thid] < tmp_times[thid + s]) {
                tmp_times[thid] = tmp_times[thid + s];
            }
        }
        __syncthreads();
    }
    
    // Thread 0 writes the final results back to global memory
    if (thid == 0) {
        if (tmp_times[thid] > -1) {
            int half_extent = 1 << register_n_bits-1;
            int max_extent = 1 << register_n_bits;
            int dt = tmp_times[0] - camera_trigger_time_index;
            if ((dt < -half_extent) || (dt >= half_extent)) {
                trigger_times[bid] = max_extent-1;
            }
            else {
                trigger_times[bid] = dt + half_extent;
            }
        }
        else {
            trigger_times[bid] = 0;
        }
    }
}

} // extern "C"