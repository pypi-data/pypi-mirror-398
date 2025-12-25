/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/cancel_handle.h"
#include "ignite/client/sql/result_set.h"
#include "ignite/client/sql/sql_statement.h"
#include "ignite/client/transaction/transaction.h"
#include "ignite/common/detail/config.h"
#include "ignite/common/ignite_result.h"
#include "ignite/common/primitive.h"

#include <memory>
#include <utility>

namespace ignite {

namespace detail {
class sql_impl;
}

/**
 * @brief Ignite SQL query API facade.
 */
class sql {
    friend class ignite_client;

public:
    // Delete
    sql() = delete;

    /**
     * Executes a single SQL statement asynchronously and returns rows.
     *
     * @param tx Optional transaction. If nullptr implicit transaction for this single operation is used.
     * @param token Cancellation token. Can be @c nullptr.
     * @param statement Statement to execute.
     * @param args Arguments for the statement (can be empty).
     * @param callback A callback called on operation completion with SQL result set.
     */
    IGNITE_API void execute_async(transaction *tx, cancellation_token *token, const sql_statement &statement,
        std::vector<primitive> args, ignite_callback<result_set> callback);

    /**
     * Executes a single SQL statement and returns rows.
     *
     * @param tx Optional transaction. If nullptr implicit transaction for this single operation is used.
     * @param token Cancellation token. Can be @c nullptr.
     * @param statement Statement to execute.
     * @param args Arguments for the statement (can be empty).
     * @return SQL result set.
     */
    IGNITE_API result_set execute(transaction *tx, cancellation_token *token, const sql_statement &statement,
        std::vector<primitive> args) {
        return sync<result_set>(
            [this, tx, token, &statement, args = std::move(args)](auto callback) mutable {
                execute_async(tx, token, statement, std::move(args), std::move(callback));
            }
        );
    }

    /**
     * Executes a multi-statement SQL query asynchronously.
     *
     * @param token Cancellation token. Can be @c nullptr.
     * @param statement Statement to execute.
     * @param args Arguments for the template (can be empty).
     * @param callback A callback called on operation completion with SQL result set.
     */
    IGNITE_API void execute_script_async(cancellation_token *token, const sql_statement &statement,
        std::vector<primitive> args, ignite_callback<void> callback);

    /**
     * Executes a multi-statement SQL query.
     *
     * @param token Cancellation token. Can be @c nullptr.
     * @param statement Statement to execute.
     * @param args Arguments for the template (can be empty).
     */
    IGNITE_API void execute_script(cancellation_token *token, const sql_statement &statement,
        std::vector<primitive> args) {
        sync<void>([this, token, &statement, args = std::move(args)](auto callback) mutable {
            execute_script_async(token, statement, std::move(args), std::move(callback));
        });
    }

private:
    /**
     * Constructor
     *
     * @param impl Implementation
     */
    explicit sql(std::shared_ptr<detail::sql_impl> impl)
        : m_impl(std::move(impl)) {}

    /** Implementation. */
    std::shared_ptr<detail::sql_impl> m_impl;
};

} // namespace ignite
