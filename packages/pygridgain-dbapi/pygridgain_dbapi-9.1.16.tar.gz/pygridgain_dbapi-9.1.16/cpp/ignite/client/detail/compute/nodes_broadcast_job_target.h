/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/compute/broadcast_job_target.h"

namespace ignite::detail {

/**
 * Job target represented by a set of nodes.
 */
class nodes_broadcast_job_target : public broadcast_job_target {
public:
    // Default
    nodes_broadcast_job_target() = default;

    /**
     * Constructor.
     *
     * @param nodes Nodes.
     */
    explicit nodes_broadcast_job_target(std::set<cluster_node> &&nodes)
        : m_nodes(std::move(nodes)) {}

    /**
     * Get nodes.
     *
     * @return Nodes.
     */
    [[nodiscard]] const std::set<cluster_node> &get_nodes() const { return m_nodes; }

private:
    /** Nodes. */
    std::set<cluster_node> m_nodes;
};

} // namespace ignite::detail
