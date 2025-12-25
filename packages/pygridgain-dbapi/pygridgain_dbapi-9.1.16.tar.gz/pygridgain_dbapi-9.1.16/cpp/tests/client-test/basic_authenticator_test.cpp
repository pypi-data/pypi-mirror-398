/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "tests/test-common/basic_auth_test_suite.h"

#include <gmock/gmock-matchers.h>
#include <gtest/gtest.h>

using namespace ignite;

struct basic_authenticator_test : public basic_auth_test_suite {
    /**
     * Tear down.
     */
    static void TearDownTestSuite() { set_authentication_enabled(false); }
};

TEST_F(basic_authenticator_test, disabled_on_server) {
    set_authentication_enabled(false);
    auto client = ignite_client::start(get_configuration_correct(), std::chrono::seconds(30));
    (void) client.get_cluster_nodes();
}

TEST_F(basic_authenticator_test, disabled_on_client) {
    set_authentication_enabled(true);
    EXPECT_THROW(
        {
            try {
                (void) ignite_client::start(get_configuration(), std::chrono::seconds(30));
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("Authentication failed"));
                throw;
            }
        },
        ignite_error);
}

TEST_F(basic_authenticator_test, success) {
    set_authentication_enabled(true);
    auto client = ignite_client::start(get_configuration_correct(), std::chrono::seconds(30));
    (void) client.get_cluster_nodes();
}

TEST_F(basic_authenticator_test, wrong_username) {
    set_authentication_enabled(true);
    EXPECT_THROW(
        {
            try {
                (void) ignite_client::start(get_configuration("Lorem Ipsum", "bla"), std::chrono::seconds(30));
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("Authentication failed"));
                throw;
            }
        },
        ignite_error);
}

TEST_F(basic_authenticator_test, wrong_password) {
    set_authentication_enabled(true);
    EXPECT_THROW(
        {
            try {
                (void) ignite_client::start(get_configuration(CORRECT_USERNAME, "wrong"), std::chrono::seconds(30));
            } catch (const ignite_error &e) {
                EXPECT_THAT(e.what_str(), testing::HasSubstr("Authentication failed"));
                throw;
            }
        },
        ignite_error);
}
