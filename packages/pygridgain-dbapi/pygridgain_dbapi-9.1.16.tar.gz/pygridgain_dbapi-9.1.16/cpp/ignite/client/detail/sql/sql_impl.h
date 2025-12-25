/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/cancellation_token.h"
#include "ignite/client/detail/cluster_connection.h"
#include "ignite/client/sql/result_set.h"
#include "ignite/client/sql/sql_statement.h"
#include "ignite/client/transaction/transaction.h"
#include "ignite/common/primitive.h"

#include <memory>
#include <utility>

namespace ignite::detail {

/**
 * Ignite SQL query facade.
 */
class sql_impl {
public:
    // Default
    sql_impl(sql_impl &&) noexcept = default;
    sql_impl &operator=(sql_impl &&) noexcept = default;

    // Deleted
    sql_impl() = delete;
    sql_impl(const sql_impl &) = delete;
    sql_impl &operator=(const sql_impl &) = delete;

    /**
     * Constructor.
     *
     * @param connection Connection.
     */
    explicit sql_impl(std::shared_ptr<cluster_connection> connection)
        : m_connection(std::move(connection)) {}

    /**
     * Executes a single SQL statement and returns rows.
     *
     * @param tx Optional transaction. If nullptr implicit transaction for this
     *   single operation is used.
     * @param token Cancellation token.
     * @param statement Statement to execute.
     * @param args Arguments for the statement.
     * @param callback A callback called on operation completion with SQL result set.
     */
    void execute_async(transaction *tx, cancellation_token *token, const sql_statement &statement,
        std::vector<primitive> &&args, ignite_callback<result_set> &&callback);

    /**
     * Executes a multi-statement SQL query asynchronously.
     *
     * @param token Cancellation token.
     * @param statement Statement to execute.
     * @param args Arguments for the template (can be empty).
     * @param callback A callback called on operation completion with SQL result set.
     */
    void execute_script_async(cancellation_token *token, const sql_statement &statement, std::vector<primitive> &&args,
        ignite_callback<void> &&callback);

private:
    /** Cluster connection. */
    std::shared_ptr<cluster_connection> m_connection;
};

} // namespace ignite::detail
