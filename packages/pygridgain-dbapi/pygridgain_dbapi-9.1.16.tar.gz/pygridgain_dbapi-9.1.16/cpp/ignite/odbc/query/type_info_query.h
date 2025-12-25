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
 * Type info query.
 */
class type_info_query : public query {
public:
    /**
     * Constructor.
     *
     * @param diag Diagnostics collector.
     * @param sql_type SQL type.
     */
    type_info_query(diagnosable_adapter &diag, std::int16_t sql_type);

    /**
     * Destructor.
     */
    ~type_info_query() override = default;

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
     * Check if data is available.
     *
     * @return True if data is available.
     */
    bool is_data_available() const override { return m_cursor != m_types.end(); }

    /**
     * Get the number of rows affected by the statement.
     *
     * @return Number of rows affected by the statement.
     */
    [[nodiscard]] std::int64_t affected_rows() const override { return 0; }

    /**
     * Move to the next result set.
     *
     * @return Operation result.
     */
    sql_result next_result_set() override { return sql_result::AI_NO_DATA; }

private:
    /** Columns metadata. */
    protocol::column_meta_vector m_columns_meta;

    /** An executed flag. */
    bool m_executed{false};

    /** Fetched flag. */
    bool m_fetched{false};

    /** Requested types. */
    std::vector<ignite_type> m_types;

    /** Query cursor. */
    std::vector<ignite_type>::const_iterator m_cursor{m_types.end()};
};

} // namespace ignite
