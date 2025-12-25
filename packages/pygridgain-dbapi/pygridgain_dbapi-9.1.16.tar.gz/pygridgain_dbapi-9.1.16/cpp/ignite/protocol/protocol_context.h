/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/protocol/protocol_version.h"
#include "ignite/protocol/bitset_span.h"
#include "ignite/protocol/bitmask_feature.h"

#include "ignite/common/detail/server_version.h"
#include "ignite/common/uuid.h"

#include <vector>

namespace ignite::protocol {

/**
 * Represents connection to the cluster.
 *
 * Considered established while there is connection to at least one server.
 */
class protocol_context {
public:
    /** Default TCP port. */
    static constexpr uint16_t DEFAULT_TCP_PORT = 10800;

    /**
     * Get protocol version.
     *
     * @return protocol version.
     */
    [[nodiscard]] protocol_version get_version() const { return m_version; }

    /**
     * Set version.
     *
     * @param ver Version to set.
     */
    void set_version(protocol_version ver) { m_version = ver; }

    /**
     * Get cluster IDs.
     *
     * @return Cluster IDs.
     */
    [[nodiscard]] const std::vector<uuid> &get_cluster_ids() const { return m_cluster_ids; }

    /**
     * Set Cluster IDs.
     *
     * @param ids Cluster IDs to set.
     */
    void set_cluster_ids(std::vector<uuid> &&ids) { m_cluster_ids = std::move(ids); }

    /**
     * Get server version.
     *
     * @return cluster version.
     */
    [[nodiscard]] detail::server_version get_server_version() const { return m_server_version; }

    /**
     * Set server version.
     *
     * @param ver Version to set.
     */
    void set_server_version(detail::server_version ver) { m_server_version = std::move(ver); }

    /**
     * Get cluster name.
     *
     * @return cluster name.
     */
    [[nodiscard]] std::string get_cluster_name() const { return m_cluster_name; }

    /**
     * Set cluster name.
     *
     * @param name Name to set.
     */
    void set_cluster_name(std::string name) { m_cluster_name = std::move(name); }

    /**
     * Get features.
     *
     * @return Features.
     */
    [[nodiscard]] bytes_view get_features() const { return m_features; }

    /**
     * Set features.
     *
     * @param features Features.
     */
    void set_features(std::vector<std::byte> features) { m_features = std::move(features); }

    /**
     * Check if the bitmask feature supported.
     *
     * @param feature Bitmask feature to test.
     * @return Features.
     */
    [[nodiscard]] bool is_feature_supported(bitmask_feature feature) const {
        return bitset_span(m_features).test(static_cast<std::size_t>(feature));
    }

private:
    /** Protocol version. */
    protocol_version m_version{protocol_version::get_current()};

    /** Cluster IDs. */
    std::vector<uuid> m_cluster_ids;

    /** Server version. */
    detail::server_version m_server_version{};

    /** Cluster name. */
    std::string m_cluster_name{};

    /** Features. */
    std::vector<std::byte> m_features{};
};

} // namespace ignite::protocol
