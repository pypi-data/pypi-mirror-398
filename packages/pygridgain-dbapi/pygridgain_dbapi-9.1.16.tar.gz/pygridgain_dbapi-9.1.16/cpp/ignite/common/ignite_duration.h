/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <cstdint>

namespace ignite {

/**
 * @brief A time-based amount of time.
 *
 * This is modeled after java.time.Duration.
 */
class ignite_duration {
public:
    /**
     * Default constructor.
     */
    constexpr ignite_duration() noexcept = default;

    /**
     * Constructor.
     *
     * @param seconds Number of seconds.
     * @param nanos Fractional second component in nanoseconds.
     */
    constexpr ignite_duration(std::int64_t seconds, std::int32_t nanos)
        : seconds(seconds)
        , nanos(nanos) {
        // TODO: check that arguments are in valid ranges.
    }

    /**
     * Gets the number of seconds.
     */
    constexpr std::int64_t get_seconds() const noexcept { return seconds; }

    /**
     * Gets the number of nanoseconds.
     */
    constexpr std::int32_t get_nano() const noexcept { return nanos; }

    /**
     * compare to another value.
     *
     * @param other Instance to compare to.
     * @return Zero if equals, negative number if less, and positive if greater.
     */
    constexpr int compare(const ignite_duration &other) const noexcept {
        if (seconds != other.seconds) {
            return seconds < other.seconds ? -1 : 1;
        }
        return nanos - other.nanos;
    }

private:
    /** Number of seconds. */
    std::int64_t seconds = 0;

    /** Fractional second component in nanoseconds. */
    std::int32_t nanos = 0;
};

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is equal to the second.
 */
constexpr bool operator==(const ignite_duration &lhs, const ignite_duration &rhs) noexcept {
    return lhs.compare(rhs) == 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is not equal to the second.
 */
constexpr bool operator!=(const ignite_duration &lhs, const ignite_duration &rhs) noexcept {
    return lhs.compare(rhs) != 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is less than the second.
 */
constexpr bool operator<(const ignite_duration &lhs, const ignite_duration &rhs) noexcept {
    return lhs.compare(rhs) < 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is less than or equal to the second.
 */
constexpr bool operator<=(const ignite_duration &lhs, const ignite_duration &rhs) noexcept {
    return lhs.compare(rhs) <= 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is greater than the second.
 */
constexpr bool operator>(const ignite_duration &lhs, const ignite_duration &rhs) noexcept {
    return lhs.compare(rhs) > 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is greater than or equal to the second.
 */
constexpr bool operator>=(const ignite_duration &lhs, const ignite_duration &rhs) noexcept {
    return lhs.compare(rhs) >= 0;
}

} // namespace ignite
