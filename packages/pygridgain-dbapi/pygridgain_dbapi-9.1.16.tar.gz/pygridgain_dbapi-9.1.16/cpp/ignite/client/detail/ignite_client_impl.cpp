/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/detail/ignite_client_impl.h"
#include "ignite/client/detail/utils.h"

namespace ignite::detail {


void ignite_client_impl::get_cluster_nodes_async(ignite_callback<std::vector<cluster_node>> callback) {
    auto reader_func = [](protocol::reader &reader) -> std::vector<cluster_node> {
        std::vector<cluster_node> nodes;
        auto size = reader.read_int32();
        nodes.reserve(std::size_t(size));

        for (std::int32_t node_idx = 0; node_idx < size; ++node_idx) {
            nodes.emplace_back(read_cluster_node(reader));
        }

        return nodes;
    };

    m_connection->perform_request_rd<std::vector<cluster_node>>(
        protocol::client_operation::CLUSTER_GET_NODES, std::move(reader_func), std::move(callback));
}

} // namespace ignite::detail
