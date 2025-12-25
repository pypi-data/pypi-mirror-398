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
// __device__ new_neighbors                                     //
// __device__ contiguous                                        //
// __device__ module_topological_trigger                        //
// __device__ topological_trigger_signals                       //
//                                                              //
////// Kernels                                                  //
//                                                              //
// __global__ topological_camera_trigger                        //
// __global__ count_topological_camera_triggers                 //
//                                                              //
//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////

#include <cooperative_groups.h>
#include <limits.h> 
#include <curand_kernel.h>

namespace cg = cooperative_groups;

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
__device__ void get_interval(
    int* extrema,
    int thid,
    int n_threads,
    int width
) 
{
    int size_per_thread = (width + n_threads -1) / n_threads;
    extrema[0] = min(width, __mul24(size_per_thread,thid));
    extrema[1] = min(width, __mul24(size_per_thread,thid+1));
}

/**
 * @brief Finds neighboring triggered pixels and adds them to a frontier array.
 * 
 * This function examines the 3x3 neighborhood around a given pixel in a 2D grid (representing a square SiPM tile)
 * and identifies triggered neighbors. It updates a frontier array to mark discovered pixels and maintains
 * a count of contiguous triggered pixels.
 *
 * @param pixel The linear index of the current pixel within the 2D grid (0 to `dimension`*`dimension` - 1).
 * @param module_disc A flattened 2D array (`dimension` x `dimension`) of floats representing the discriminator values for each pixel.
 *                 A value greater than 0.5 indicates the pixel is triggered.
 * @param frontier A flattened 2D array (`dimension` x `dimension`) of integers acting as a boolean mask.
 *                 0 indicates the pixel has not been found/processed, 1 indicates it has been found.
 * @param neighbors An array of size 9 to store the linear indices of triggered neighboring pixels. Initialized with -1.
 * @param count A pointer to an integer storing the total count of contiguous triggered pixels found so far.
 *              This is passed as a pointer to allow modification within the recursive calls.
 * @param dimension The dimension of the SiPM tile (assuming a square tile, `dimension` x `dimension`).
 */
__device__ void new_neighbors(
    int pixel,
    const float* module_disc,
    int* frontier,
    int* neighbors,
    int* count,
    int dimension
)
{   
    // Pixel row on the 8x8 module
    int row = pixel / dimension;
    
    // Border aware 3x3 window
    int jmin = max(row*dimension, pixel-1);
    int jmax = min((row+1)*dimension-1, pixel+1);
    int start;
    int end;
    if (row == 0) {
        start = 0;
        end = dimension;
    }
    else if (row == dimension-1) {
        start = -dimension;
        end = 0;
    }
    else {
        start = -dimension;
        end = dimension;
    }
    
    // If the central pixel is triggered add it to the frontier
    if (module_disc[pixel] > 0.5f) {
        frontier[pixel] = 1;
    }
    else return;
    
    // Count new neighbors looping over the window
    int n = 0;
    for (int j=jmin; j<=jmax; j++) {
        for (int i=j+start; i<=j+end; i=i+dimension) {
            // Skip the current pixel
            if (i == pixel) continue;
            // If the neighbor is triggered...
            if (module_disc[i] > 0.5f)
            {
                // ... check if it's new
                if (frontier[i] < 1) 
                {
                    // If it's new update the frontier, the new neighbors count and the neighbors list
                    frontier[i] = 1;
                    neighbors[n++] = i;
                }
            }
        }
    }
    // Update the total count of contiguous pixels
    count[0] += n;
}

// TODO: try to write a non-recursive implementation

/**
 * @brief Recursively finds contiguous triggered pixels in a 2D grid.
 *
 * This function implements a depth-first search to identify groups of contiguous
 * pixels that are triggered. It starts from a single triggered pixel and recursively 
 * explores its neighbors, marking visited triggered pixels in a frontier array.
 *
 * @param pixel The linear index of the starting pixel (0 to dimension*dimension - 1).
 * @param module_disc A flattened 2D array (dimension x dimension) of floats representing the discriminator values.
 *                 A value greater than 0.5 indicates the pixel is triggered.
 * @param frontier A flattened 2D array (dimension x dimension) of integers used as a boolean mask.
 *                 0: pixel not yet visited or not triggered, 1: pixel visited and triggered.
 * @param count A pointer to an integer storing the total count of contiguous triggered pixels found.
 *              It's initialized to 1 outside this function, representing the starting pixel.
 * @param n_min The minimum number of contiguous pixels required to form a valid group. The search stops early if this requirement is met.
 * @param dimension The dimension of the SiPM tile (assuming a square tile, `dimension` x `dimension`).
 */
__device__ void contiguous(
    int pixel,
    const float* module_disc,
    int* frontier,
    int* count,
    int n_min,
    int dimension
)
{
    // Init the neighbors list with negative indices
    int neighbors[9] = {-1,-1,-1,-1,-1,-1,-1,-1,-1};

    // Find `pixel` neighbors and update the frontier
    new_neighbors(pixel, module_disc, frontier, neighbors, count, dimension);

    // Return if enough contiguous pixels have been found
    if (count[0] > n_min) return;
    
    // Repeat for each new neighbor updating the same frontier (i.e. find a group of contiguous)
    for (int i=0; i<9; i++)
    {
        if (neighbors[i]>-1) contiguous(neighbors[i], module_disc, frontier, count, n_min, dimension);
    }
}

/**
 * @brief Determines if a module trigger condition is met based on contiguous triggered pixels.
 *
 * This function checks if there is a group of contiguous triggered pixels within a 2D grid (representing the SiPM tile within the module)
 * that meets a specified size threshold (`n_contiguous`). It avoids redundant checks by marking pixels belonging to
 * already-examined groups. The SiPM tile is square and composed of `dimension`*`dimension` number of pixels.
 *
 * @param module_disc A flattened 2D array (`dimension` x `dimension`, e.g. 8x8=64) of floats representing the discriminator
 *                 values for each pixel on the SiPM tile. A value greater than 0.5 indicates the pixel is triggered.
 * @param n_contiguous The minimum number of contiguous triggered pixels required to generate a trigger signal.
 * @param dimension The dimension of the SiPM tile (assuming a square tile, `dimension` x `dimension`).
 *
 * @return `true` if a group of at least `n_contiguous` adjacent pixels are triggered (value > 0.5) in `module_disc`; `false` if no such group is found.
 */
__device__ bool module_topological_trigger(
    float* module_disc,
    int n_contiguous,
    int dimension
)
{
    int n_pixels = dimension*dimension;
    // Check number of contiguous triggered pixels for each triggered pixel.
    // If a group is found but does not fulfill trigger condition
    // each pixel of the group is marked as `checked`,
    // in this way 'contiguous' will not be re-called 
    // on the same group more than once.

    // Where to keep track of the checked pixels
    // (assuming there are no SiPM tiles with more than 128 pixels)
    bool checked[128];
    for (int k=0; k<n_pixels; k++) 
        checked[k] = false;
    
    // Where to flag pixels of groups
    // (assuming there are no SiPM tiles with more than 128 pixels)
    int frontier[128];

    // Loop over all pixels
    for (int i=0; i<n_pixels; i++){
        // Check this pixel if is triggered and has not been checked
        if (module_disc[i] > 0.5f & checked[i] == false) {
            // Empty the frontier
            for (int k=0; k<n_pixels; k++) 
                frontier[k] = 0;
            // Start the group counter
            int count[1] = {1};
            // Find the group size
            contiguous(i, module_disc, frontier, count, n_contiguous, dimension);
            // If there are enough pixels in the group raise a module trigger
            if (count[0] >= n_contiguous) {
                return true;
            }
            // Otherwise mark all the pixels in the group as checked
            else {
                for (int k=0; k<n_pixels; k++) {
                    if (frontier[k] > 0) checked[k] = true;
                }
            }
        }
    }
    return false;
}

/**
 * @brief Computes module trigger signals based on a topological trigger condition within a time window.
 *
 * This function processes discriminator signals from a module over a specified time window
 * and generates a module-level trigger signal based on the `module_topological_trigger` function.  It operates on a per-block
 * basis, where each block corresponds to a single module. It then identifies the first time slice within the window
 * where a module trigger occurs.
 *
 * @param disc_signals A flattened 3D array representing discriminator signals. The dimensions are implicitly
 *                     [number of modules] x [number of pixels per module] x [window_size].  This array contains
 *                     the raw discriminator outputs for each pixel of each module over the entire time window.
 * @param n_contiguous The minimum number of contiguous triggered pixels required to trigger the topological trigger.
 * @param module_trigger_signals Output array for the module trigger signals.  Dimensions are [number of modules] x [window_size].
 *                           A value of 1.0 indicates a trigger, and 0.0 indicates no trigger for a given module at a given time slice.
 * @param trigger_t_idices Output array to store the index of the first time slice within the window where a module trigger occurs.
 *                        Dimensions are [number of modules]. A value of -1 indicates no trigger was found within the window for that module.
 * @param window_size The size of the time window being processed.
 * @param module_dimension The dimension of the square SiPM tile within the module (e.g., 8 for an 8x8 tile).
 * @param block A `cg::thread_block` object representing the current thread block.  Used for thread synchronization and block-level operations.
 */
__device__ void topological_trigger_signals(
    float* disc_signals,
    int n_contiguous,
    float* module_trigger_signals,
    int* trigger_t_idices,
    int window_size,
    int module_dimension,
    const cg::thread_block &block
)
{
    const int n_module_pix = module_dimension*module_dimension; // Number of pixels in a module
    
    // A block for each module
    int bid = blockIdx.x;
    
    // Current thread
    int thid = block.thread_rank();
    
    // Number of threads that will compute the module trigger signal
    int n_threads = blockDim.x;
 
    // Sub-window extrema of each thread
    int extrema[2];
    get_interval(extrema, thid, n_threads, window_size);

    for (int i=extrema[0]; i<extrema[1]; i++) {
        // Get all pixels trigger signal at the i-th time-slice
        // (assuming there are no SiPM tiles with more than 128 pixels)
        float module_disc[128];
        for (int k=0; k<n_module_pix; k++){
            module_disc[k] = disc_signals[n_module_pix*blockIdx.x*window_size + window_size*k + i];
        }
        // Check for a topological trigger
        bool trigger = module_topological_trigger(module_disc, n_contiguous, module_dimension);
        // Set the module trigger signal
        module_trigger_signals[bid*window_size+i] = trigger ? 1.0f : 0.0f;
    }
    
    // Wait until module trigger signal is computed
    cg::sync(block);

    // Get the first time slice with a module trigger
    if (thid == 0) {
        trigger_t_idices[bid] = -1;
        for (int i=0; i<window_size; i++) {
            if (module_trigger_signals[bid*window_size+i] > 0.5f) {
                trigger_t_idices[bid] = i;
                break;
            }
        }
    }
}

/**
 * @brief This kernel processes discriminators signals to generate a camera trigger based on a topological condition for a modular SiPM camera.
 *
 * It operates in two main stages:
 * 
 * 1. Calls `topological_trigger_signals` to compute trigger signals for each module and identify the time indices where the first trigger occurs.
 * 2. Synchronizes all blocks in the grid and then, on a single thread, determines the earliest module trigger across all modules. 
 *    This earliest trigger is used to generate the camera trigger signal.
 *
 * @param disc_signals A flattened 3D array representing discriminator signals. The dimensions are
 *                     [number of modules] x [number of pixels per module] x [window_size].  This array contains
 *                     the raw discriminator outputs for each pixel of each module over the entire time window.
 * @param n_contiguous Integer representing the number of contiguous time samples for each module in `disc_signals`.
 * @param module_trigger_signals Output array to store the computed trigger signals for each module. 
 *                            It should have the same size as `disc_signals`.
 * @param trigger_t_idices Output array to store the time indices of the first trigger found for each module. 
 *                         A value of -1 indicates no trigger was found for that module.
 *                         Should be allocated once and not intialized (it is internally initialized at each call). It should have a size equal to the number of modules.
 * @param trigger Output array of size 2. 
 *                `trigger[0]` will store the time index of the camera trigger (the earliest module trigger).
 *                `trigger[1]` will store the module number (1-based index) that generated the camera trigger.
 *                 If no trigger is generated across all modules, trigger[0] is -1 and trigger[1] is 0.
 * @param window_size The size of the sliding window used in the topological clustering algorithm within `topological_trigger_signals`.
 * @param module_dimension The dimension of the square SiPM tile within the module (e.g., 8 for an 8x8 tile).
 * 
 * @note
 * This kernel can be used only on 2D sector with a NxN layout. Let say that the discriminator signals of a 4X4 SiPM tile are summed in groups of four, generating a 2X2 sectors matrix. 
 * You can apply this kernel to the [number of modules] x [number of sectors per module (i.e. 4)] x [window_size] signals with `module_dimension` set to 2.
 * 
 */
__global__ void topological_camera_trigger(
    float* disc_signals,
    int n_contiguous,
    float* module_trigger_signals,
    int* trigger_t_idices,
    int* trigger,
    int window_size,
    int module_dimension,
    int n_modules,
    long long int seed
)
{
    // Handle to thread block group
    cg::thread_block block = cg::this_thread_block();
    cg::grid_group grid = cg::this_grid();
    
    // Compute module trigger signals and get modules trigger time slice
    topological_trigger_signals(disc_signals, n_contiguous, module_trigger_signals, trigger_t_idices, window_size, module_dimension, block);

    // Wait until all modules are processed
    cg::sync(grid);
    
    // Find the first module trigger (which will generate a camera trigger)
    if (grid.thread_rank() == 0) {
        // Start from a random module
        // otherwise the result will be biased
        // in a high-background situation
        curandStatePhilox4_32_10_t state;
        curand_init(seed, 0, 0, &state);
        int start_module = curand(&state) % n_modules;

        int min_index = INT_MAX;
        int module_triggered = -1;
        for (int k=0; k<n_modules; k++) {
            int i = (start_module+k) % n_modules;
            int tr_index = trigger_t_idices[i];
            if (tr_index > -1 & tr_index < min_index) {
                min_index = tr_index;
                module_triggered = i;
            }
        }
        if (module_triggered == -1) {
            trigger[0] = -1;
            trigger[1] = 0;
        }
        else {
            trigger[0] = min_index;
            trigger[1] = module_triggered;
        }
    }
}

/**
 * @brief Counts the number of camera triggers within a time window.
 *
 * This kernel processes trigger signals from modules to count the number of camera triggers. 
 * The function identifies camera triggers by appling an OR to modules trigger signals. 
 * It then counts the rising edges of the resulting camera trigger signal.
 *
 * It operates on a single block of threads and uses shared memory to
 * optimize the computation. 
 * 
 * @param counts Pointer to an integer where the total number of detected camera triggers will be stored.
 *               This is updated atomically across kernel launches and should be initialized to 0.
 * @param signals Pointer to the array of modules trigger signals. The data is organized such that 
 *                all time samples for module 0 are contiguous, followed by all time samples for module 1, and so on.
 * @param window_size The size of the time window over which trigger signals are defined.
 * @param n_modules The number of modules.
 *
 * @warning
 *   1. The required shared memory is `4 * (window_size + blockDim.x)` bytes.
 *   2. Assumes ideal rising edges with zero rising time, meaning we check for transitions from <= 0.5 to > 0.5.
 * 
*/
__global__ void count_topological_camera_triggers(
    int* counts,
    const float* signals,
    int window_size,
    int n_modules
)
{
    // Single block
    if (blockIdx.x > 0) return;
    
    // Current thread
    int thid = threadIdx.x;

    // Initialize shared memory where to store the temporary camera trigger signal
    // and number of rising edge found by each thread.
    // Rising edge are assumed ideal and with 0 rising time.
    extern __shared__ float shared_buffer[]; // 4*(window_size+blockDim.x) bytes
    float* camera_trigger = shared_buffer;
    int* tmp_counts = (int*)&camera_trigger[window_size];

    if (thid < window_size) {
        // Initialize thread counts
        tmp_counts[thid] = 0;
        
        // Reduce number of threads depending on the window size
        // At least one thread per time-bin
        int n_threads = min(window_size, blockDim.x);
        
        // Sub-window extrema for each thread
        int extrema[2];
        get_interval(extrema, thid, n_threads, window_size);
        if (extrema[0] == extrema[1]) return;

        // Compute camera trigger
        for (int i=extrema[0]; i<extrema[1]; i++) {
            camera_trigger[i] = 0.f;
            // Check if at least a module is triggered
            for (int j=0; j<n_modules; j++) {
                if (signals[j*window_size+i] > 0.5f) {
                    camera_trigger[i] = 1.f;
                    break;
                }
            }
        }
        // Wait until each thread has generated its camera trigger
        __syncthreads();

        // Check for rising edges
        // (sync is necessary since we are looking in others thread windows)
        for (int i=extrema[0]; i<extrema[1]; i++) {
            if (i == 0) continue;
            if ((camera_trigger[i-1]<0.5f) && (camera_trigger[i]>0.5f)) tmp_counts[thid] += 1;
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
    if (thid==0) counts[0] += tmp_counts[0];
}

} // extern "C"