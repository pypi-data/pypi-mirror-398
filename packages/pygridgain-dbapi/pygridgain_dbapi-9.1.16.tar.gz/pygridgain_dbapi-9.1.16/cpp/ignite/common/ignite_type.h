/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ostream>

namespace ignite {

/**
 * @brief Supported types for column data.
 *
 * @note type of enum value is int, size is same as sizeof(int).
 */
enum class ignite_type {
    /** Null. */
    NIL = 0,

    /** Boolean. */
    BOOLEAN = 1,

    /** 8-bit signed integer. */
    INT8 = 2,

    /** 16-bit signed integer. */
    INT16 = 3,

    /** 32-bit signed integer. */
    INT32 = 4,

    /** 64-bit signed integer. */
    INT64 = 5,

    /** 32-bit single-precision floating-point number. */
    FLOAT = 6,

    /** 64-bit double-precision floating-point number. */
    DOUBLE = 7,

    /** A decimal fixed-point number. */
    DECIMAL = 8,

    /** Timezone-free date. */
    DATE = 9,

    /** Timezone-free time with precision. */
    TIME = 10,

    /** Timezone-free datetime. */
    DATETIME = 11,

    /** Number of ticks since Jan 1, 1970 00:00:00.000 (with no timezone). Tick unit depends on precision. */
    TIMESTAMP = 12,

    /** 128-bit UUID. */
    UUID = 13,

    /** String. */
    STRING = 15,

    /** Binary data. */
    BYTE_ARRAY = 16,

    /** Date interval. */
    PERIOD = 17,

    /** Time interval. */
    DURATION = 18,

    /** Undefined. */
    UNDEFINED
};

/**
 * @brief Writes a ignite_type value to an output stream.
 */
inline std::ostream &operator<<(std::ostream &os, const ignite_type t) {
    os << static_cast<std::underlying_type_t<ignite_type>>(t);
    return os;
}

} // namespace ignite
