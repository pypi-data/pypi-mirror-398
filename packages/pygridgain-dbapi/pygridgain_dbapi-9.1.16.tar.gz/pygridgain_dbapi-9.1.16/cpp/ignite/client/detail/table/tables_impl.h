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
#include "ignite/client/table/table.h"

#include <memory>

namespace ignite::detail {

/**
 * Table management.
 */
class tables_impl {
public:
    // Deleted
    tables_impl(tables_impl &&) = delete;
    tables_impl(const tables_impl &) = delete;
    tables_impl &operator=(tables_impl &&) = delete;
    tables_impl &operator=(const tables_impl &) = delete;

    /**
     * Constructor.
     *
     * @param connection Connection.
     */
    explicit tables_impl(std::shared_ptr<cluster_connection> connection)
        : m_connection(std::move(connection)) {}

    /**
     * Gets a table by name.
     * See tables::get_table_async() for details.
     *
     * @param name Table name.
     * @param callback Callback.
     * @throw ignite_error In case of error while trying to send a request.
     */
    void get_table_async(std::string_view name, ignite_callback<std::optional<table>> callback);

    /**
     * Gets a table by name.
     * See tables::get_table_async() for details.
     *
     * @param name Table name.
     * @param callback Callback.
     * @throw ignite_error In case of error while trying to send a request.
     */
    void get_table_async(const qualified_name &name, ignite_callback<std::optional<table>> callback);

    /**
     * Gets all tables.
     *
     * @param callback Callback to be called once operation is complete. On success, the callback is invoked with
     *    a vector of all tables.
     * @throw ignite_error In case of error while trying to send a request.
     */
    void get_tables_async(ignite_callback<std::vector<table>> callback);

private:
    /** Cluster connection. */
    std::shared_ptr<cluster_connection> m_connection;
};

} // namespace ignite::detail
