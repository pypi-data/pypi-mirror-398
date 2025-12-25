/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/client/ignite_logger.h>

#include <gtest/gtest.h>

#include <chrono>
#include <memory>
#include <sstream>
#include <string>

namespace ignite {

/**
 * Test logger.
 */
class gtest_logger : public ignite_logger {
public:
    /**
     * Construct.
     *
     * @param includeTs Include timestamps.
     * @param debug Enable debug.
     */
    gtest_logger(bool includeTs, bool debug)
        : m_includeTs(includeTs)
        , m_debug(debug) {}

    void log_error(std::string_view message) override {
        std::cout << "[          ] [ ERROR ]   " + get_timestamp() + std::string(message) + '\n' << std::flush;
    }

    void log_warning(std::string_view message) override {
        std::cout << "[          ] [ WARNING ] " + get_timestamp() + std::string(message) + '\n' << std::flush;
    }

    void log_info(std::string_view message) override {
        std::cout << "[          ] [ INFO ]    " + get_timestamp() + std::string(message) + '\n' << std::flush;
    }

    void log_debug(std::string_view message) override {
        if (m_debug)
            std::cout << "[          ] [ DEBUG ]   " + get_timestamp() + std::string(message) + '\n' << std::flush;
    }

    [[nodiscard]] bool is_debug_enabled() const override { return m_debug; }

    void set_debug_enabled(bool enabled) { m_debug = enabled; }

private:
    /**
     * Get timestamp in string format.
     *
     * @return Timestamp string.
     */
    [[nodiscard]] std::string get_timestamp() const {
        if (!m_includeTs)
            return {};

        using clock = std::chrono::system_clock;

        auto now = clock::now();
        auto cTime = clock::to_time_t(now);

        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch());

        std::stringstream ss;
        ss << std::put_time(std::localtime(&cTime), "%H:%M:%S.") << std::setw(3) << std::setfill('0')
           << (ms.count() % 1000) << " ";
        return ss.str();
    }

    /** Include timestamps. */
    bool m_includeTs;

    /** Include debug messages. */
    bool m_debug;
};

} // namespace ignite
