/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "tests/client-test/ignite_runner_suite.h"

#define TEST_TABLE_NAME "continuous_query_test"

using namespace ignite;

class continuous_query_test_ign_version : public ignite::ignite_runner_suite {
private:
    static ignite_client ConnectToCluster() {
        ignite_client_configuration cfg{get_node_addrs()};
        cfg.set_logger(get_logger());
        return ignite_client::start(cfg, std::chrono::seconds(30));
    }

protected:
    static void SetUpTestSuite() {
        auto client = ConnectToCluster();

        auto sql = client.get_sql();
        sql.execute(nullptr, nullptr, {"drop table if exists " TEST_TABLE_NAME}, {});

        sql.execute(nullptr, nullptr,
            {"create table " TEST_TABLE_NAME "(" + std::string{KEY_COLUMN} + " bigint primary key, "
                + std::string{VAL_COLUMN} + " varchar)"},
            {});
    }

    static void TearDownTestSuite() {
        auto client = ConnectToCluster();

        auto sql = client.get_sql();
        sql.execute(nullptr, nullptr, {"drop table if exists " TEST_TABLE_NAME}, {});
    }

    void SetUp() override {
        m_client = ConnectToCluster();
        m_binary_view = m_client.get_tables().get_table(TEST_TABLE_NAME)->get_record_binary_view();
        std::cout << "CompatibilityServer version" << ignite_runner::COMPATIBILITY_VERSION << "\n";
    }

    ignite_client m_client;
    record_view<ignite_tuple> m_binary_view;
};

TEST_F(continuous_query_test_ign_version, all_events_should_be_received) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_page_size(2);

    auto cq = m_binary_view.query_continuously(opts);

    int rec_count = 100;

    for (int64_t i = 0; i < rec_count; ++i) {
        m_binary_view.insert(nullptr, get_tuple(i, std::to_string(i)));
    }

    std::vector<ignite_tuple> events;
    events.reserve(rec_count);

    for (int64_t i = 0; i < rec_count;) {
        auto batch = cq.get_next();

        for (auto &event : batch.get_events()) {
            events.push_back(*event.get_entry());
            ++i;
        }
    }

    ASSERT_EQ(rec_count, events.size());

    std::sort(
        events.begin(),
        events.end(),
        [] (ignite_tuple& lhs, ignite_tuple& rhs) {
            return lhs.get(KEY_COLUMN).get<int64_t>() < rhs.get(KEY_COLUMN).get<int64_t>();
        });

    for (int64_t i = 0; i < rec_count; ++i) {
        ASSERT_EQ(i, events[i].get(KEY_COLUMN).get<int64_t>());
        ASSERT_EQ(std::to_string(i), events[i].get(VAL_COLUMN).get<std::string>());
    }
}