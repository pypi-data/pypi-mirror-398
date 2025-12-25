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

namespace ignite {

/**
 * @brief Connection end point structure.
 */
struct end_point {
    // Default
    end_point() = default;

    /**
     * Constructor.
     *
     * @param host Host.
     * @param port Port.
     */
    end_point(std::string host, uint16_t port)
        : host(std::move(host))
        , port(port) {}

    /**
     * Convert to string.
     *
     * @return String form.
     */
    [[nodiscard]] std::string to_string() const { return host + ":" + std::to_string(port); }

    /**
     * compare to another instance.
     *
     * @param other Another instance.
     * @return Negative value if less, positive if larger and zero, if equals
     *   another instance.
     */
    [[nodiscard]] int compare(const end_point &other) const {
        if (port < other.port)
            return -1;

        if (port > other.port)
            return 1;

        return host.compare(other.host);
    }

    /** Remote host. */
    std::string host;

    /** TCP port. */
    uint16_t port{0};
};

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if equal.
 */
inline bool operator==(const end_point &val1, const end_point &val2) {
    return val1.port == val2.port && val1.host == val2.host;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if not equal.
 */
inline bool operator!=(const end_point &val1, const end_point &val2) {
    return !(val1 == val2);
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if less.
 */
inline bool operator<(const end_point &val1, const end_point &val2) {
    return val1.compare(val2) < 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if less or equal.
 */
inline bool operator<=(const end_point &val1, const end_point &val2) {
    return val1.compare(val2) <= 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if greater.
 */
inline bool operator>(const end_point &val1, const end_point &val2) {
    return val1.compare(val2) > 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if greater or equal.
 */
inline bool operator>=(const end_point &val1, const end_point &val2) {
    return val1.compare(val2) >= 0;
}

} // namespace ignite
