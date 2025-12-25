/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/compute/job_target.h"
#include "ignite/client/table/ignite_tuple.h"

#include "ignite/client/detail/argument_check_utils.h"
#include "ignite/client/detail/compute/any_node_job_target.h"
#include "ignite/client/detail/compute/colocated_job_target.h"

namespace ignite {

std::shared_ptr<job_target> job_target::node(cluster_node node) {
    return std::shared_ptr<job_target>{new detail::any_node_job_target{{std::move(node)}}};
}

std::shared_ptr<job_target> job_target::any_node(std::set<cluster_node> nodes) {
    detail::arg_check::container_non_empty(nodes, "Nodes set");

    return std::shared_ptr<job_target>{new detail::any_node_job_target{std::move(nodes)}};
}

std::shared_ptr<job_target> job_target::any_node(const std::vector<cluster_node> &nodes) {
    detail::arg_check::container_non_empty(nodes, "Nodes set");

    std::set<cluster_node> node_set(nodes.begin(), nodes.end());
    return any_node(node_set);
}

std::shared_ptr<job_target> job_target::colocated(std::string_view table_name, const ignite_tuple &key) {
    detail::arg_check::container_non_empty(table_name, "Table name");
    detail::arg_check::tuple_non_empty(key, "Key tuple");

    return std::shared_ptr<job_target>{new detail::colocated_job_target{qualified_name::parse(table_name), key}};
}

std::shared_ptr<job_target> job_target::colocated(qualified_name table_name, const ignite_tuple &key) {
    detail::arg_check::container_non_empty(table_name.get_schema_name(), "Table name");
    detail::arg_check::tuple_non_empty(key, "Key tuple");

    return std::shared_ptr<job_target>{new detail::colocated_job_target{table_name, key}};
}

} // namespace ignite
