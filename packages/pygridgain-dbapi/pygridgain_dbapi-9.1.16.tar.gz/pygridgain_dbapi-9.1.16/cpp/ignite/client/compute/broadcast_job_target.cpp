/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/compute/broadcast_job_target.h"
#include "ignite/client/table/ignite_tuple.h"

#include "ignite/client/detail/argument_check_utils.h"
#include "ignite/client/detail/compute/nodes_broadcast_job_target.h"

namespace ignite {

std::shared_ptr<broadcast_job_target> broadcast_job_target::node(cluster_node val) {
    return std::shared_ptr<broadcast_job_target>{new detail::nodes_broadcast_job_target{{std::move(val)}}};
}

std::shared_ptr<broadcast_job_target> broadcast_job_target::nodes(std::set<cluster_node> vals) {
    detail::arg_check::container_non_empty(vals, "Nodes set");

    return std::shared_ptr<broadcast_job_target>{new detail::nodes_broadcast_job_target{std::move(vals)}};
}

std::shared_ptr<broadcast_job_target> broadcast_job_target::nodes(const std::vector<cluster_node> &vals) {
    detail::arg_check::container_non_empty(vals, "Nodes set");

    std::set<cluster_node> node_set(vals.begin(), vals.end());
    return nodes(node_set);
}

} // namespace ignite
