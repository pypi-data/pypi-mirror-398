/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "primitive.h"

namespace ignite {

/**
 * @brief Ignite binary object type.
 *
 * Wrapper for @ref ignite::primitive.
 */
class binary_object {
public:
    // Default
    binary_object() = default;

    /**
     * Primitive constructor.
     *
     * @param value Primitive type value.
     */
    binary_object(primitive value) // NOLINT(google-explicit-constructor)
        : m_value(std::move(value)) {}

    /**
     * Get underlying primitive value.
     *
     * @throw ignite_error If the packed value is not a primitive.
     * @return Primitive value.
     */
    primitive get_primitive() const { return m_value; }

private:
    /** Value. */
    primitive m_value;
};

} // namespace ignite
