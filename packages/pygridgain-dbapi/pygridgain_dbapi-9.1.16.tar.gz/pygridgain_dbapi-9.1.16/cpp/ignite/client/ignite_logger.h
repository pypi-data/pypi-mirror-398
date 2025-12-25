/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <string_view>

namespace ignite {

/**
 * @brief Ignite logger interface.
 *
 * User can implement this class to use preferred logger with Ignite client.
 */
class ignite_logger {
public:
    // Default
    ignite_logger() = default;
    virtual ~ignite_logger() = default;

    // Deleted.
    ignite_logger(ignite_logger &&) = delete;
    ignite_logger(const ignite_logger &) = delete;
    ignite_logger &operator=(ignite_logger &&) = delete;
    ignite_logger &operator=(const ignite_logger &) = delete;

    /**
     * Used to log error messages.
     *
     * @param message Error message.
     */
    virtual void log_error(std::string_view message) = 0;

    /**
     * Used to log warning messages.
     *
     * @param message Warning message.
     */
    virtual void log_warning(std::string_view message) = 0;

    /**
     * Used to log info messages.
     *
     * @param message Info message.
     */
    virtual void log_info(std::string_view message) = 0;

    /**
     * Used to log debug messages.
     *
     * It is recommended to disable debug logging by default for the sake of performance.
     *
     * @param message Debug message.
     */
    virtual void log_debug(std::string_view message) = 0;

    /**
     * Check whether debug is enabled.
     * @return
     */
    [[nodiscard]] virtual bool is_debug_enabled() const = 0;
};

} // namespace ignite
