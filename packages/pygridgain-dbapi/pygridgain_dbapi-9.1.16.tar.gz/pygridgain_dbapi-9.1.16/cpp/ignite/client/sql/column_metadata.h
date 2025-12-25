/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/sql/column_origin.h"
#include "ignite/common/ignite_type.h"

#include <cstdint>
#include <string>

namespace ignite {

/**
 * @brief Table column metadata.
 *
 * Represents table field properties such as name, type, nullability, etc.
 */
class column_metadata {
public:
    // Default
    column_metadata() = default;

    /**
     * Constructor.
     *
     * @param name Column name.
     * @param type Column type.
     * @param precision Precision.
     * @param scale Scale.
     * @param nullable Column nullability.
     * @param origin Column origin.
     */
    column_metadata(std::string name, ignite_type type, std::int32_t precision, std::int32_t scale, bool nullable,
        column_origin origin)
        : m_name(std::move(name))
        , m_type(type)
        , m_precision(precision)
        , m_scale(scale)
        , m_nullable(nullable)
        , m_origin(std::move(origin)) {}

    /**
     * Gets the column name.
     *
     * @return Column name.
     */
    [[nodiscard]] const std::string &name() const { return m_name; }

    /**
     * Gets the column type.
     *
     * @return Column type.
     */
    [[nodiscard]] ignite_type type() const { return m_type; }

    /**
     * Gets the column precision, or -1 when not applicable to the current
     * column type.
     *
     * @return Number of decimal digits for exact numeric types; number of
     *   decimal digits in mantissa for approximate numeric types; number of
     *   decimal digits for fractional seconds of datetime types; length in
     *   characters for character types; length in bytes for binary types;
     *   length in bits for bit types; 1 for BOOLEAN; -1 if precision is not
     *   valid for the type.
     */
    [[nodiscard]] std::int32_t precision() const { return m_precision; }

    /**
     * Gets the column scale.
     *
     * @return Number of digits of scale.
     */
    [[nodiscard]] std::int32_t scale() const { return m_scale; }

    /**
     * Gets a value indicating whether the column is nullable.
     *
     * @return A value indicating whether the column is nullable.
     */
    [[nodiscard]] bool nullable() const { return m_nullable; }

    /**
     * Gets the column origin.
     *
     * For example, for "select foo as bar" query, column name will be "bar", but origin name will be "foo".
     *
     * @return The column origin.
     */
    [[nodiscard]] const column_origin &origin() const { return m_origin; }

private:
    /** Column name. */
    std::string m_name;

    /** Column type. */
    ignite_type m_type{ignite_type::UNDEFINED};

    /** Precision. */
    std::int32_t m_precision{0};

    /** Scale. */
    std::int32_t m_scale{0};

    /** Nullable. */
    bool m_nullable{false};

    /** Origin. */
    column_origin m_origin;
};

} // namespace ignite
