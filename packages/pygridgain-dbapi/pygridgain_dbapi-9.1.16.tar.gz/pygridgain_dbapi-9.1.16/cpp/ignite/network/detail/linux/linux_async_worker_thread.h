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
#include "ignite/network/async_handler.h"
#include "ignite/network/detail/linux/connecting_context.h"
#include "ignite/network/detail/linux/linux_async_client.h"
#include "ignite/network/tcp_range.h"

#include <cstdint>
#include <ctime>
#include <memory>
#include <mutex>
#include <thread>

namespace ignite::network::detail {

class linux_async_client_pool;

/**
 * Async pool working thread.
 */
class linux_async_worker_thread {
public:
    /**
     * Default constructor.
     */
    explicit linux_async_worker_thread(linux_async_client_pool &client_pool);

    /**
     * Destructor.
     */
    ~linux_async_worker_thread();

    /**
     * Start worker thread.
     *
     * @param limit Connection limit.
     * @param addrs Addresses to connect to.
     */
    void start(size_t limit, std::vector<tcp_range> addrs);

    /**
     * Stop thread.
     */
    void stop();

private:
    /**
     * Run thread.
     */
    void run();

    /**
     * Initiate new connection process if needed.
     */
    void handle_new_connections();

    /**
     * Handle epoll events.
     */
    void handle_connection_events();

    /**
     * Handle network error during connection establishment.
     *
     * @param addr End point.
     * @param msg Error message.
     */
    void report_connection_error(const end_point &addr, std::string msg);

    /**
     * Handle failed connection.
     *
     * @param msg Error message.
     */
    void handle_connection_failed(std::string msg);

    /**
     * Handle network error on established connection.
     *
     * @param client Client instance.
     */
    void handle_connection_closed(linux_async_client *client);

    /**
     * Handle successfully established connection.
     *
     * @param client Client instance.
     */
    void handle_connection_success(linux_async_client *client);

    /**
     * Calculate connection timeout.
     *
     * @return Connection timeout.
     */
    [[nodiscard]] int calculate_connection_timeout() const;

    /**
     * Check whether new connection should be initiated.
     *
     * @return @c true if new connection should be initiated.
     */
    [[nodiscard]] bool should_initiate_new_connection() const;

    /** Client pool. */
    linux_async_client_pool &m_client_pool;

    /** Flag indicating that thread is stopping. */
    volatile bool m_stopping;

    /** Client epoll file descriptor. */
    int m_epoll;

    /** Stop event file descriptor. */
    int m_stop_event;

    /** Addresses to use for connection establishment. */
    std::vector<tcp_range> m_non_connected;

    /** Connection which is currently in connecting process. */
    std::unique_ptr<connecting_context> m_current_connection;

    /** Currently connected client. */
    std::shared_ptr<linux_async_client> m_current_client;

    /** Failed connection attempts. */
    size_t m_failed_attempts;

    /** Last connection time. */
    timespec m_last_connection_time;

    /** Minimal number of addresses. */
    size_t m_min_addrs;

    /** Thread. */
    std::thread m_thread;
};

} // namespace ignite::network::detail
