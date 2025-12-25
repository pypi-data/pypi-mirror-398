/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/odbc/query/query.h"

namespace ignite {

/**
 * Special columns query.
 */
class special_columns_query : public query {
public:
    /**
     * Constructor.
     *
     * @param diag Diagnostics collector.
     * @param type Type.
     * @param catalog Catalog name.
     * @param schema Schema name.
     * @param table Table name.
     * @param scope Minimum required scope of the rowid.
     * @param nullable Determines whether to return special columns that can have a NULL value.
     */
    special_columns_query(diagnosable_adapter &diag, std::int16_t type, std::string catalog, std::string schema,
        std::string table, std::int16_t scope, std::int16_t nullable);

    /**
     * Destructor.
     */
    ~special_columns_query() override = default;

    /**
     * Execute query.
     *
     * @return True on success.
     */
    sql_result execute() override;

    /**
     * Fetch next result row to application buffers.
     *
     * @param column_bindings Application buffers to put data to.
     * @return Operation result.
     */
    sql_result fetch_next_row(column_binding_map &column_bindings) override;

    /**
     * Get data of the specified column in the result set.
     *
     * @param column_idx Column index.
     * @param buffer Buffer to put column data to.
     * @return Operation result.
     */
    sql_result get_column(std::uint16_t column_idx, application_data_buffer &buffer) override;

    /**
     * Close query.
     *
     * @return True on success.
     */
    sql_result close() override;

    /**
     * Get column metadata.
     *
     * @return Column metadata.
     */
    const protocol::column_meta_vector *get_meta() override { return &m_columns_meta; }

    /**
     * Check if data is available.
     *
     * @return True if data is available.
     */
    bool is_data_available() const override { return false; }

    /**
     * Get the number of rows affected by the statement.
     *
     * @return Number of rows affected by the statement.
     */
    std::int64_t affected_rows() const override { return 0; }

    /**
     * Move to the next result set.
     *
     * @return Operation result.
     */
    sql_result next_result_set() override { return sql_result::AI_NO_DATA; }

private:
    /** Query type. */
    std::int16_t m_type;

    /** Catalog name. */
    std::string m_catalog;

    /** Schema name. */
    std::string m_schema;

    /** Table name. */
    std::string m_table;

    /** Minimum required scope of the rowid. */
    std::int16_t m_scope;

    /** Determines whether to return special columns that can have a NULL value. */
    std::int16_t m_nullable;

    /** Query executed. */
    bool m_executed = false;

    /** Columns metadata. */
    protocol::column_meta_vector m_columns_meta;
};

} // namespace ignite
