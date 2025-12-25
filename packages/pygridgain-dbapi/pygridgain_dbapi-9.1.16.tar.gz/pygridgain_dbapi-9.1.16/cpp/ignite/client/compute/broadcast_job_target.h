/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/detail/config.h"
#include "ignite/client/network/cluster_node.h"

#include <set>
#include <vector>
#include <memory>

namespace ignite {

/**
 * @brief Compute task target.
 *
 * Encapsulates which nodes will be used as targets for compute task.
 */
class broadcast_job_target {
public:
    // Default
    virtual ~broadcast_job_target() = default;

    /**
     * Create a single node job target.
     *
     * @param val Node.
     */
    [[nodiscard]] IGNITE_API static std::shared_ptr<broadcast_job_target> node(cluster_node val);

    /**
     * Create a multiple node job target.
     *
     * @param vals Nodes.
     */
    [[nodiscard]] IGNITE_API static std::shared_ptr<broadcast_job_target> nodes(std::set<cluster_node> vals);

    /**
     * Create a multiple node job target.
     *
     * @param vals Nodes.
     */
    [[nodiscard]] IGNITE_API static std::shared_ptr<broadcast_job_target> nodes(const std::vector<cluster_node> &vals);

protected:
    // Default
    broadcast_job_target() = default;
};


} // namespace ignite
