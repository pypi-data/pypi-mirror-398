/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "tests/client-test/ignite_runner_suite.h"

#include <ignite/client/basic_authenticator.h>
#include <ignite/client/ignite_client.h>
#include <ignite/client/ignite_client_configuration.h>

#include <chrono>
#include <thread>

/**
 * Test suite.
 */
class basic_auth_test_suite : public ignite::ignite_runner_suite {
public:
    /** Correct username */
    inline static const std::string CORRECT_USERNAME{"user-1"};

    /** Correct password */
    inline static const std::string CORRECT_PASSWORD{"password-1"};

    /** Correct username */
    inline static const std::string INCORRECT_USERNAME{"root"};

    /** Correct password */
    inline static const std::string INCORRECT_PASSWORD{"123"};

    /**
     * Get default configuration.
     *
     * @return Configuration.
     */
    static ignite::ignite_client_configuration get_configuration() {
        ignite::ignite_client_configuration cfg{get_node_addrs()};
        cfg.set_logger(get_logger());

        return cfg;
    }

    /**
     * Get configuration with basic auth enabled.
     *
     * @param user Username to use.
     * @param password Password to use.
     * @return Configuration.
     */
    static ignite::ignite_client_configuration get_configuration(std::string user, std::string password) {
        ignite::ignite_client_configuration cfg{get_configuration()};

        auto authenticator = std::make_shared<ignite::basic_authenticator>(std::move(user), std::move(password));
        cfg.set_authenticator(authenticator);

        return cfg;
    }

    /**
     * Get configuration with correct credentials.
     *
     * @return Configuration with correct credentials.
     */
    static ignite::ignite_client_configuration get_configuration_correct() {
        return get_configuration(CORRECT_USERNAME, CORRECT_PASSWORD);
    }

    /**
     * Change cluster authentication state.
     *
     * @param enable Authentication enabled.
     */
    static void set_authentication_enabled(bool enable) {
        using namespace ignite;

        if (m_auth_enabled == enable)
            return;

        try {
            ignite_client_configuration cfg = m_auth_enabled ? get_configuration_correct() : get_configuration();

            auto client = ignite_client::start(cfg, std::chrono::seconds(30));

            auto nodes = client.get_cluster_nodes();
            auto descriptor = job_descriptor::builder(ENABLE_AUTHN_JOB).build();

            client.get_compute().submit(job_target::any_node(nodes), descriptor, {enable ? 1 : 0}).get_result();
        } catch (const ignite_error &) {
            // Ignore.
            // As a result of this call, the client may be disconnected from the server due to authn config change.
        }

        // Wait for the server to apply the configuration change and drop the client connection.
        std::this_thread::sleep_for(std::chrono::seconds(10));

        m_auth_enabled = enable;
    }

private:
    /** Authentication enabled. */
    inline static bool m_auth_enabled{false};
};
