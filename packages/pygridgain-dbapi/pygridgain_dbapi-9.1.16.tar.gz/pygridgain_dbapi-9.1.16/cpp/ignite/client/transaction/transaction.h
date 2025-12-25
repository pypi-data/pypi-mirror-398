/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/detail/config.h"
#include "ignite/common/ignite_result.h"

namespace ignite {

namespace detail {
class sql_impl;
class table_impl;
class transaction_impl;
class transactions_impl;
}

/**
 * @brief Ignite transaction.
 */
class transaction {
    friend class detail::sql_impl;
    friend class detail::table_impl;
    friend class detail::transactions_impl;

public:
    // Default
    transaction() = default;

    /**
     * Commits the transaction.
     */
    IGNITE_API void commit() {
        return sync<void>([this](const auto& callback) { commit_async(std::move(callback)); });
    }

    /**
     * Commits the transaction asynchronously.
     *
     * @param callback Callback to be called upon asynchronous operation completion.
     */
    IGNITE_API void commit_async(const ignite_callback<void> &callback);

    /**
     * Rollbacks the transaction.
     */
    IGNITE_API void rollback() {
        sync<void>([this](const auto& callback) { rollback_async(std::move(callback)); });
    }

    /**
     * Rollbacks the transaction asynchronously.
     *
     * @param callback Callback to be called upon asynchronous operation completion.
     */
    IGNITE_API void rollback_async(const ignite_callback<void> &callback);

private:
    /**
     * Constructor
     *
     * @param impl Implementation
     */
    explicit transaction(std::shared_ptr<detail::transaction_impl> impl)
        : m_impl(std::move(impl)) {}

    /** Implementation. */
    std::shared_ptr<detail::transaction_impl> m_impl;
};

} // namespace ignite
