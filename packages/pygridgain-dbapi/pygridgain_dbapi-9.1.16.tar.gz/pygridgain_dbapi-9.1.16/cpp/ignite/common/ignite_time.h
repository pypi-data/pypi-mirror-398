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
 * @brief A time of day with nanosecond precision.
 *
 * This is modeled after java.time.LocalTime.
 */
class ignite_time {
public:
    /**
     * Default constructor.
     */
    constexpr ignite_time() noexcept = default;

    /**
     * Constructor.
     *
     * @param hour Hour-of-day, from 0 to 23.
     * @param minute Minute-of-hour, from 0 to 59.
     * @param second Second-of-minute, from 0 to 59.
     * @param nano Nano-of-second, from 0 to 999,999,999.
     */
    constexpr ignite_time(
        std::int_fast8_t hour, std::int_fast8_t minute, std::int_fast8_t second = 0, std::int32_t nano = 0)
        : m_hour(hour)
        , m_minute(minute)
        , m_second(second)
        , m_nano(nano) {
        // TODO: check that arguments are in valid ranges.
    }

    /**
     * Gets the hour-of-day field.
     */
    [[nodiscard]] constexpr std::int_fast8_t get_hour() const noexcept { return m_hour; }

    /**
     * Gets the m_minute-of-m_hour field.
     */
    [[nodiscard]] constexpr std::int_fast8_t get_minute() const noexcept { return m_minute; }

    /**
     * Gets the second-of-m_minute field.
     */
    [[nodiscard]] constexpr std::int_fast8_t get_second() const noexcept { return m_second; }

    /**
     * Gets the nano-of-second field.
     */
    [[nodiscard]] constexpr std::int32_t get_nano() const noexcept { return m_nano; }

    /**
     * compare to another value.
     *
     * @param other Instance to compare to.
     * @return Zero if equals, negative number if less, and positive if greater.
     */
    [[nodiscard]] constexpr int compare(const ignite_time &other) const noexcept {
        if (m_hour != other.m_hour) {
            return m_hour - other.m_hour;
        }
        if (m_minute != other.m_minute) {
            return m_minute - other.m_minute;
        }
        if (m_second != other.m_second) {
            return m_second - other.m_second;
        }
        return m_nano - other.m_nano;
    }

private:
    std::int_least8_t m_hour = 0;
    std::int_least8_t m_minute = 0;
    std::int_least8_t m_second = 0;
    std::int_least32_t m_nano = 0;
};

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is equal to the second.
 */
constexpr bool operator==(const ignite_time &lhs, const ignite_time &rhs) noexcept {
    return lhs.compare(rhs) == 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is not equal to the second.
 */
constexpr bool operator!=(const ignite_time &lhs, const ignite_time &rhs) noexcept {
    return lhs.compare(rhs) != 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is less than the second.
 */
constexpr bool operator<(const ignite_time &lhs, const ignite_time &rhs) noexcept {
    return lhs.compare(rhs) < 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is less than or equal to the second.
 */
constexpr bool operator<=(const ignite_time &lhs, const ignite_time &rhs) noexcept {
    return lhs.compare(rhs) <= 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is greater than the second.
 */
constexpr bool operator>(const ignite_time &lhs, const ignite_time &rhs) noexcept {
    return lhs.compare(rhs) > 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is greater than or equal to the second.
 */
constexpr bool operator>=(const ignite_time &lhs, const ignite_time &rhs) noexcept {
    return lhs.compare(rhs) >= 0;
}

} // namespace ignite
