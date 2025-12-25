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

#include <vector>
#include <cstring>
#include <iostream>
#include <regex>
#include <cstdint>
#include <memory>
#include <sstream>
#include <filesystem>
#include <fstream>
#include <zlib.h>
#include <stdexcept>
#include <type_traits>
#include <cassert>
#include <algorithm>
#include <cmath>

#ifdef USE_LIBZSTD
    #define ZSTD_STATIC_LINKING_ONLY
    #include <zstd.h>
#endif

#ifdef USE_OPENMP
    #include <omp.h>
#endif

namespace iactxx::eventio 
{

///////////////////////////////
// Structs and types
///////////////////////////////

using u8 = uint8_t;
using u16 = uint16_t;
using u32 = uint32_t;
using u64 = uint64_t;
using i16 = int16_t;
using i32 = int32_t;
using i64 = int64_t;
using f32 = float;

/**
 * @brief Uninitialized uint8_t
 * Allows saving time when initializing a std::vector whose elements are going to be overwritten.
 * Particulary useful for load_file() and decompress_gzip_file().
 * 
 * Adapted from https://mmore500.com/2019/12/11/uninitialized-char.html
 * 
 */
struct uu8 {
    uint8_t val;

    // Default constructor (leaves val uninitialized)
    uu8() { ;/* leaves val uninitialized */ }

    // Constructor from uint8_t
    explicit uu8(uint8_t v) : val(v) {} // Initializes val

    // Assignment operator from uint8_t
    uu8& operator=(uint8_t v) {
        val = v;
        return *this;
    }

    // Conversion to uint8_t
    operator uint8_t() const { return val; }
};

/**
 * @brief Object header.
 * 
 */
struct ObjectHeader
{
    u64 length;
    u64 address;
    u32 marker;
    u32 id;
    u16 type;
    u16 version;
    u16 header_size;
    bool only_sub_objects;
    bool extended;
};

/**
 * @brief Event header struct.
 * 
 * @note Fields are defined in ``event_header.h``
 * 
 */
struct EventHeader {
    char event_header[4];
    f32 event_number;
    f32 particle_id;
    f32 total_energy;
    f32 starting_altitude;
    f32 first_target_id;
    f32 first_interaction_height;
    f32 momentum_x;
    f32 momentum_y;
    f32 momentum_minus_z;
    f32 zenith;
    f32 azimuth;
    f32 n_random_sequences;
    f32 random_seeds[10][3];
    f32 run_number;
    f32 date;
    f32 version;
    f32 n_observation_levels;
    f32 observation_height[10];
    f32 energy_spectrum_slope;
    f32 energy_min;
    f32 energy_max;
    f32 energy_cutoff_hadrons;
    f32 energy_cutoff_muons;
    f32 energy_cutoff_electrons;
    f32 energy_cutoff_photons;
    f32 nflain;
    f32 nfdif;
    f32 nflpi0;
    f32 nflpif;
    f32 nflche;
    f32 nfragm;
    f32 earth_magnetic_field_x;
    f32 earth_magnetic_field_z;
    f32 egs4_flag;
    f32 nkg_flag;
    f32 low_energy_hadron_model;
    f32 high_energy_hadron_model;
    f32 cerenkov_flag;
    f32 neutrino_flag;
    f32 curved_flag;
    f32 computer;
    f32 theta_min;
    f32 theta_max;
    f32 phi_min;
    f32 phi_max;
    f32 cherenkov_bunch_size;
    f32 n_cherenkov_detectors_x;
    f32 n_cherenkov_detectors_y;
    f32 cherenkov_detector_grid_spacing_x;
    f32 cherenkov_detector_grid_spacing_y;
    f32 cherenkov_detector_length_x;
    f32 cherenkov_detector_length_y;
    f32 cherenkov_output_flag;
    f32 angle_array_x_magnetic_north;
    f32 additional_muon_information_flag;
    f32 egs4_multpliple_scattering_step_length_factor;
    f32 cherenkov_wavelength_min;
    f32 cherenkov_wavelength_max;
    f32 n_reuse;
    f32 reuse_x[20];
    f32 reuse_y[20];
    f32 sybill_interaction_flag;
    f32 sybill_cross_section_flag;
    f32 qgsjet_interaction_flag;
    f32 qgsjet_cross_section_flag;
    f32 dpmjet_interaction_flag;
    f32 dpmjet_cross_section_flag;
    f32 venus_nexus_epos_cross_section_flag;
    f32 muon_multiple_scattering_flag;
    f32 nkg_radial_distribution_range;
    f32 energy_fraction_if_thinning_level_hadronic;
    f32 energy_fraction_if_thinning_level_em;
    f32 actual_weight_limit_thinning_hadronic;
    f32 actual_weight_limit_thinning_em;
    f32 max_radius_radial_thinning_cutting;
    f32 viewcone_inner_angle;
    f32 viewcone_outer_angle;
    f32 transition_energy_low_high_energy_model;
    f32 skimming_incidence_flag;
    f32 horizontal_shower_exis_altitude;
    f32 starting_height;
    f32 explicit_charm_generation_flag;
    f32 electromagnetic_subshower_hadronic_origin_output_flag;
    f32 conex_min_vertical_depth;
    f32 conex_high_energy_treshold_hadrons;
    f32 conex_high_energy_treshold_muons;
    f32 conex_high_energy_treshold_em;
    f32 conex_low_energy_treshold_hadrons;
    f32 conex_low_energy_treshold_muons;
    f32 conex_low_energy_treshold_em;
    f32 observaton_level_curvature_flag;
    f32 conex_weight_limit_thinning_hadronic;
    f32 conex_weight_limit_thinning_em;
    f32 conex_weight_limit_sampling_hadronic;
    f32 conex_weight_limit_sampling_muons;
    f32 conex_weight_limit_sampling_em;
    f32 augerhit_stripes_half_width;
    f32 augerhit_detector_distance;
    f32 augerhit_reserved;
    f32 n_multithin;
    f32 multithin_energy_fraction_hadronic[6];
    f32 multithin_weight_limit_hadronic[6];
    f32 multithin_energy_fraction_em[6];
    f32 multithin_weight_limit_em[6];
    f32 multithin_random_seeds[6][3];
    f32 icecube_energy_threshold;
    f32 icecube_gzip_flag;
    f32 icecube_pipe_flag;
};

// Check padding
constexpr std::size_t EXPECTED_EVENT_HEADER_SIZE = 888;
static_assert(
    sizeof(EventHeader) == EXPECTED_EVENT_HEADER_SIZE,
    "Size of EventHeader struct is not as expected. Check packing/padding. "
);

template<typename TTelData>
struct TelescopeDefinition {
    TTelData x;
    TTelData y;
    TTelData z;
    TTelData r;
};

/**
 * @brief Bunch position.
 * 
 * @tparam T Data type.
 */
template <typename T> 
struct BunchPosition { 
    T x;
    T y;
    T z;
};

/**
 * @brief Bunch direction.
 * 
 * @tparam T Data type.
 */
template <typename T> 
struct BunchDirection { 
    T cx;
    T cy;
    T cz;
};

// TODO: use explicit names
/**
 * @brief Bunches data.
 * 
 * @tparam T Data type.
 */
template <typename T> 
class Bunches {
    public:
        u32 n_bunches;
        std::unique_ptr<BunchPosition<T>[]> pos;
        std::unique_ptr<BunchDirection<T>[]> dir;
        std::unique_ptr<T[]> time;
        std::unique_ptr<T[]> zem;
        std::unique_ptr<T[]> photons;
        std::unique_ptr<T[]> wavelength;

        // Special member functions
        Bunches() = default;
        explicit Bunches(int size)
        {
            n_bunches = size;
            pos.reset(new BunchPosition<T>[size]);
            dir.reset(new BunchDirection<T>[size]);
            time.reset(new T[size]);
            zem.reset(new T[size]);
            photons.reset(new T[size]);
            wavelength.reset(new T[size]);
        };
        Bunches(const Bunches &other) // Required by unique_ptr
        {
            *this = other;
        }
        Bunches& operator=(const Bunches<T> &other) // Required by unique_ptr
        {
            if (this != &other) copy(other);
            return *this;
        }
        Bunches(Bunches&& other) = default;
        Bunches& operator=(Bunches&& other) = default;
        ~Bunches() = default;
    
    private:
        inline void copy(const Bunches<T> &other) {
            n_bunches = other.n_bunches;

            pos = std::make_unique<BunchPosition<T>[]>(n_bunches);
            std::copy_n(other.pos.get(), n_bunches, pos.get());

            dir = std::make_unique<BunchDirection<T>[]>(n_bunches);
            std::copy_n(other.dir.get(), n_bunches, dir.get());

            time = std::make_unique<T[]>(n_bunches);
            std::copy_n(other.time.get(), n_bunches, time.get());

            zem = std::make_unique<T[]>(n_bunches);
            std::copy_n(other.zem.get(), n_bunches, zem.get());

            photons = std::make_unique<T[]>(n_bunches);
            std::copy_n(other.photons.get(), n_bunches, photons.get());

            wavelength = std::make_unique<T[]>(n_bunches);
            std::copy_n(other.wavelength.get(), n_bunches, wavelength.get());
        }
};

// eventio object idenfiers
constexpr u16 RUN_HEADER{1200};
constexpr u16 TELESCOPE_DEFINITION{1201};
constexpr u16 EVENT_HEADER{1202};
constexpr u16 TELESCOPE_DATA{1204};
constexpr u16 PHOTONS{1205};
constexpr u16 EVENT_END{1209};
constexpr u16 RUN_END{1210};
constexpr u16 INPUT_CARD{1212};
constexpr u16 NONE{0};
constexpr u64 MARKER{3558836791};

///////////////////////////////
// Bits manipulation
///////////////////////////////

/**
 * @brief Check if a type is an unsigned integer at compile time.
 * 
 * @tparam T type to be checked.
 */
template <typename T>
constexpr bool is_unsigned_integer = std::is_integral_v<T> && std::is_unsigned_v<T>;

/**
 * @brief Unpack bits of an unsigned integer.
 * 
 * @tparam Tuint Unsigned integer type.
 * @param value Unsigned integer value.
 * @return u8* Unpacked bits.
 */
template<typename Tuint>
static inline u8* unpack_unisgned(const Tuint& value)
{
    static_assert(is_unsigned_integer<Tuint>, "Template argument must be an unsigned integer type.");

    constexpr int n_bits = sizeof(Tuint)*8;
    u8* bits[n_bits];
    for (int i=0; i<n_bits; ++i) {
        bits[i] = (value & (Tuint(1) << i)) == (Tuint(1) << i);
    }
    return bits;
}

/**
 * @brief Convert from bits to unsigned integer using an index value and a length value and assuming big-endian bits order.
 * 
 * @tparam Tuint Type of the output unisgned integer.
 * @param bits Array of bits.
 * @param start First bit.
 * @param nbit Number of bits.
 * @return Tuint Converted unsigned integer value.
 */
template<typename Tuint>
static inline Tuint 
bits_to_unsigned(
    const u8* bits,
    const int start,
    const int nbit
)
{
  static_assert(is_unsigned_integer<Tuint>, "Template argument must be an unsigned integer type.");

  Tuint value{0};
  int end = start + nbit;
  for (int i=start; i<end; ++i) 
    value += (bits[i] << i);
  return value;
}

/**
 * @brief Extracts bits from an unsigned integer using an index value and a length value.
 * The extracted bits start from the least significant bit and all higher order bits are zeroed.
 * 
 * @tparam TExtr Return type of the extracted bits.
 * @tparam TSource Input type
 * @param src Unsigned integer from which extract bits
 * @param start Index of the first bit to be extracted
 * @param len Number of bits to be extracted
 * @return TExtr Extracted bits.
 */
template<typename TExtr, typename TSource>
static inline TExtr 
extract_bits_usigned(
    const TSource& src,
    const int start,
    const int len
)
{
    return static_cast<TExtr>((src >> start) & ((1 << len) - 1));
}

/**
 * @brief Extracts bits from an unsigned integer using an index value and a length value and store the result.
 * The extracted bits are written to the destination starting from the least significant bit. All higher order bits in the result are zeroed.
 * 
 * @tparam Tdest Destination type
 * @tparam Tuint Input type
 * @param src Unsigned integer from which extract bits
 * @param dest Where to store the extracted bits
 * @param start Index of the first bit to be extracted
 * @param len Number of bits to be extracted
 */
template<typename Tdest, typename Tuint>
static inline void
extract_bits_usigned(
    const Tuint& src,
    Tdest& dest,
    const int start,
    const int len
)
{
    static_assert(is_unsigned_integer<Tuint>, "Template argument must be an unsigned integer type.");

    dest = (src >> start) & ((1 << len) - 1);
}

/**
 * @brief Extract a bit as a boolean value from an unsigned integer.
 * 
 * @tparam Tuint Unsigned integer type.
 * @param src Unsigned integer value.
 * @param position Position of the bit.
 * @return bool 
 */
template<typename Tuint>
static inline bool
bool_from_bit(
    Tuint& src,
    const int position
)
{ 
    static_assert(is_unsigned_integer<Tuint>, "Template argument must be an unsigned integer type.");

    // 0 (i.e. the bit is 0) is converted to false,
    // any other value (i.e. the bit is 1) is converted to true
    return src & (1 << position);
}

///////////////////////////////
// eventio decoding
///////////////////////////////

/**
 * @brief Parse an object header.
 * 
 * @tparam Corsika fila data type.
 * @param obj ObjectHeader where to store info.
 * @param data Corsika file data array.
 * @param position Header position inside data array.
 */
template<typename T>
static inline void 
decode_object_header(
    ObjectHeader& obj,
    T& data,
    const size_t position
)
{
    u16 buffer16;
    u64 buffer64;

    // Bytes 0-3 
    u32 first_4byte;
    memcpy(&first_4byte, &data[position], 4);
    
    size_t off = 0;

    // Main object
    if (first_4byte == MARKER) {
        obj.header_size = 16;
        obj.marker = first_4byte;
        
        //// Next four bytes
        // Bytes 4-5
        memcpy(&obj.type, &data[position+4], 2);
        //
        // Bits 4-15 of the bytes 6-7
        memcpy(&buffer16, &data[position+6], 2);
        obj.version = extract_bits_usigned<u16>(buffer16, 4, 11);
        obj.extended = bool_from_bit(buffer16, 1);
    
    // Sub-object
    } else {
        obj.marker = 0;
        obj.header_size = 12;
        // First four bytes
        extract_bits_usigned(first_4byte, obj.type, 0, 16);
        obj.extended = bool_from_bit(first_4byte, 17);
        extract_bits_usigned(first_4byte, obj.version, 20, 12);
        off = 4;
    }

    obj.address = position + obj.header_size;

    // Next four bytes
    memcpy(&obj.id, &data[position+8-off], 4);
    
    // Next four bytes
    memcpy(&buffer64, &data[position+12-off], 4);
    extract_bits_usigned(buffer64, obj.length, 0, 30);
    obj.only_sub_objects = bool_from_bit(buffer64, 30);

    // Next four bytes if there is an extention
    if (obj.extended) {
        obj.header_size += 4;
        u64 length_ext;
        // Read length extention into length_ext
        memcpy(&buffer64, &data[position+16-off], 4);
        extract_bits_usigned(buffer64, length_ext, 0, 12);
        // Extend length
        obj.length = obj.length | (length_ext<<30);
    }
}

/**
 * @brief Read compact bunches and store the data in a Bunches object 
 * starting from a certain position. The Bunches object 
 * is not resized and can contain more than a event 
 * (if the Bunches object has been properly resized before).
 * 
 * @tparam T Corsika file data type.
 * @tparam B Bunches data type.
 * @param bunches Bunches struct where to store data.
 * @param index Start index.
 * @param n_bunches Number of bunches to be stored.
 * @param data Corsika file data array.
 * @param position Bunches position inside file-data array.
 * 
 */
template<typename T, typename B>
static inline void 
parse_compact_bunches(
    Bunches<B>& bunches,
    u32 index,
    u32 n_bunches,
    const T& data,
    size_t position
)
{ 
    constexpr size_t BUNCH_RECORD_SIZE = 16;
    constexpr size_t ENTRY_SIZE = 2;
    constexpr size_t POS_X_OFFSET = 12;
    constexpr size_t POS_Y_OFFSET = 14;
    constexpr size_t DIR_X_OFFSET = 16;
    constexpr size_t DIR_Y_OFFSET = 18;
    constexpr size_t TIME_OFFSET = 20;
    constexpr size_t ZEM_OFFSET = 22;
    constexpr size_t PHOTONS_OFFSET = 24;
    constexpr size_t WAVELENGTH_OFFSET = 26;

    constexpr B POS_SCALE = static_cast<B>(0.1);
    constexpr B DIR_SCALE = static_cast<B>(1. / 30000.);
    constexpr B DIR_CLAMP_MIN = static_cast<B>(-1.);
    constexpr B DIR_CLAMP_MAX = static_cast<B>(1.);
    constexpr B TIME_SCALE = static_cast<B>(0.1);
    constexpr B ZEM_EXP_SCALE = static_cast<B>(0.001);
    constexpr B ZEM_BASE = static_cast<B>(10.);
    constexpr B PHOTONS_SCALE = static_cast<B>(0.01);

    const std::byte* base_data_ptr = reinterpret_cast<const std::byte*>(data) + position;

    i16 x, y, cx, cy, time, zem, photons, wavelength;
    u32 end = index + n_bunches;
    u32 k = 0;
    
    for (u32 i=index; i<end; ++i) {
        const std::byte* current_bunch_base_ptr = base_data_ptr + k * BUNCH_RECORD_SIZE;

        // Get bunches from buffer
        std::memcpy(&x,          current_bunch_base_ptr + POS_X_OFFSET,      ENTRY_SIZE);
        std::memcpy(&y,          current_bunch_base_ptr + POS_Y_OFFSET,      ENTRY_SIZE);
        std::memcpy(&cx,         current_bunch_base_ptr + DIR_X_OFFSET,      ENTRY_SIZE);
        std::memcpy(&cy,         current_bunch_base_ptr + DIR_Y_OFFSET,      ENTRY_SIZE);
        std::memcpy(&time,       current_bunch_base_ptr + TIME_OFFSET,       ENTRY_SIZE);
        std::memcpy(&zem,        current_bunch_base_ptr + ZEM_OFFSET,        ENTRY_SIZE);
        std::memcpy(&photons,    current_bunch_base_ptr + PHOTONS_OFFSET,    ENTRY_SIZE);
        std::memcpy(&wavelength, current_bunch_base_ptr + WAVELENGTH_OFFSET, ENTRY_SIZE);

        // Position
        bunches.pos[i].x = static_cast<B>(x) * POS_SCALE;
        bunches.pos[i].y = static_cast<B>(y) * POS_SCALE;

        // Direction
        bunches.dir[i].cx = std::clamp(static_cast<B>(cx) * DIR_SCALE, DIR_CLAMP_MIN, DIR_CLAMP_MAX);
        bunches.dir[i].cy = std::clamp(static_cast<B>(cy) * DIR_SCALE, DIR_CLAMP_MIN, DIR_CLAMP_MAX);

        // Arrival time
        bunches.time[i] = static_cast<B>(time) * TIME_SCALE;

        // Emission altitude
        bunches.zem[i] = std::pow(ZEM_BASE, static_cast<B>(zem) * ZEM_EXP_SCALE);

        // Photons
        bunches.photons[i] = static_cast<B>(photons) * PHOTONS_SCALE;

        // Wavelength
        bunches.wavelength[i] = static_cast<B>(wavelength);

        k += 1;
    }
}

/**
 * @brief Read bunches and store the data in a Bunches object 
 * starting from a certain position. The Bunches object 
 * is not resized and can contain more than a event 
 * (if the Bunches object has been properly resized before).
 * 
 * @tparam T Corsika file data type (u8 or similar).
 * @tparam B Bunches data type.
 * @param bunches Bunches struct where to store data.
 * @param index Start index.
 * @param n_bunches Number of bunches to be stored.
 * @param data Corsika file data array.
 * @param position Bunches position inside file-data array.
 * 
 */
template<typename T, typename B>
static inline void 
parse_bunches(
    Bunches<B>& bunches,
    u32 index,
    u32 n_bunches,
    const T& data,
    size_t position
)
{ 
    constexpr size_t BUNCH_RECORD_SIZE = 32;
    constexpr size_t ENTRY_SIZE = 4;
    constexpr size_t POS_X_OFFSET = 12;
    constexpr size_t POS_Y_OFFSET = 16;
    constexpr size_t DIR_X_OFFSET = 20;
    constexpr size_t DIR_Y_OFFSET = 24;
    constexpr size_t TIME_OFFSET = 28;
    constexpr size_t ZEM_OFFSET = 32;
    constexpr size_t PHOTONS_OFFSET = 36;
    constexpr size_t WAVELENGTH_OFFSET = 40;

    const std::byte* base_data_ptr = reinterpret_cast<const std::byte*>(data) + position;

    size_t end = index + n_bunches;
    size_t k = 0;
    for (size_t i=index; i<end; ++i) {
        const std::byte* current_bunch_base_ptr = base_data_ptr + k * BUNCH_RECORD_SIZE;

        // Get bunches from buffer
        std::memcpy(&bunches.pos[i].x,      current_bunch_base_ptr + POS_X_OFFSET,      ENTRY_SIZE);
        std::memcpy(&bunches.pos[i].y,      current_bunch_base_ptr + POS_Y_OFFSET,      ENTRY_SIZE);
        std::memcpy(&bunches.dir[i].cx,     current_bunch_base_ptr + DIR_X_OFFSET,      ENTRY_SIZE);
        std::memcpy(&bunches.dir[i].cy,     current_bunch_base_ptr + DIR_Y_OFFSET,      ENTRY_SIZE);
        std::memcpy(&bunches.time[i],       current_bunch_base_ptr + TIME_OFFSET,       ENTRY_SIZE);
        std::memcpy(&bunches.zem[i],        current_bunch_base_ptr + ZEM_OFFSET,        ENTRY_SIZE);
        std::memcpy(&bunches.photons[i],    current_bunch_base_ptr + PHOTONS_OFFSET,    ENTRY_SIZE);
        std::memcpy(&bunches.wavelength[i], current_bunch_base_ptr + WAVELENGTH_OFFSET, ENTRY_SIZE);

        k += 1;
    }
}

///////////////////////////////
// CORSIKA input card
///////////////////////////////

/**
 * @brief Get values of a CORSIKA option from the input card string. 
 * Booleans are replaced with (T)0 and (T)1.
 * 
 * @note Does not work for multiple keyword with the same name (like TELESCOPE).
 * 
 * @tparam T Type of the values.
 * @param key Option keyword (e.g. "CSCAT").
 * @param input_card std::string containing the input card.
 * @return std::vector<T> Option values.
 */
template<typename T>
static inline std::vector<T>
get_from_input_card(
    std::string key,
    const std::string& input_card
)
{
    auto start = input_card.find(key);
    auto end = input_card.find("\n", start+1);

    auto key_row = input_card.substr(start, end-start);

    // Remove comments from the key_row
    size_t comment_pos = key_row.find("//");
    if (comment_pos != std::string::npos) {
        key_row = key_row.substr(0, comment_pos);
    }

    comment_pos = key_row.find("#");
    if (comment_pos != std::string::npos) {
        key_row = key_row.substr(0, comment_pos);
    }

    // Replace T/F with 1/0 for boolean conversion
    key_row = std::regex_replace(key_row, std::regex(" F "), " 0 ");
    key_row = std::regex_replace(key_row, std::regex(" T "), " 1 ");
    
    std::regex words_regex("[-+]?(?:\\d+\\.?\\d*|\\.\\d+)(?:[eE][-+]?\\d+)?");
    auto words_begin = std::sregex_iterator(key_row.begin(), key_row.end(), words_regex);
    auto words_end = std::sregex_iterator();

    std::vector<T> values;
    for (std::sregex_iterator i = words_begin; i != words_end; ++i)
        {
            float value = std::stof((*i).str());
            values.push_back(static_cast<T>(value));
    }
    return values;
}

///////////////////////////////
// File reading
///////////////////////////////

constexpr unsigned char GZ_FIRST_BYTE{0x1f};
constexpr unsigned char GZ_SECOND_BYTE{0x8b};
constexpr std::size_t GZ_CHUNK_SIZE = 32768;

/**
 * @brief Load a whole file into memory.
 * 
 * @tparam TData Data type of the returned vector/array.
 * @tparam TSize Data type of the updated array size.
 * @param file_path Path of the file.
 * @param size Size of the returned array.
 * @return std::vector<TData> Pointer to the read data.
 */
template<typename TData>
inline std::vector<TData>
load_file(
    const char* file_path
) 
{
    // Get file size in bytes
    std::filesystem::path input_file_path{file_path};
    std::uintmax_t file_size = std::filesystem::file_size(file_path);
    
    // Get pointer size
    constexpr std::size_t type_size = sizeof(TData);
    if (file_size % type_size != 0)
        throw(std::runtime_error("File size is not a multiple of the type size."));
    
    std::size_t num_elements = static_cast<std::size_t>(file_size / type_size);

    // Allocate memory
    std::vector<TData> buffer(num_elements);

    // Open file
    std::ifstream input_file(input_file_path, std::ios_base::binary);

    if (!input_file.is_open()) {
        throw std::runtime_error("Failed to open file: " + input_file_path.string());
    }

    // Read file
    input_file.read(reinterpret_cast<char*>(buffer.data()), file_size);

    if (!input_file) 
    {
        throw std::runtime_error(
            "Error reading file: " + input_file_path.string() +
            ". Only " + std::to_string(input_file.gcount()) + " bytes could be read."
        );
    }
    
    return buffer;
}

/**
 * @brief Check if a file is gzipped by looking for its magic number.
 * 
 * @param file_path Path of the file.
 * @return true If the file is gzipped.
 * @return false If the file is not gzipped.
 * @throws std::runtime_error If the file does not exist.
 */
static inline bool is_gzipped(const char* file_path)
{
    if (!std::filesystem::exists(std::filesystem::path{file_path})) {
        std::stringstream message;
        message << "Error opening file: " << file_path << std::endl;
        throw std::runtime_error(message.str());
    }

    unsigned char buffer[2];
    std::ifstream input_file(file_path, std::ios_base::binary);
    input_file.read(reinterpret_cast<char*>(buffer), 2);
    input_file.close();

    return (buffer[0] == GZ_FIRST_BYTE) && (buffer[1] == GZ_SECOND_BYTE);
}

/**
 * @brief Decompress from source file until stream ends or EOF.
 * Throws if:
 *   - status is Z_MEM_ERROR, i.e. memory could not be allocated for processing;
 *   - status is Z_DATA_ERROR, i.e. the deflate data is invalid or incomplete;
 *   - status is Z_STREAM_ERROR, i.e. the stream is not initialized properly;
 *   - there is an error reading the file.
 * Adapted from https://www.zlib.net/zlib_how.html.
 * 
 * @tparam TData 
 * @tparam TSize 
 * @param file_path 
 * @param size 
 * @return std::vector<TData> 
 */
template<typename TData>
inline std::vector<TData>
decompress_gzip_file(
  const char* file_path
)
{   
    static_assert(sizeof(TData) == 1, "Template argument TData must be a byte-sized type (e.g., char, unsigned char, std::byte).");

    FILE* source = fopen(file_path, "rb");

    Bytef in[GZ_CHUNK_SIZE];
    Bytef out[GZ_CHUNK_SIZE];

    // Allocate inflate state
    z_stream stream;
    stream.zalloc = Z_NULL;
    stream.zfree = Z_NULL;
    stream.opaque = Z_NULL;
    stream.avail_in = 0;
    stream.next_in = Z_NULL;

    int status;
    status = inflateInit2(&stream, 16+MAX_WBITS); // only gzip files, add 32 to enable also zlib decoding
    if (status != Z_OK) {
        std::stringstream message;
        message << "Error decompressing file: " << file_path << "\nCheck the gzip file integrity."<< std::endl;
        throw std::runtime_error(message.str());
    }

    // Get file size in bytes
    std::filesystem::path input_file_path{file_path};
    std::uintmax_t file_size = std::filesystem::file_size(input_file_path);

    // Reasonable amount of memory for CORSIKA IACT files
    std::vector<TData> data;
    data.reserve(2.0*file_size);

    // std::cerr << "INFO: decompress_gzip_file(" << file_path << ") - After reserve:\n"
    //             << "      Size: " << data.size()
    //             << ", Capacity: " << data.capacity()
    //             << " (elements)" << std::endl;

    // auto decompress_start_time = std::chrono::high_resolution_clock::now();

  
    // Decompress until deflate stream ends or end of file
    unsigned have;
    do {
        stream.avail_in = fread(in, 1, GZ_CHUNK_SIZE, source);

        if (ferror(source)) {
            inflateEnd(&stream);
            std::stringstream message;
            message << "Error decompressing file: " << file_path << "\nCheck the gzip file integrity."<< std::endl;
            throw std::runtime_error(message.str());
        }
        
        if (stream.avail_in == 0)
            break;

        // Run inflate() on input until output buffer is not full
        stream.next_in = in;
        do {
            stream.avail_out = GZ_CHUNK_SIZE;
            stream.next_out = out;

            status = inflate(&stream, Z_NO_FLUSH);

            switch (status) {
            case Z_STREAM_ERROR:
                [[fallthrough]];
            case Z_NEED_DICT:
                status = Z_DATA_ERROR;
                [[fallthrough]];
            case Z_DATA_ERROR:
                [[fallthrough]];
            case Z_MEM_ERROR:
                inflateEnd(&stream);
                std::stringstream message;
                message << "Error decompressing file: " << file_path << "\nCheck the gzip file integrity."<< std::endl;
                throw std::runtime_error(message.str());
            }
            have = GZ_CHUNK_SIZE - stream.avail_out;
            data.insert(data.end(), out, out+have);
        } while (stream.avail_out == 0);

    } while (status != Z_STREAM_END);

    // Clean up inflate state
    inflateEnd(&stream);

    // auto decompress_end_time = std::chrono::high_resolution_clock::now();
    // auto decompress_duration = std::chrono::duration_cast<std::chrono::microseconds>(decompress_end_time - decompress_start_time);
    // std::cerr << "TIMING: decompress_gzip_file(" << file_path << ") - Decompression loop took " 
    //             << decompress_duration.count() << " microseconds." << std::endl;

    // std::cerr << "INFO: decompress_gzip_file(" << file_path << ") - Before shrink_to_fit:\n"
    //             << "      Size: " << data.size() 
    //             << ", Capacity: " << data.capacity() 
    //             << " (elements)" << std::endl;

    // auto shrink_start_time = std::chrono::high_resolution_clock::now();

    data.shrink_to_fit();

    // auto shrink_end_time = std::chrono::high_resolution_clock::now();
    // auto shrink_duration = std::chrono::duration_cast<std::chrono::microseconds>(shrink_end_time - shrink_start_time);

    // std::cerr << "INFO: decompress_gzip_file(" << file_path << ") - After shrink_to_fit:\n"
    //             << "      Size: " << data.size() 
    //             << ", Capacity: " << data.capacity() 
    //             << " (elements)" << std::endl;
    // std::cerr << "TIMING: decompress_gzip_file(" << file_path << ") - shrink_to_fit took " 
    //             << shrink_duration.count() << " microseconds." << std::endl;

    return data;
}

/**
 * @brief Check if a file is Zstandard compressed by looking for its magic number.
 * @param file_path Path of the file to check.
 * @return true If the file starts with the Zstandard magic number.
 * @return false If the file does not start with the magic number, is too short, or cannot be opened/read.
 * @throws std::runtime_error If the file does not exist.
 */
static inline bool is_zstd_compressed(const char* file_path)
{
    if (!std::filesystem::exists(std::filesystem::path{file_path})) {
        std::stringstream message;
        message << "Error checking file (does not exist): " << file_path << std::endl;
        throw std::runtime_error(message.str());
    }

    unsigned char buffer[4];
    std::ifstream input_file(file_path, std::ios_base::binary);
    input_file.read(reinterpret_cast<char*>(buffer), sizeof(buffer));
    input_file.close();

    return (buffer[0] == 0x28 &&
            buffer[1] == 0xB5 &&
            buffer[2] == 0x2F &&
            buffer[3] == 0xFD);
}

#ifdef USE_LIBZSTD
/**
 * @brief Decompress a Zstandard compressed file into a vector of bytes.
 * Throws std::runtime_error if:
 * - The file cannot be opened.
 * - Memory cannot be allocated for ZSTD context.
 * - There is an error reading from the file.
 * - ZSTD reports a decompression error.
 * * @tparam TData The type of data elements in the output vector. Must be byte-sized.
 * @param file_path Path to the Zstandard compressed file.
 * @return std::vector<TData> A vector containing the decompressed data.
 */
template<typename TData>
inline std::vector<TData>
decompress_zstd_file(
  const char* file_path
)
{   
    static_assert(sizeof(TData) == 1, "Template argument TData must be a byte-sized type.");

    // Open the source file in binary read mode
    FILE* source_file = fopen(file_path, "rb");
    if (!source_file) {
        // consider thread-safe error reporting
        std::stringstream ss;
        ss << "Error opening file: " << file_path << " (" << strerror(errno) << ")";
        throw std::runtime_error(ss.str());
    }

    // Create and initialize ZSTD decompression context
    ZSTD_DCtx* dctx = ZSTD_createDCtx();
    if (!dctx) {
        fclose(source_file);
        throw std::runtime_error("ZSTD_createDCtx() failed: Not enough memory?");
    }

    // Recommended buffer sizes for ZSTD streaming operations
    size_t const input_buffer_recommended_size = ZSTD_DStreamInSize();
    size_t const output_buffer_recommended_size = ZSTD_DStreamOutSize();

    // Buffer vectors
    std::vector<unsigned char> input_buffer(input_buffer_recommended_size);
    std::vector<unsigned char> output_buffer(output_buffer_recommended_size);

    // Reserve memory for the output vector 
    std::vector<TData> decompressed_data;
    std::filesystem::path input_file_path_obj{file_path};
    std::uintmax_t file_size = std::filesystem::file_size(input_file_path_obj);
    decompressed_data.reserve(static_cast<size_t>(file_size*2.0));

    // std::cerr << "INFO: decompress_zstd_file(" << file_path << ") - After reserve:\n"
    //           << "      Size: " << decompressed_data.size()
    //           << ", Capacity: " << decompressed_data.capacity()
    //           << " (elements)" << std::endl;

    // auto decompress_start_time = std::chrono::high_resolution_clock::now();
    
    // Initialize to a non-zero value
    // Will be used to check if at the end of file zstd needs to flush buffers 
    size_t last_decompression_return_value = 1;

    // Main decompression loop
    ZSTD_inBuffer zstd_input_wrapper = {nullptr, 0, 0}; // will point to input_buffer.data()
    while (true) {
        // If all data from the previous fread operation was processed, or at the beginning:
        // read from the file into the input_buffer
        if (zstd_input_wrapper.pos == zstd_input_wrapper.size) 
        {
            size_t bytes_read_from_file = fread(input_buffer.data(), 1, input_buffer_recommended_size, source_file);
            
            // Check for errors
            if (ferror(source_file)) 
            {
                ZSTD_freeDCtx(dctx);
                fclose(source_file);
                std::stringstream ss;
                ss << "Error reading from file: " << file_path << " (" << strerror(errno) << ")";
                throw std::runtime_error(ss.str());
            }
            
            // Assign buffer data to the wrapper
            zstd_input_wrapper.src = input_buffer.data();
            zstd_input_wrapper.size = bytes_read_from_file;
            zstd_input_wrapper.pos = 0;

            // End of the file reached
            if (bytes_read_from_file == 0) 
            {
                if (last_decompression_return_value == 0) {
                    break; // Successfully reached EOF and all ZSTD frames are complete.
                }
                // If last_decompression_return_value was not 0, ZSTD might still need to flush
                // internal buffers or expects more input for the current frame.
                // The loop will continue once more with an empty input buffer.
            }
        }

        // Prepare the output buffer for ZSTD
        ZSTD_outBuffer zstd_output_wrapper = {output_buffer.data(), output_buffer_recommended_size, 0};
        
        // Perform decompression
        // The return value is a hint for the next input size, 0 if a frame is complete, or an error code
        size_t const current_decompression_return_value = ZSTD_decompressStream(dctx, &zstd_output_wrapper, &zstd_input_wrapper);

        if (ZSTD_isError(current_decompression_return_value)) 
        {
            ZSTD_freeDCtx(dctx);
            fclose(source_file);
            std::stringstream ss;
            ss << "ZSTD decompression error for file '" << file_path << "': " 
               << ZSTD_getErrorName(current_decompression_return_value);
            throw std::runtime_error(ss.str());
        }

        // Append the decompressed chunk to the result vector
        const TData* decompressed_chunk_start = reinterpret_cast<const TData*>(output_buffer.data());
        decompressed_data.insert(
            decompressed_data.end(), 
            decompressed_chunk_start, 
            decompressed_chunk_start + zstd_output_wrapper.pos
        );
        
        last_decompression_return_value = current_decompression_return_value;

        if (current_decompression_return_value == 0 && zstd_input_wrapper.size == 0) 
        {
             break; // all frames are decompressed and EOF is confirmed
        }
        
        // Check for truncated stream at EOF:
        if (zstd_input_wrapper.pos == zstd_input_wrapper.size && 
            zstd_input_wrapper.size == 0 && 
            current_decompression_return_value != 0) 
        {
            ZSTD_freeDCtx(dctx);
            fclose(source_file);
            std::stringstream ss;
            ss << "ZSTD decompression error for file '" << file_path 
               << "': Stream is truncated or corrupt. ZSTD expects more data at EOF.";
            throw std::runtime_error(ss.str());
        }
    }

    // Clean up
    ZSTD_freeDCtx(dctx);
    fclose(source_file);

    // auto decompress_end_time = std::chrono::high_resolution_clock::now();
    // auto decompress_duration = std::chrono::duration_cast<std::chrono::microseconds>(decompress_end_time - decompress_start_time);
    // std::cerr << "TIMING: decompress_zstd_file(" << file_path << ") - Decompression loop took " 
    //           << decompress_duration.count() << " microseconds." << std::endl;

    // // Reduce vector capacity to actual size
    // std::cerr << "INFO: decompress_zstd_file(" << file_path << ") - Before shrink_to_fit:\n"
    //           << "      Size: " << decompressed_data.size() 
    //           << ", Capacity: " << decompressed_data.capacity() 
    //           << " (elements)" << std::endl;

    // auto shrink_start_time = std::chrono::high_resolution_clock::now();

    decompressed_data.shrink_to_fit();
    
    // auto shrink_end_time = std::chrono::high_resolution_clock::now();
    // auto shrink_duration = std::chrono::duration_cast<std::chrono::microseconds>(shrink_end_time - shrink_start_time);

    // std::cerr << "INFO: decompress_zstd_file(" << file_path << ") - After shrink_to_fit:\n"
    //           << "      Size: " << decompressed_data.size() 
    //           << ", Capacity: " << decompressed_data.capacity() 
    //           << " (elements)" << std::endl;
    // std::cerr << "TIMING: decompress_zstd_file(" << file_path << ") - shrink_to_fit took " 
    //           << shrink_duration.count() << " microseconds." << std::endl;

    return decompressed_data;
}
#endif

} // iactxx::eventio namespace

///////////////////////////////
// ostream overloads
///////////////////////////////

/**
 * @brief Overload ostream operator<< for ObjectHeader struct.
 * 
 * @param output Output stream.
 * @param object_header An ObjectHeader.
 * @return std::ostream& 
 */
static inline std::ostream &operator<<(std::ostream &output, const iactxx::eventio::ObjectHeader &object_header)
{
    output << "Marker\t\t" << object_header.marker << std::endl;
    output << "Object type\t" << object_header.type << std::endl;
    output << "Object version\t" << object_header.version << std::endl;
    output << "Identifier\t" << object_header.id << std::endl;
    output << "Length\t\t" << object_header.length << std::endl;
    output << std::boolalpha << "Only sub-obj\t" << object_header.only_sub_objects << std::endl;
    output << "Header size\t" << object_header.header_size << std::endl;
    output << "Address\t\t" << object_header.address << std::endl;
    output << "Extended\t" << object_header.extended << std::endl;
    return output;
}

/**
 * @brief Overload ostream operator<< for Bunches struct.
 * 
 * @tparam T Bunches data type.
 * @param output Output stream.
 * @param bunches A Bunches.
 * @return std::ostream& 
 */
template<typename T>
static inline std::ostream &operator<<(std::ostream &output, const iactxx::eventio::Bunches<T> &bunches)
{
    auto n_bunches = bunches.n_bunches;

    for (std::size_t i=0; i<n_bunches; ++i) {
        output << bunches.pos[i].x << "\t"
               << bunches.pos[i].y << "\t"
               << bunches.pos[i].z << "\t"
               << bunches.dir[i].cx << "\t"
               << bunches.dir[i].cy << "\t"
               << bunches.time[i] << "\t"
               << bunches.zem[i] << "\t"
               << bunches.photons[i] << "\t"
               << bunches.wavelength[i]
               << "\n";
    }
    output << std::endl;
    return output;
}
