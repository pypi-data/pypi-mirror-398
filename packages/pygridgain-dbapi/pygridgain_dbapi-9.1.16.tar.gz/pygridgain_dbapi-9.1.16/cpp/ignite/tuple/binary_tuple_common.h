/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <cstddef>
#include <cstdint>

namespace ignite {

/** C++ version of Java int. Used as a column number, etc. */
using tuple_num_t = std::int32_t;

/** Data size for columns and entire rows too. */
using tuple_size_t = std::uint32_t;

namespace binary_tuple_common {

/** Header size in bytes. */
constexpr tuple_size_t HEADER_SIZE = 1;

/** Empty varlen token. */
constexpr std::byte VARLEN_EMPTY_BYTE{0x80};

/** Mask for tuple size bits. */
constexpr std::byte VARLEN_ENTRY_SIZE_MASK{0b11};

/** Flag indicating that the offset table is larger than required. */
constexpr std::byte OFFSET_TABLE_OVERSIZED{0b100};

/** Encodes size as a bit mask. */
constexpr unsigned int size_to_flags(tuple_size_t size) noexcept {
    if (size <= UINT8_MAX) {
        return 0b00;
    }
    if (size <= UINT16_MAX) {
        return 0b01;
    }
    return 0b10;
}

/**
 * @brief A helper to work with binary tuple header.
 */
struct header {
    /** Tuple flags. */
    std::byte flags{0};

    /** Sets the size of offset-table entries based on the value area size. */
    unsigned int set_entry_size(tuple_size_t value_area_size) noexcept {
        const auto size_log2 = size_to_flags(value_area_size);
        flags &= ~VARLEN_ENTRY_SIZE_MASK;
        flags |= std::byte(size_log2);
        return 1u << size_log2;
    }

    /** Sets the offset-table 'oversized' flag. */
    void set_oversized(bool oversized) {
        if (oversized) {
            flags |= OFFSET_TABLE_OVERSIZED;
        } else {
            flags &= ~OFFSET_TABLE_OVERSIZED;
        }
    }

    /** Gets the size of a single offset-table entry, in bytes. */
    tuple_size_t get_entry_size() const noexcept { return 1u << static_cast<unsigned>(flags & VARLEN_ENTRY_SIZE_MASK); }

    /** Gets the offset-table 'oversized' flag. */
    bool is_oversized() const noexcept { return (flags & OFFSET_TABLE_OVERSIZED) != std::byte{0}; }
};

} // namespace binary_tuple_common

} // namespace ignite
