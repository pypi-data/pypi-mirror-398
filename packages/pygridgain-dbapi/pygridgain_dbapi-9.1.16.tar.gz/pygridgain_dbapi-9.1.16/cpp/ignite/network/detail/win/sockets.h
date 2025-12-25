/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#define WIN32_LEAN_AND_MEAN
#define _WINSOCKAPI_ // NOLINT(bugprone-reserved-identifier)

// clang-format off
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <mstcpip.h>
// clang-format on

#include <string>

namespace ignite::network::detail {

/**
 * Get socket error message for the error code.
 * @param error Error code.
 * @return Socket error message string.
 */
std::string get_socket_error_message(HRESULT error);

/**
 * Get last socket error message.
 * @return Last socket error message string.
 */
std::string get_last_socket_error_message();

/**
 * Try and set socket options.
 *
 * @param socket Socket.
 * @param buf_size Buffer size.
 * @param no_delay Set no-delay mode.
 * @param out_of_band Set out-of-Band mode.
 * @param keep_alive Keep alive mode.
 */
void try_set_socket_options(SOCKET socket, int buf_size, BOOL no_delay, BOOL out_of_band, BOOL keep_alive);

/**
 * Set non blocking mode for socket.
 *
 * @param socket_handle Socket file descriptor.
 * @param non_blocking Non-blocking mode.
 */
bool set_non_blocking_mode(SOCKET socket_handle, bool non_blocking);

/**
 * Wait on the socket for any event for specified time.
 * This function uses poll to achieve timeout functionality for every separate socket operation.
 *
 * @param socket Socket handle.
 * @param timeout Timeout.
 * @param rd Wait for read if @c true, or for write if @c false.
 * @return -errno on error, wait_result::TIMEOUT on timeout and wait_result::SUCCESS on success.
 */
int wait_on_socket(SOCKET socket, std::int32_t timeout, bool rd);

/**
 * Init windows sockets.
 *
 * Thread-safe.
 */
void init_wsa();

} // namespace ignite::network::detail
