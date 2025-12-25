/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/network/async_client_pool.h>
#include <ignite/network/data_filter.h>
#include <ignite/network/socket_client.h>
#include <ignite/network/ssl/secure_configuration.h>

#include <string>

namespace ignite::network {

/**
 * Make basic TCP socket.
 */
std::unique_ptr<socket_client> make_tcp_socket_client();

/**
 * Make asynchronous client pool.
 *
 * @param filters Filters.
 * @return Async client pool.
 */
std::shared_ptr<async_client_pool> make_async_client_pool(data_filters filters);

/**
 * Ensure that SSL library is loaded.
 *
 * Called implicitly when secure_socket is created, so there is no need to call this function explicitly.
 *
 * @throw ignite_error if it is not possible to load SSL library.
 */
void ensure_ssl_loaded();

/**
 * Make secure socket for SSL/TLS connection.
 *
 * @param cfg Configuration.
 *
 * @throw ignite_error if it is not possible to load SSL library.
 */
std::unique_ptr<socket_client> make_secure_socket_client(secure_configuration cfg);

} // namespace ignite::network
