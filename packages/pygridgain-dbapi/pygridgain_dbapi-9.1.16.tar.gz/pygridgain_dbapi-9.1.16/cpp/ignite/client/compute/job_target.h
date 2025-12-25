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
#include "ignite/client/table/qualified_name.h"
#include "ignite/client/detail/compute/job_target_type.h"

#include <set>
#include <vector>
#include <memory>

namespace ignite {
class ignite_tuple;
class compute;
class job_target;

/**
 * @brief Information about what nodes may be used for job execution.
 */
class job_target {
    friend class compute;
public:
    // Default
    virtual ~job_target() = default;

    /**
     * Create a single node job target.
     *
     * @param node Node.
     */
    [[nodiscard]] IGNITE_API static std::shared_ptr<job_target> node(cluster_node node);

    /**
     * Create a multiple node job target.
     *
     * @param nodes Nodes.
     */
    [[nodiscard]] IGNITE_API static std::shared_ptr<job_target> any_node(std::set<cluster_node> nodes);

    /**
     * Create a multiple node job target.
     *
     * @param nodes Nodes.
     */
    [[nodiscard]] IGNITE_API static std::shared_ptr<job_target> any_node(const std::vector<cluster_node> &nodes);

    /**
     * Creates a colocated job target for a specific table and key.
     *
     * @param table_name Table name.
     * @param key Key.
     */
    [[nodiscard]] IGNITE_API static std::shared_ptr<job_target> colocated(std::string_view table_name, const ignite_tuple &key);

    /**
     * Creates a colocated job target for a specific table and key.
     *
     * @param table_name Table name.
     * @param key Key.
     */
    [[nodiscard]] IGNITE_API static std::shared_ptr<job_target> colocated(qualified_name table_name, const ignite_tuple &key);

protected:
    // Default
    job_target() = default;

    /**
     * Get the job type.
     *
     * @return Job type.
     */
    [[nodiscard]] virtual detail::job_target_type get_type() const = 0;
};


} // namespace ignite
