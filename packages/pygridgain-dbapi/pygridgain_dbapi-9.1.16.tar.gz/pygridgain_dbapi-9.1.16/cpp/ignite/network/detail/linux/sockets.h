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
#include <string>

#ifndef SOCKET_ERROR
# define SOCKET_ERROR (-1)
#endif // SOCKET_ERROR

namespace ignite::network::detail {

/**
 * Get socket error message for the error code.
 * @param error Error code.
 * @return Socket error message string.
 */
std::string get_socket_error_message(int error);

/**
 * Get last socket error message.
 * @return Last socket error message string.
 */
std::string get_last_socket_error_message();

/**
 * Try and set socket options.
 *
 * @param socket_fd Socket file descriptor.
 * @param buf_size Buffer size.
 * @param no_delay Set no-delay mode.
 * @param out_of_band Set out-of-Band mode.
 * @param keep_alive Keep alive mode.
 */
void try_set_socket_options(int socket_fd, int buf_size, bool no_delay, bool out_of_band, bool keep_alive);

/**
 * Wait on the socket for any event for specified time.
 * This function uses poll to achieve timeout functionality for every separate socket operation.
 *
 * @param socket Socket handle.
 * @param timeout Timeout.
 * @param rd Wait for read if @c true, or for write if @c false.
 * @return -errno on error, wait_result::TIMEOUT on timeout and wait_result::SUCCESS on success.
 */
int wait_on_socket(int socket, std::int32_t timeout, bool rd);

/**
 * Set non blocking mode for socket.
 *
 * @param socket_fd Socket file descriptor.
 * @param non_blocking Non-blocking mode.
 */
bool set_non_blocking_mode(int socket_fd, bool non_blocking);

} // namespace ignite::network::detail
