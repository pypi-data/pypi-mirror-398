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
#include <set>
#include <string>

namespace ignite::protocol {

/** Protocol version. */
class protocol_version {
public:
    /** Version 3.0.0. */
    static const protocol_version VERSION_3_0_0;

    /** Version set. */
    typedef std::set<protocol_version> version_set;

    /**
     * Get string to version map.
     *
     * @return String to a version map.
     */
    static const version_set &get_supported() {
        static protocol_version::version_set supported{protocol_version::VERSION_3_0_0};
        return supported;
    }

    /**
     * Get current version.
     *
     * @return Current version.
     */
    static const protocol_version &get_current() { return VERSION_3_0_0; }

    /**
     * Parse string and extract a protocol version.
     *
     * @throw ignite_error if the version cannot be parsed.
     * @param version Version string to parse.
     * @return Protocol version.
     */
    static std::optional<protocol_version> from_string(const std::string &version);

    /**
     * Convert to string value.
     *
     * @return Protocol version.
     */
    [[nodiscard]] std::string to_string() const;

    /**
     * Default constructor.
     */
    protocol_version() = default;

    /**
     * Constructor.
     *
     * @param vmajor Major version part.
     * @param vminor Minor version part.
     * @param vpatch Patch version part.
     */
    protocol_version(std::int16_t vmajor, std::int16_t vminor, std::int16_t vpatch)
        : m_major(vmajor)
        , m_minor(vminor)
        , m_patch(vpatch) {}

    /**
     * Get major part.
     *
     * @return Major part.
     */
    [[nodiscard]] std::int16_t get_major() const { return m_major; }

    /**
     * Get minor part.
     *
     * @return Minor part.
     */
    [[nodiscard]] std::int16_t get_minor() const { return m_minor; }

    /**
     * Get patch part.
     *
     * @return Patch part.
     */
    [[nodiscard]] std::int16_t get_patch() const { return m_patch; }

    /**
     * Check if the version is supported.
     *
     * @return True if the version is supported.
     */
    [[nodiscard]] bool is_supported() const { return get_supported().count(*this) != 0; }

    /**
     * compare to another value.
     *
     * @param other Instance to compare to.
     * @return Zero if equals, negative number if less and positive if more.
     */
    [[nodiscard]] std::int32_t compare(const protocol_version &other) const;

private:
    /** Major part. */
    std::int16_t m_major{0};

    /** Minor part. */
    std::int16_t m_minor{0};

    /** Patch part. */
    std::int16_t m_patch{0};
};

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if equal.
 */
inline bool operator==(const protocol_version &val1, const protocol_version &val2) {
    return val1.compare(val2) == 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if not equal.
 */
inline bool operator!=(const protocol_version &val1, const protocol_version &val2) {
    return val1.compare(val2) != 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if less.
 */
inline bool operator<(const protocol_version &val1, const protocol_version &val2) {
    return val1.compare(val2) < 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if less or equal.
 */
inline bool operator<=(const protocol_version &val1, const protocol_version &val2) {
    return val1.compare(val2) <= 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if greater.
 */
inline bool operator>(const protocol_version &val1, const protocol_version &val2) {
    return val1.compare(val2) > 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if greater or equal.
 */
inline bool operator>=(const protocol_version &val1, const protocol_version &val2) {
    return val1.compare(val2) >= 0;
}

} // namespace ignite::protocol
