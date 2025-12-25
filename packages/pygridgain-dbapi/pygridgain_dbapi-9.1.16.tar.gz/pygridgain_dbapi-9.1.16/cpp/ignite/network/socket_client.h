/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <cstddef>
#include <cstdint>

namespace ignite::network {

/**
 * Socket client implementation.
 */
class socket_client {
public:
    /**
     * Non-negative timeout operation result.
     */
    enum wait_result {
        /** Timeout. */
        TIMEOUT = 0,

        /** Success. */
        SUCCESS = 1
    };

    // Default
    virtual ~socket_client() = default;

    /**
     * Establish connection with remote service.
     *
     * @param hostname Remote host name.
     * @param port Service port.
     * @param timeout Timeout.
     * @return @c true on success and @c false on timeout.
     */
    virtual bool connect(const char *hostname, std::uint16_t port, std::int32_t timeout) = 0;

    /**
     * Close established connection.
     */
    virtual void close() = 0;

    /**
     * Send data by established connection.
     *
     * @param data Pointer to data to be sent.
     * @param size Size of the data in bytes.
     * @param timeout Timeout.
     * @return Number of bytes that have been sent on success,
     *     wait_result::TIMEOUT on timeout and -errno on failure.
     */
    virtual int send(const std::byte *data, std::size_t size, std::int32_t timeout) = 0;

    /**
     * Receive data from established connection.
     *
     * @param buffer Pointer to data buffer.
     * @param size Size of the buffer in bytes.
     * @param timeout Timeout.
     * @return Number of bytes that have been received on success,
     *     wait_result::TIMEOUT on timeout and -errno on failure.
     */
    virtual int receive(std::byte *buffer, std::size_t size, std::int32_t timeout) = 0;

    /**
     * Check if the socket is blocking or not.
     *
     * @return @c true if the socket is blocking and false otherwise.
     */
    [[nodiscard]] virtual bool is_blocking() const = 0;
};

} // namespace ignite::network
