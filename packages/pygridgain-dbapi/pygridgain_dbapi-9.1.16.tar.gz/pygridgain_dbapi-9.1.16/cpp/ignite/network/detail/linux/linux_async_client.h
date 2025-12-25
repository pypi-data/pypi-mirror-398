/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "sockets.h"

#include "ignite/common/end_point.h"
#include "ignite/network/async_handler.h"
#include "ignite/network/codec.h"
#include "ignite/network/tcp_range.h"

#include <cstdint>
#include <deque>
#include <memory>
#include <mutex>

namespace ignite::network::detail {

/**
 * Linux-specific implementation of async network client.
 */
class linux_async_client {
    /**
     * State.
     */
    enum class state {
        CONNECTED,

        SHUTDOWN,

        CLOSED,
    };

public:
    static constexpr size_t BUFFER_SIZE = 0x10000;

    /**
     * Constructor.
     *
     * @param fd Socket file descriptor.
     * @param addr Address.
     * @param range Range.
     */
    linux_async_client(int fd, end_point addr, tcp_range range);

    /**
     * Destructor.
     *
     * Should not be destructed from external threads.
     * Can be destructed from WorkerThread.
     */
    ~linux_async_client();

    /**
     * Shutdown client.
     *
     * Can be called from external threads.
     * Can be called from WorkerThread.
     *
     * @param err Error message. Can be null.
     * @return @c true if shutdown performed successfully.
     */
    bool shutdown(std::optional<ignite_error> err);

    /**
     * Close client.
     *
     * Should not be called from external threads.
     * Can be called from WorkerThread.
     *
     * @return @c true if shutdown performed successfully.
     */
    bool close();

    /**
     * Send packet using client.
     *
     * @param data Data to send.
     * @return @c true on success.
     */
    bool send(std::vector<std::byte> &&data);

    /**
     * Initiate next receive of data.
     *
     * @return @c true on success.
     */
    bytes_view receive();

    /**
     * Process sent data.
     *
     * @return @c true on success.
     */
    bool process_sent();

    /**
     * Start monitoring client.
     *
     * @param epoll Epoll file descriptor.
     * @return @c true on success.
     */
    bool start_monitoring(int epoll);

    /**
     * Stop monitoring client.
     */
    void stop_monitoring();

    /**
     * Enable epoll notifications.
     */
    void enable_send_notifications();

    /**
     * Disable epoll notifications.
     */
    void disable_send_notifications();

    /**
     * Get client ID.
     *
     * @return Client ID.
     */
    [[nodiscard]] uint64_t id() const { return m_id; }

    /**
     * Set ID.
     *
     * @param id ID to set.
     */
    void set_id(uint64_t id) { m_id = id; }

    /**
     * Get address.
     *
     * @return Address.
     */
    [[nodiscard]] const end_point &address() const { return m_addr; }

    /**
     * Get range.
     *
     * @return Range.
     */
    [[nodiscard]] const tcp_range &get_range() const { return m_range; }

    /**
     * Check whether client is closed.
     *
     * @return @c true if closed.
     */
    [[nodiscard]] bool is_closed() const { return m_state == state::CLOSED; }

    /**
     * Get closing error for the connection. Can be IGNITE_SUCCESS.
     *
     * @return Connection error.
     */
    [[nodiscard]] std::optional<ignite_error> get_close_error() const { return m_close_err; }

private:
    /**
     * Send next packet in queue.
     *
     * @warning Can only be called when holding m_send_mutex lock.
     * @return @c true on success.
     */
    bool send_next_packet_locked();

    /** State. */
    state m_state;

    /** Socket file descriptor. */
    int m_fd;

    /** Epoll file descriptor. */
    int m_epoll;

    /** Connection ID. */
    uint64_t m_id;

    /** Server end point. */
    end_point m_addr;

    /** Address range associated with current connection. */
    tcp_range m_range;

    /** Packets that should be sent. */
    std::deque<data_buffer_owning> m_send_packets;

    /** Send critical section. */
    std::mutex m_send_mutex;

    /** Packet that is currently received. */
    std::vector<std::byte> m_recv_packet;

    /** Closing error. */
    std::optional<ignite_error> m_close_err{};
};

} // namespace ignite::network::detail
