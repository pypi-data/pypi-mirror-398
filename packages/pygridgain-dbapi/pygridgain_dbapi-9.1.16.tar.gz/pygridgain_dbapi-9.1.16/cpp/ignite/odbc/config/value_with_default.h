/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <utility>

namespace ignite {

/**
 * Simple abstraction for value, that have default value but can be set to a different value.
 *
 * @tparam T Type of the value.
 */
template<typename T>
class value_with_default {
public:
    /** Type of the value. */
    typedef T value_type;

    /**
     * Constructor.
     *
     * @param value Value to return.
     * @param set Flag indicating whether value was set by user or is default.
     */
    value_with_default(value_type value, bool set)
        : m_value(std::move(value))
        , m_set(set) {}

    /**
     * Get value.
     *
     * @return Value or default value if not set.
     */
    const value_type &get_value() const { return m_value; }

    /**
     * Check whether value is set to non-default.
     */
    [[nodiscard]] bool is_set() const { return m_set; }

private:
    /** Current value. */
    value_type m_value{};

    /** Flag showing whether value was set to non-default value. */
    bool m_set{false};
};

} // namespace ignite
