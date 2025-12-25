/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/network/socket_client.h>
#include <ignite/network/ssl/secure_configuration.h>

#include <cstdint>
#include <string>
#include <utility>

namespace ignite::network
{

/**
 * Secure socket client.
 */
class secure_socket_client : public socket_client
{
public:
    /**
     * Constructor.
     *
     * @param cfg Secure configuration.
     */
    explicit secure_socket_client(secure_configuration  cfg) : m_cfg(std::move(cfg)) {}

    /**
     * Destructor.
     */
    ~secure_socket_client() override;

    /**
     * Establish connection with the host.
     *
     * @param hostname Host name or address.
     * @param port TCP port.
     * @param timeout Timeout in seconds.
     * @return @c true on success and @c false on timeout.
     */
    bool connect(const char* hostname, std::uint16_t port, std::int32_t timeout) override;

    /**
     * Close the connection.
     */
    void close() override;

    /**
     * Send data using connection.
     * @param data Data to send.
     * @param size Number of bytes to send.
     * @param timeout Timeout in seconds.
     * @return Number of bytes that have been sent on success,
     *     WaitResult::TIMEOUT on timeout and -errno on failure.
     */
    int send(const std::byte* data, std::size_t size, std::int32_t timeout) override;

    /**
     * Receive data from established connection.
     *
     * @param buffer Pointer to data buffer.
     * @param size Size of the buffer in bytes.
     * @param timeout Timeout in seconds.
     * @return Number of bytes that have been received on success,
     *     WaitResult::TIMEOUT on timeout and -errno on failure.
     */
    int receive(std::byte* buffer, std::size_t size, std::int32_t timeout) override;

    /**
     * Check if the socket is blocking or not.
     * @return @c true if the socket is blocking and false otherwise.
     */
    [[nodiscard]] bool is_blocking() const override {
        return m_blocking;
    }

private:
    /**
     * Close the connection.
     * Internal call.
     */
    void close_internal();

    /**
     * Wait on the socket for any event for specified time.
     * This function uses poll to achive timeout functionality
     * for every separate socket operation.
     *
     * @param ssl SSL instance.
     * @param timeout Timeout in seconds.
     * @param rd Wait for read if @c true, or for write if @c false.
     * @return -errno on error, WaitResult::TIMEOUT on timeout and
     *     WaitResult::SUCCESS on success.
     */
    static int wait_on_socket(void* ssl, std::int32_t timeout, bool rd);

    /**
     * Wait on the socket if it's required by SSL.
     *
     * @param res Operation result.
     * @param ssl SSl instance.
     * @param timeout Timeout in seconds.
     * @return
     */
    static int wait_on_socket_if_needed(int res, void* ssl, int timeout);

    /**
     * Make new SSL instance.
     *
     * @param context SSL context.
     * @param hostname Host name or address.
     * @param port TCP port.
     * @param blocking Indicates if the resulted SSL is blocking or not.
     * @return New SSL instance on success and null-pointer on fail.
     */
    static void* make_ssl(void* context, const char* hostname, std::uint16_t port, bool& blocking);

    /**
     * Complete async connect.
     *
     * @param ssl SSL instance.
     * @param timeout Timeout in seconds.
     * @return @c true on success and @c false on timeout.
     */
    static bool complete_connect_internal(void* ssl, int timeout);

    /** Secure configuration. */
    secure_configuration m_cfg;

    /** SSL context. */
    void* m_context{nullptr};

    /** OpenSSL BIO interface */
    void* m_bio{nullptr};

    /** Blocking flag. */
    bool m_blocking{true};
};

} // namespace ignite::network
