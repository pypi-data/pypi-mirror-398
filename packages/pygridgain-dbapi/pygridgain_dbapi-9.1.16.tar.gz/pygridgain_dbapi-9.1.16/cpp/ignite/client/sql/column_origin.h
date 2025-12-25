/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <string>

namespace ignite {

/**
 * @brief SQL column origin.
 *
 * Original name of column.
 * Required when SQL statement change column name using aliases.
 * See @ref ignite::column_metadata
 */
class column_origin {
public:
    // Default
    column_origin() = default;

    /**
     * Constructor.
     *
     * @param column_name Column name.
     * @param table_name Table name
     * @param schema_name Schema name.
     */
    column_origin(std::string column_name, std::string table_name, std::string schema_name)
        : m_column_name(std::move(column_name))
        , m_table_name(std::move(table_name))
        , m_schema_name(std::move(schema_name)) {}

    /**
     * Gets the column name.
     *
     * @return Column name.
     */
    [[nodiscard]] const std::string &column_name() const { return m_column_name; }

    /**
     * Gets the table name.
     *
     * @return Table name.
     */
    [[nodiscard]] const std::string &table_name() const { return m_table_name; }

    /**
     * Gets the schema name.
     *
     * @return Schema name.
     */
    [[nodiscard]] const std::string &schema_name() const { return m_schema_name; }

private:
    /** Column name. */
    std::string m_column_name;

    /** Table name. */
    std::string m_table_name;

    /** Schema name. */
    std::string m_schema_name;
};

} // namespace ignite
