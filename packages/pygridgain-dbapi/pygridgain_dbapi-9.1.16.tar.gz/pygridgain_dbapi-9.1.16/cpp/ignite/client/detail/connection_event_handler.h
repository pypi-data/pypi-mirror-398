/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <cstdint>

namespace ignite::detail {

class node_connection;

/**
 * Socket event handler.
 */
class connection_event_handler {
public:
    // Default
    connection_event_handler() = default;
    virtual ~connection_event_handler() = default;

    // Deleted
    connection_event_handler(connection_event_handler &&) = delete;
    connection_event_handler(const connection_event_handler &) = delete;
    connection_event_handler &operator=(connection_event_handler &&) = delete;
    connection_event_handler &operator=(const connection_event_handler &) = delete;

    /**
     * Handle observable timestamp.
     *
     * @param timestamp Timestamp.
     */
    virtual void on_observable_timestamp_changed(std::int64_t timestamp) = 0;

    /**
     * Handle partition assignment change.
     *
     * @param timestamp Assignment timestamp.
     */
    virtual void on_partition_assignment_changed(std::int64_t timestamp) = 0;
};

} // namespace ignite::detail
