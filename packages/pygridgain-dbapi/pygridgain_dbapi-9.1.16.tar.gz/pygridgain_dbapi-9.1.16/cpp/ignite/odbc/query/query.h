/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/odbc/common_types.h"
#include "ignite/odbc/diagnostic/diagnosable_adapter.h"
#include "ignite/protocol/sql/column_meta.h"

#include <cstdint>

namespace ignite {

/** Query type. */
enum class query_type {
    /** Data query type. */
    DATA,

    /** Batch query type. */
    BATCH,

    /** Table metadata. */
    TABLE_METADATA,

    /** Column metadata. */
    COLUMN_METADATA,

    /** Type info. */
    TYPE_INFO,

    /** Foreign keys. */
    FOREIGN_KEYS,

    /** Primary keys. */
    PRIMARY_KEYS,

    /** Special columns. */
    SPECIAL_COLUMNS,
};

/**
 * Query.
 */
class query {
public:
    /**
     * Virtual destructor
     */
    virtual ~query() = default;

    /**
     * Execute query.
     *
     * @return Execution result.
     */
    virtual sql_result execute() = 0;

    /**
     * Fetch next result row to application buffers.
     *
     * @param column_bindings Application buffers to put data to.
     * @return Operation result.
     */
    virtual sql_result fetch_next_row(column_binding_map &column_bindings) = 0;

    /**
     * Get data of the specified column in the result set.
     *
     * @param column_idx Column index.
     * @param buffer Buffer to put column data to.
     * @return Operation result.
     */
    virtual sql_result get_column(std::uint16_t column_idx, application_data_buffer &buffer) = 0;

    /**
     * Close query.
     *
     * @return Operation result.
     */
    virtual sql_result close() = 0;

    /**
     * Get column metadata.
     *
     * @return Column metadata.
     */
    [[nodiscard]] virtual const protocol::column_meta_vector *get_meta() {
        static const protocol::column_meta_vector empty;

        return &empty;
    }

    /**
     * Check if data is available.
     *
     * @return True if data is available.
     */
    [[nodiscard]] virtual bool is_data_available() const = 0;

    /**
     * Get number of rows affected by the statement.
     *
     * @return Number of rows affected by the statement.
     */
    [[nodiscard]] virtual std::int64_t affected_rows() const = 0;

    /**
     * Move to the next result set.
     *
     * @return Operation result.
     */
    virtual sql_result next_result_set() = 0;

    /**
     * Get query type.
     *
     * @return Query type.
     */
    [[nodiscard]] query_type get_type() const { return m_type; }

protected:
    /**
     * Constructor.
     */
    query(diagnosable_adapter &diag, query_type type)
        : m_diag(diag)
        , m_type(type) {}

    /** Diagnostics collector. */
    diagnosable_adapter &m_diag;

    /** Query type. */
    query_type m_type;
};

} // namespace ignite
