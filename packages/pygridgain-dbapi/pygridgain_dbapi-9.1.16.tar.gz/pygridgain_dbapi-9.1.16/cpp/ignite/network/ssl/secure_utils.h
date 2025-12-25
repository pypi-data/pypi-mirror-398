/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/network/ssl/secure_configuration.h>
#include <ignite/network/ssl/ssl_gateway.h>

namespace ignite::network {

enum
{
    /** OpenSSL functions return this code on success. */
    SSL_OPERATION_SUCCESS = 1,
};

/**
 * Make SSL context using configuration.
 *
 * @param cfg Configuration to use.
 * @return New context instance on success.
 * @throw ignite_error on error.
 */
SSL_CTX* make_context(const secure_configuration &cfg);

/**
 * Free context.
 *
 * @param ctx Context to free.
 */
void free_context(SSL_CTX* ctx);

/**
 * Check whether error is actual error or code returned when used in async environment.
 *
 * @param err Error obtained with SSL_get_error.
 * @return @c true if the code returned on actual error.
 */
bool is_actual_error(int err);

/**
 * Throw SSL-related error.
 *
 * @param err Error message.
 */
void throw_secure_error(std::string err);

/**
 * Get SSL-related error in text format.
 *
 * @param err Error message in human-readable format.
 */
std::string get_last_secure_error();

/**
 * Try extract from OpenSSL error stack and throw SSL-related error.
 *
 * @param description Error description.
 * @param advice User advice.
 */
void throw_last_secure_error(const std::string& description, const std::string& advice);

/**
 * Try extract from OpenSSL error stack and throw SSL-related error.
 *
 * @param description Error description.
 */
void throw_last_secure_error(const std::string& description);

} // namespace ignite::network
