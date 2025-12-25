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
#include <type_traits>

namespace ignite::detail {

/**
 * A hybrid timestamp that combines physical clock and logical clock.
 */
class hybrid_timestamp {
public:
    /** Number of bits in "logical time" part. */
    static constexpr std::int32_t LOGICAL_TIME_BITS_SIZE = 16;

    /**
     * Constructor.
     *
     * @param time Hybrid timestamp value.
     */
    explicit hybrid_timestamp(std::int64_t time)
        : m_time(time) {}

    /**
     * Get time value.
     *
     * @return Time value.
     */
    [[nodiscard]] std::int64_t get_value() const { return m_time; }

    /**
     * Converts physical time to a primitive {@code long} representation of hybrid timestamp.
     */
    [[nodiscard]] static std::int64_t physical_to_long(std::int64_t physical) {
        return physical << LOGICAL_TIME_BITS_SIZE;
    }

private:
    /** Time value. */
    std::int64_t m_time{0};
};

} // namespace ignite::detail
