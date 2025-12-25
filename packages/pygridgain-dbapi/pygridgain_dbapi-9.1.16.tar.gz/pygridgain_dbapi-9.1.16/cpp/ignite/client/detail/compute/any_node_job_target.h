/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/compute/job_target.h"
#include "ignite/client/detail/compute/job_target_type.h"

namespace ignite::detail {

/**
 * Job target represented by a set of nodes.
 */
class any_node_job_target : public job_target {
public:
    // Default
    any_node_job_target() = default;

    /**
     * Constructor.
     *
     * @param nodes Nodes.
     */
    explicit any_node_job_target(std::set<cluster_node> &&nodes)
        : m_nodes(std::move(nodes)) {}

    /**
     * Get nodes.
     *
     * @return Nodes.
     */
    [[nodiscard]] const std::set<cluster_node> &get_nodes() const { return m_nodes; }

    [[nodiscard]] job_target_type get_type() const override { return job_target_type::ANY_NODE; }

private:
    /** Nodes. */
    std::set<cluster_node> m_nodes;
};

} // namespace ignite::detail
