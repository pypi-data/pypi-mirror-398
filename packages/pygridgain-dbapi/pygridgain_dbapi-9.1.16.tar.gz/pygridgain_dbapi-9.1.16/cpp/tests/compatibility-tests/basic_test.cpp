/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "tests/client-test/ignite_runner_suite.h"

using namespace ignite;

class basic_test_ign_version : public ignite::ignite_runner_suite {
private:
    static ignite_client ConnectToCluster() {
        ignite_client_configuration cfg{get_node_addrs()};
        cfg.set_logger(get_logger());
        return ignite_client::start(cfg, std::chrono::seconds(30));
    }

protected:
    void SetUp() override {
        m_client = ConnectToCluster();

        std::cout << "CompatibilityServer version" << ignite_runner::COMPATIBILITY_VERSION << "\n";
    }

    ignite_client m_client;
};


TEST_F(basic_test_ign_version, get_cluster_nodes_successful) {
    auto cluster_nodes = m_client.get_cluster_nodes();

    ASSERT_GE(cluster_nodes.size(), 1);
}