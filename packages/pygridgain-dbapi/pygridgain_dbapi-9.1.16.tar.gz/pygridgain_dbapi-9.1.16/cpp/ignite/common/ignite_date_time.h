/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite_date.h"
#include "ignite_time.h"

#include <cstdint>

namespace ignite {

/**
 * @brief A date together with time of day with nanosecond precision.
 *
 * This is modeled after java.time.LocalDateTime.
 */
class ignite_date_time : public ignite_date, public ignite_time {
public:
    /**
     * Default constructor.
     */
    constexpr ignite_date_time() noexcept = default;

    /**
     * Constructor.
     *
     * @param date
     * @param time
     */
    constexpr ignite_date_time(const ignite_date &date, const ignite_time &time)
        : ignite_date(date)
        , ignite_time(time) {}

    /**
     * Gets the date part of this date-time.
     */
    [[nodiscard]] constexpr const ignite_date &date() const noexcept { return *this; }

    /**
     * Gets the time part of this date-time.
     */
    [[nodiscard]] constexpr const ignite_time &time() const noexcept { return *this; }

    /**
     * compare to another value.
     *
     * @param other Instance to compare to.
     * @return Zero if equals, negative number if less, and positive if greater.
     */
    [[nodiscard]] constexpr int compare(const ignite_date_time &other) const noexcept {
        if (int cmp = date().compare(other.date())) {
            return cmp;
        }
        return time().compare(other.time());
    }
};

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is equal to the second.
 */
constexpr bool operator==(const ignite_date_time &lhs, const ignite_date_time &rhs) noexcept {
    return lhs.compare(rhs) == 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is not equal to the second.
 */
constexpr bool operator!=(const ignite_date_time &lhs, const ignite_date_time &rhs) noexcept {
    return lhs.compare(rhs) != 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is less than the second.
 */
constexpr bool operator<(const ignite_date_time &lhs, const ignite_date_time &rhs) noexcept {
    return lhs.compare(rhs) < 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is less than or equal to the second.
 */
constexpr bool operator<=(const ignite_date_time &lhs, const ignite_date_time &rhs) noexcept {
    return lhs.compare(rhs) <= 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is greater than the second.
 */
constexpr bool operator>(const ignite_date_time &lhs, const ignite_date_time &rhs) noexcept {
    return lhs.compare(rhs) > 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is greater than or equal to the second.
 */
constexpr bool operator>=(const ignite_date_time &lhs, const ignite_date_time &rhs) noexcept {
    return lhs.compare(rhs) >= 0;
}

} // namespace ignite
