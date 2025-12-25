/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/ignite_logger.h"

#include <memory>

namespace ignite::detail {

/** Protocol version. */
class logger_wrapper : public ignite_logger {
public:
    /**
     * Constructor.
     *
     * @param logger Logger.
     */
    logger_wrapper(std::shared_ptr<ignite_logger> logger)
        : m_logger(std::move(logger)) {}

    /**
     * Used to log error messages.
     *
     * @param message Error message.
     */
    void log_error(std::string_view message) override {
        if (m_logger)
            m_logger->log_error(message);
    }

    /**
     * Used to log warning messages.
     *
     * @param message Warning message.
     */
    void log_warning(std::string_view message) override {
        if (m_logger)
            m_logger->log_warning(message);
    }

    /**
     * Used to log info messages.
     *
     * @param message Info message.
     */
    void log_info(std::string_view message) override {
        if (m_logger)
            m_logger->log_info(message);
    }

    /**
     * Used to log debug messages.
     *
     * It is recommended to disable debug logging by default for the sake of performance.
     *
     * @param message Debug message.
     */
    void log_debug(std::string_view message) override {
        if (m_logger)
            m_logger->log_debug(message);
    }

    /**
     * Check whether debug is enabled.
     * @return
     */
    [[nodiscard]] bool is_debug_enabled() const override { return m_logger && m_logger->is_debug_enabled(); }

private:
    /** Logger. */
    std::shared_ptr<ignite_logger> m_logger;
};

} // namespace ignite::detail
