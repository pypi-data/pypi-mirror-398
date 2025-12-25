/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/network/async_handler.h>
#include <ignite/network/data_sink.h>
#include <ignite/network/tcp_range.h>

#include <cstdint>
#include <memory>
#include <vector>

namespace ignite::network {

/**
 * Asynchronous client pool.
 */
class async_client_pool : public data_sink {
public:
    // Default
    ~async_client_pool() override = default;

    /**
     * Start internal thread that establishes connections to provided addresses and asynchronously sends and
     * receives messages from them. Function returns either when thread is started and first connection is
     * established or failure happened.
     *
     * @param addrs Addresses to connect to.
     * @param conn_limit Connection upper limit. Zero means limit is disabled.
     *
     * @throw ignite_error on error.
     */
    virtual void start(std::vector<tcp_range> addrs, uint32_t conn_limit) = 0;

    /**
     * Close all established connections and stops handling threads.
     */
    virtual void stop() = 0;

    /**
     * Set handler.
     *
     * @param handler Handler to set.
     */
    virtual void set_handler(std::weak_ptr<async_handler> handler) = 0;
};

} // namespace ignite::network
