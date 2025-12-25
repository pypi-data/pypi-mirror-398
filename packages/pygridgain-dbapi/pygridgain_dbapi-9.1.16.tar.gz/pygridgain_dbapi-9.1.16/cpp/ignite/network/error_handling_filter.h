/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/network/data_filter_adapter.h>

#include <functional>

namespace ignite::network {

/**
 * Filter that handles exceptions thrown by upper level handlers.
 */
class error_handling_filter : public data_filter_adapter {
public:
    /**
     * Callback that called on successful connection establishment.
     *
     * @param addr Address of the new connection.
     * @param id Connection ID.
     */
    void on_connection_success(const end_point &addr, uint64_t id) override;

    /**
     * Callback that called on error during connection establishment.
     *
     * @param addr Connection address.
     * @param err Error.
     */
    void on_connection_error(const end_point &addr, ignite_error err) override;

    /**
     * Callback that called on error during connection establishment.
     *
     * @param id Async client ID.
     * @param err Error. Can be null if connection closed without error.
     */
    void on_connection_closed(uint64_t id, std::optional<ignite_error> err) override;

    /**
     * Callback that called when new message is received.
     *
     * @param id Async client ID.
     * @param msg Received message.
     */
    void on_message_received(uint64_t id, bytes_view msg) override;

    /**
     * Callback that called when message is sent.
     *
     * @param id Async client ID.
     */
    void on_message_sent(uint64_t id) override;

private:
    /**
     * Execute function and handle all possible exceptions.
     *
     * @param id Async client ID.
     * @param func Function to handle;
     */
    void close_connection_on_exception(uint64_t id, const std::function<void()> &func);
};

} // namespace ignite::network
