/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/end_point.h"
#include <ignite/common/ignite_error.h>
#include <ignite/network/data_buffer.h>

#include <cstdint>
#include <optional>

namespace ignite::network {

/**
 * Asynchronous event handler.
 */
class async_handler {
public:
    /**
     * Destructor.
     */
    virtual ~async_handler() = default;

    /**
     * Callback that called on successful connection establishment.
     *
     * @param addr Address of the new connection.
     * @param id Connection ID.
     */
    virtual void on_connection_success(const end_point &addr, uint64_t id) = 0;

    /**
     * Callback that called on error during a connection establishment.
     *
     * @param addr Connection address.
     * @param err Error.
     */
    virtual void on_connection_error(const end_point &addr, ignite_error err) = 0;

    /**
     * Callback that called on error during a connection establishment.
     *
     * @param id Async client ID.
     * @param err Error. Can be null if connection closed without an error.
     */
    virtual void on_connection_closed(uint64_t id, std::optional<ignite_error> err) = 0;

    /**
     * Callback that called when a new message is received.
     *
     * @param id Async client ID.
     * @param msg Received message.
     */
    virtual void on_message_received(uint64_t id, bytes_view msg) = 0;

    /**
     * Callback that called when a message is sent.
     *
     * @param id Async client ID.
     */
    virtual void on_message_sent(uint64_t id) = 0;
};

} // namespace ignite::network
