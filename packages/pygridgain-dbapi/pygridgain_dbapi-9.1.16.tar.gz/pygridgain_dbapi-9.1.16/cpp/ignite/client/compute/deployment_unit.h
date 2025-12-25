/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <string>

namespace ignite {

/**
 * @brief Deployment unit identifier.
 */
class deployment_unit {

public:
    static const inline std::string LATEST_VERSION{"latest"};

    // Delete
    deployment_unit() = delete;

    /**
     * Constructor.
     *
     * @param name Unit name.
     * @param version Unit version. Defaults to @c LATEST_VERSION.
     */
    deployment_unit(std::string name, std::string version = LATEST_VERSION) // NOLINT(google-explicit-constructor)
        : m_name(std::move(name))
        , m_version(std::move(version)) {}

    /**
     * Get name.
     *
     * @return Unit name.
     */
    [[nodiscard]] const std::string &get_name() const { return m_name; }

    /**
     * Set name.
     *
     * @param name Unit name to set.
     */
    void set_name(const std::string &name) { m_name = name; }

    /**
     * Get version.
     *
     * @return Unit version.
     */
    [[nodiscard]] const std::string &get_version() const { return m_version; }

    /**
     * Set version.
     *
     * @param version Unit version to set.
     */
    void set_version(const std::string &version) { m_version = version; }

private:
    /** Name. */
    std::string m_name;

    /** Version. */
    std::string m_version;
};

} // namespace ignite
