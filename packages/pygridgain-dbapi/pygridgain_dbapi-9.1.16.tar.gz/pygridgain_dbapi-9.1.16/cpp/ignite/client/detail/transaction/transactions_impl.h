/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/detail/cluster_connection.h"
#include "ignite/client/detail/transaction/transaction_impl.h"
#include "ignite/client/transaction/transaction_options.h"

#include "ignite/common/detail/config.h"
#include "ignite/common/ignite_result.h"

#include <memory>

namespace ignite::detail {

/**
 * Ignite transactions implementation.
 */
class transactions_impl {
public:
    // Default
    transactions_impl(transactions_impl &&) noexcept = default;
    transactions_impl &operator=(transactions_impl &&) noexcept = default;

    // Deleted
    transactions_impl() = delete;
    transactions_impl(const transactions_impl &) = delete;
    transactions_impl &operator=(const transactions_impl &) = delete;

    /**
     * Constructor.
     *
     * @param connection Connection.
     */
    explicit transactions_impl(std::shared_ptr<cluster_connection> connection)
        : m_connection(std::move(connection)) {}

    /**
     * Starts a new transaction asynchronously.
     *
     * @param callback Callback to be called with a new transaction or error upon completion of asynchronous operation.
     * @param tx_opts Transaction options.
     */
    IGNITE_API void begin_async(transaction_options tx_opts, ignite_callback<transaction> callback) {
        auto writer_func = [this, &tx_opts](protocol::writer &writer, auto) {
            writer.write_bool(tx_opts.is_read_only());
            writer.write(tx_opts.get_timeout_millis());
            writer.write(m_connection->get_observable_timestamp());
        };

        auto reader_func = [](protocol::reader &reader, std::shared_ptr<node_connection> conn) mutable -> transaction {
            auto id = reader.read_int64();

            return transaction(std::make_shared<transaction_impl>(id, std::move(conn)));
        };

        m_connection->perform_request<transaction>(
            protocol::client_operation::TX_BEGIN, std::move(writer_func), std::move(reader_func), std::move(callback));
    }

private:
    /** Cluster connection. */
    std::shared_ptr<cluster_connection> m_connection;
};

} // namespace ignite::detail
