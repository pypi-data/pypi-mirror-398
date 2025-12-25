/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite_runner_suite.h"

#include <ignite/client/basic_authenticator.h>
#include <ignite/client/ignite_client.h>
#include <ignite/client/ignite_client_configuration.h>

#include <gtest/gtest.h>
#include <gmock/gmock-matchers.h>

#include <chrono>
#include <thread>

using namespace ignite;

/**
 * Test suite.
 */
class client_test : public ignite_runner_suite {
public:
    /**
     * Create default config.
     * @return Default config.
     */
    static ignite_client_configuration create_default_client_config() {
        ignite_client_configuration cfg{get_node_addrs()};
        cfg.set_logger(get_logger());
        return cfg;
    }
};

TEST_F(client_test, configuration_set_invalid_heartbeat) {
    using namespace std::chrono_literals;

    auto cfg = create_default_client_config();

    EXPECT_THROW(
        {
            try {
                cfg.set_heartbeat_interval(-1s);
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("Heartbeat interval can not be negative"));
                throw;
            }
        },
        ignite_error);
}

TEST_F(client_test, configuration_set_invalid_operation_timeout) {
    using namespace std::chrono_literals;

    auto cfg = create_default_client_config();

    EXPECT_THROW(
        {
            try {
                cfg.set_operation_timeout(-1s);
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("Operation timeout can't be negative"));
                throw;
            }
        },
        ignite_error);
}

TEST_F(client_test, configuration_set_empty_address_constructor) {
    EXPECT_THROW(
        {
            try {
                ignite_client_configuration _cfg({});
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("Connection endpoint list can not be empty"));
                throw;
            }
        },
        ignite_error);
}

TEST_F(client_test, configuration_set_empty_address_setter_1) {
    auto cfg = create_default_client_config();

    EXPECT_THROW(
        {
            try {
                cfg.set_endpoints({});
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("Connection endpoint list can not be empty"));
                throw;
            }
        },
        ignite_error);
}

TEST_F(client_test, configuration_set_empty_address_setter_2) {
    auto cfg = create_default_client_config();

    EXPECT_THROW(
        {
            try {
                cfg.set_endpoints(std::vector<std::string>{});
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("Connection endpoint list can not be empty"));
                throw;
            }
        },
        ignite_error);
}

TEST_F(client_test, get_configuration) {
    using namespace std::chrono_literals;

    auto cfg = create_default_client_config();
    cfg.set_connection_limit(42);
    cfg.set_heartbeat_interval(18s);

    auto client = ignite_client::start(cfg, 30s);

    const auto &cfg2 = client.configuration();

    EXPECT_EQ(cfg.get_endpoints(), cfg2.get_endpoints());
    EXPECT_EQ(cfg.get_connection_limit(), cfg2.get_connection_limit());
    EXPECT_EQ(cfg.get_heartbeat_interval(), cfg2.get_heartbeat_interval());
}


TEST_F(client_test, heartbeat_enable_reasonable_connection_is_not_closed) {
    using namespace std::chrono_literals;

    auto cfg = create_default_client_config();
    cfg.set_heartbeat_interval(2s);

    auto client = ignite_client::start(cfg, 30s);
    auto tx = client.get_transactions().begin();

    std::this_thread::sleep_for(7s);
    tx.rollback();
}


TEST_F(client_test, heartbeat_enable_too_big_connection_is_not_closed) {
    using namespace std::chrono_literals;

    auto cfg = create_default_client_config();
    cfg.set_heartbeat_interval(20s);

    auto client = ignite_client::start(cfg, 30s);
    auto tx = client.get_transactions().begin();

    std::this_thread::sleep_for(7s);
    tx.rollback();
}


TEST_F(client_test, heartbeat_disable_connection_is_closed) {
    using namespace std::chrono_literals;

    auto cfg = create_default_client_config();
    cfg.set_heartbeat_interval(0s);

    auto client = ignite_client::start(cfg, 30s);
    auto tx = client.get_transactions().begin();

    std::this_thread::sleep_for(7s);

    EXPECT_THROW(
        {
            try {
                tx.rollback();
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("connection is closed"));
                throw;
            }
        },
        ignite_error);
}
