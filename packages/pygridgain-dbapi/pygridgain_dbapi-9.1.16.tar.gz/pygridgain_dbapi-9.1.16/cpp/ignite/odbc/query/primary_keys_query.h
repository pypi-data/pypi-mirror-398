/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/odbc/meta/primary_key_meta.h"
#include "ignite/odbc/query/query.h"
#include "ignite/odbc/sql_connection.h"

namespace ignite {

/**
 * Primary keys query.
 */
class primary_keys_query : public query {
public:
    /**
     * Constructor.
     *
     * @param diag Diagnostics collector.
     * @param connection Statement-associated connection.
     * @param schema Schema name.
     * @param table Table name.
     */
    primary_keys_query(diagnosable_adapter &diag, sql_connection &connection, std::string schema, std::string table);

    /**
     * Destructor.
     */
    ~primary_keys_query() override = default;

    /**
     * Execute query.
     *
     * @return True on success.
     */
    sql_result execute() override;

    /**
     * Get column metadata.
     *
     * @return Column metadata.
     */
    const protocol::column_meta_vector *get_meta() override { return &m_columns_meta; }

    /**
     * Fetch next result row to application buffers.
     *
     * @return Operation result.
     */
    sql_result fetch_next_row(column_binding_map &column_bindings) override;

    /**
     * Get data of the specified column in the result set.
     *
     * @param columnIdx Column index.
     * @param buffer Buffer to put column data to.
     * @return Operation result.
     */
    sql_result get_column(std::uint16_t columnIdx, application_data_buffer &buffer) override;

    /**
     * Close query.
     *
     * @return True on success.
     */
    sql_result close() override;

    /**
     * Check if data is available.
     *
     * @return True if data is available.
     */
    bool is_data_available() const override { return m_cursor != m_meta.end(); }

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
    /**
     * Make get primary keys requests and use response to set internal state.
     *
     * @return Operation result.
     */
    sql_result make_request_get_primary_keys();

    /** Connection associated with the statement. */
    sql_connection &m_connection;

    /** Schema name. */
    std::string m_schema;

    /** Table name. */
    std::string m_table;

    /** Query executed. */
    bool m_executed{false};

    /** A flag indicating whether a result set was fetched. */
    bool m_fetched{false};

    /** Columns metadata. */
    protocol::column_meta_vector m_columns_meta;

    /** Primary keys metadata. */
    primary_key_meta_vector m_meta;

    /** Result set cursor. */
    primary_key_meta_vector::iterator m_cursor;
};

} // namespace ignite
