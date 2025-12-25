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
#include <optional>
#include <string>

namespace ignite::network {

/**
 * TCP port range.
 */
struct tcp_range {
    // Default
    tcp_range() = default;

    /**
     * Parse string and try to get TcpRange.
     *
     * @param str String to parse.
     * @param defPort Default port.
     * @return TcpRange instance on success and none on failure.
     */
    static std::optional<tcp_range> parse(std::string_view str, uint16_t def_port);

    /**
     * Constructor.
     *
     * @param host Host.
     * @param port Port.
     * @param range Number of ports after the @c port that
     *    should be tried if the previous are unavailable.
     */
    tcp_range(std::string host, uint16_t port, uint16_t range = 0)
        : host(std::move(host))
        , port(port)
        , range(range) {}

    /**
     * compare to another instance.
     *
     * @param other Another instance.
     * @return Negative value if less, positive if larger and
     *    zero, if equals another instance.
     */
    [[nodiscard]] int compare(const tcp_range &other) const;

    /**
     * Check whether empty.
     *
     * @return @c true if empty.
     */
    [[nodiscard]] bool empty() const { return host.empty(); }

    /**
     * Convert to string.
     *
     * @return String representation.
     */
    [[nodiscard]] std::string to_string() const {
        return host + ':' + std::to_string(port) + ".." + std::to_string(port + range);
    }

    /** Remote host. */
    std::string host;

    /** TCP port. */
    uint16_t port{0};

    /** Number of ports after the port that should be tried if the previous are unavailable. */
    uint16_t range{0};
};

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if equal.
 */
inline bool operator==(const tcp_range &val1, const tcp_range &val2) {
    return val1.port == val2.port && val1.range == val2.range && val1.host == val2.host;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if not equal.
 */
inline bool operator!=(const tcp_range &val1, const tcp_range &val2) {
    return !(val1 == val2);
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if less.
 */
inline bool operator<(const tcp_range &val1, const tcp_range &val2) {
    return val1.compare(val2) < 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if less or equal.
 */
inline bool operator<=(const tcp_range &val1, const tcp_range &val2) {
    return val1.compare(val2) <= 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if greater.
 */
inline bool operator>(const tcp_range &val1, const tcp_range &val2) {
    return val1.compare(val2) > 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if greater or equal.
 */
inline bool operator>=(const tcp_range &val1, const tcp_range &val2) {
    return val1.compare(val2) >= 0;
}

} // namespace ignite::network
