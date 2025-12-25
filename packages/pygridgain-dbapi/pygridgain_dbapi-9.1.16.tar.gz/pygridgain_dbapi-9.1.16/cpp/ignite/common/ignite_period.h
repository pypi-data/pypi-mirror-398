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
 * @brief A date-based amount of time.
 *
 * This is modeled after java.time.Period.
 */
class ignite_period {
public:
    /**
     * Default constructor.
     */
    constexpr ignite_period() noexcept = default;

    /**
     * Constructor.
     *
     * @param years The number of years.
     * @param months The number of months.
     * @param days The number of days.
     */
    constexpr ignite_period(std::int32_t years, std::int32_t months, std::int32_t days)
        : years(years)
        , months(months)
        , days(days) {
        // TODO: check that arguments are in valid ranges.
    }

    /**
     * Gets the years field.
     */
    constexpr std::int32_t get_years() const noexcept { return years; }

    /**
     * Gets the months field.
     */
    constexpr std::int32_t get_months() const noexcept { return months; }

    /**
     * Gets the days field.
     */
    constexpr std::int32_t get_days() const noexcept { return days; }

    /**
     * compare to another value.
     *
     * @param other Instance to compare to.
     * @return Zero if equals, negative number if less, and positive if greater.
     */
    constexpr int compare(const ignite_period &other) const noexcept {
        if (years != other.years) {
            return years - other.years;
        }
        if (months != other.months) {
            return months - other.months;
        }
        return days - other.days;
    }

private:
    std::int_least32_t years = 0;
    std::int_least32_t months = 0;
    std::int_least32_t days = 0;
};

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is equal to the second.
 */
constexpr bool operator==(const ignite_period &lhs, const ignite_period &rhs) noexcept {
    return lhs.compare(rhs) == 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is not equal to the second.
 */
constexpr bool operator!=(const ignite_period &lhs, const ignite_period &rhs) noexcept {
    return lhs.compare(rhs) != 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is less than the second.
 */
constexpr bool operator<(const ignite_period &lhs, const ignite_period &rhs) noexcept {
    return lhs.compare(rhs) < 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is less than or equal to the second.
 */
constexpr bool operator<=(const ignite_period &lhs, const ignite_period &rhs) noexcept {
    return lhs.compare(rhs) <= 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is greater than the second.
 */
constexpr bool operator>(const ignite_period &lhs, const ignite_period &rhs) noexcept {
    return lhs.compare(rhs) > 0;
}

/**
 * @brief Comparison operator.
 *
 * @param lhs First value.
 * @param rhs Second value.
 * @return true If the first value is greater than or equal to the second.
 */
constexpr bool operator>=(const ignite_period &lhs, const ignite_period &rhs) noexcept {
    return lhs.compare(rhs) >= 0;
}

} // namespace ignite
