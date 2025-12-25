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
#include "ignite/network/detail/linux/linux_async_client.h"
#include "ignite/network/tcp_range.h"

#include <cstdint>
#include <memory>

#include <netdb.h>

namespace ignite::network::detail {

/**
 * Connecting context.
 */
class connecting_context {
public:
    // Default
    connecting_context(connecting_context &&) = default;
    connecting_context &operator=(connecting_context &&) = default;

    /**
     * Constructor.
     */
    explicit connecting_context(tcp_range range);

    /**
     * Destructor.
     */
    ~connecting_context();

    /**
     * reset connection context to it's initial state.
     */
    void reset();

    /**
     * Next address in range.
     *
     * @return Next address info for connection.
     */
    addrinfo *next();

    /**
     * Get last address.
     *
     * @return Address.
     */
    end_point current_address() const;

    /**
     * Make client.
     *
     * @param fd Socket file descriptor.
     * @return Client instance from current internal state.
     */
    std::shared_ptr<linux_async_client> to_client(int fd);

private:
    /** Range. */
    tcp_range m_range;

    /** Next port. */
    uint16_t m_next_port;

    /** Current address info. */
    addrinfo *m_info;

    /** Address info which is currently used for connection */
    addrinfo *m_current_info;
};

} // namespace ignite::network::detail
