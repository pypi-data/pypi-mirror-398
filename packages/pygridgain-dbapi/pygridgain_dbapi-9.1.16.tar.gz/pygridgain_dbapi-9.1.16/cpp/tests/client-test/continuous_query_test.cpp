/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/ignite_client.h"
#include "ignite_runner_suite.h"

#include <gmock/gmock-matchers.h>
#include <gtest/gtest.h>

#include <chrono>
#include <limits>
#include <string>
#include <vector>

using namespace ignite;
using namespace std::chrono_literals;

#define TEST_TABLE_NAME "continuous_query_test"
#define KEY_COLUMN "ID"
#define VAL_COLUMN "VAL1"

typedef std::pair<ignite_tuple, ignite_tuple> ignite_tuple_pair;

template<typename T>
class events_store {
public:
    typedef T value_type;

    explicit events_store(continuous_query<value_type> &cq)
        : m_cq(cq) {}

    template<class T1, class T2>
    std::cv_status query_events(std::size_t n, std::chrono::duration<T1, T2> timeout) {
        auto now = std::chrono::steady_clock::now();

        while (m_events.size() < n) {
            std::promise<std::vector<table_row_event<value_type>>> events_promise;
            m_cq.get_next_async([&](auto res) {
                if (res.has_error()) {
                    try {
                        throw std::move(res).error();
                    } catch (...) {
                        events_promise.set_exception(std::current_exception());
                    }
                } else {
                    events_promise.set_value(std::move(res).value().get_events());
                }
            });

            auto fut = events_promise.get_future();
            auto res = fut.wait_until(now + timeout);
            if (res == std::future_status::timeout)
                return std::cv_status::timeout;

            auto err = result_of_operation<void>([&]() {
                auto events = fut.get();
                for (const auto &event : events) {
                    m_watermarks.push_back(event.get_watermark());
                }
                m_events.insert(
                    m_events.end(), std::make_move_iterator(events.begin()), std::make_move_iterator(events.end()));
            });

            if (err.has_error()) {
                m_error = err.error();
                return std::cv_status::no_timeout;
            }
        }

        return std::cv_status::no_timeout;
    }

    [[nodiscard]] std::optional<ignite_error> get_error() const { return m_error; }

    [[nodiscard]] table_row_event<value_type> get_event(std::size_t idx) const { return m_events.at(idx); }

    [[nodiscard]] continuous_query_watermark get_watermark(std::size_t idx) const { return m_watermarks.at(idx); }

    [[nodiscard]] std::size_t get_events_num() const { return m_events.size(); }

private:
    continuous_query<value_type> m_cq;
    std::vector<table_row_event<value_type>> m_events;
    std::vector<continuous_query_watermark> m_watermarks;
    std::optional<ignite_error> m_error{std::nullopt};
};

template<class T>
events_store<T> make_store(continuous_query<T> &cq) {
    return events_store<T>{cq};
}

/**
 * Test table type mapping.
 */
struct cq_test_type {
    cq_test_type() = default;

    explicit cq_test_type(std::int32_t key)
        : key(key) {}

    explicit cq_test_type(std::string val)
        : val(std::move(val)) {}

    explicit cq_test_type(std::int32_t key, std::string val)
        : key(key)
        , val(std::move(val)) {}

    std::int32_t key{0};
    std::string val;
};

namespace ignite {

template<>
ignite_tuple convert_to_tuple(cq_test_type &&value) {
    ignite_tuple tuple;

    tuple.set("id", value.key);
    tuple.set("val1", value.val);

    return tuple;
}

template<>
cq_test_type convert_from_tuple(ignite_tuple &&value) {
    cq_test_type res;

    res.key = value.get<std::int32_t>("id");

    if (value.column_count() > 1)
        res.val = value.get<std::string>("val1");

    return res;
}

} // namespace ignite

/**
 * Test key type mapping.
 */
struct cq_test_key_type {
    cq_test_key_type() = default;

    explicit cq_test_key_type(std::int32_t key)
        : key(key) {}

    std::int32_t key{0};
};

/**
 * Test value type mapping.
 */
struct cq_test_value_type {
    cq_test_value_type() = default;

    explicit cq_test_value_type(std::string val)
        : val(std::move(val)) {}

    std::string val;
};

typedef std::pair<cq_test_key_type, cq_test_value_type> cq_test_pair;

namespace ignite {

template<>
ignite_tuple convert_to_tuple(cq_test_key_type &&value) {
    ignite_tuple tuple;

    tuple.set("id", value.key);

    return tuple;
}

template<>
cq_test_key_type convert_from_tuple(ignite_tuple &&value) {
    cq_test_key_type res;

    res.key = value.get<std::int32_t>("id");

    return res;
}

template<>
ignite_tuple convert_to_tuple(cq_test_value_type &&value) {
    ignite_tuple tuple;

    tuple.set("val1", value.val);

    return tuple;
}

template<>
cq_test_value_type convert_from_tuple(ignite_tuple &&value) {
    cq_test_value_type res;

    res.val = value.get<std::string>("val1");

    return res;
}

} // namespace ignite

struct continuous_query_test : public ignite_runner_suite {
protected:
    void SetUp() override {
        ignite_client_configuration cfg{get_node_addrs()};
        m_logger = get_logger();
        cfg.set_logger(m_logger);

        m_client = ignite_client::start(cfg, std::chrono::seconds(30));
        m_client.get_sql().execute(nullptr, nullptr, {"drop table if exists " TEST_TABLE_NAME}, {});
        m_client.get_sql().execute(nullptr, nullptr,
            {"create table " TEST_TABLE_NAME "(" KEY_COLUMN " int primary key, " VAL_COLUMN
             R"( varchar) zone "zone1")"},
            {});
        m_simple_table_binary_view = m_client.get_tables().get_table(TEST_TABLE_NAME)->get_record_binary_view();

        m_table_with_sec_storage_bin_view = m_client.get_tables().get_table("TBL1")->get_record_binary_view();
    }

    static void SetUpTestSuite() {
        ignite_client_configuration cfg{get_node_addrs()};
        cfg.set_logger(get_logger());
        auto client = ignite_client::start(cfg, std::chrono::seconds(30));

        auto sql = client.get_sql();
        sql.execute(nullptr, nullptr, {"drop table if exists " TEST_TABLE_NAME}, {});
        client.get_sql().execute(nullptr, nullptr, {"drop table if exists schema_update_while_query_is_active"}, {});
        client.get_sql().execute(nullptr, nullptr, {"drop table if exists drop_table_invokes_error"}, {});
        client.get_sql().execute(nullptr, nullptr, {"delete from TBL1"}, {});

        sql.execute(nullptr, nullptr,
            {"create table " TEST_TABLE_NAME "(" KEY_COLUMN " int primary key, " VAL_COLUMN
             R"( varchar) zone "zone1")"},
            {});
    }

    static void TearDownTestSuite() {
        ignite_client_configuration cfg{get_node_addrs()};
        cfg.set_logger(get_logger());
        auto client = ignite_client::start(cfg, std::chrono::seconds(30));

        client.get_sql().execute(nullptr, nullptr, {"drop table if exists " TEST_TABLE_NAME}, {});
        client.get_sql().execute(nullptr, nullptr, {"drop table if exists schema_update_while_query_is_active"}, {});
        client.get_sql().execute(nullptr, nullptr, {"drop table if exists drop_table_invokes_error"}, {});
        client.get_sql().execute(nullptr, nullptr, {"delete from TBL1"}, {});
    }

    /**
     * Get tuple for specified column values.
     *
     * @param id ID.
     * @param val Value.
     * @return Ignite tuple instance.
     */
    static ignite_tuple get_tuple(int32_t id, std::string val) {
        return {{KEY_COLUMN, id}, {VAL_COLUMN, std::move(val)}};
    }

    /**
     * Get tuple for specified column values.
     *
     * @param id ID.
     * @return Ignite tuple instance.
     */
    static ignite_tuple get_tuple(int32_t id, std::nullptr_t) { return {{KEY_COLUMN, id}, {VAL_COLUMN, std::nullopt}}; }

    /**
     * Get tuple for specified column values.
     *
     * @param val Value.
     * @return Ignite tuple instance.
     */
    static ignite_tuple get_tuple(std::nullptr_t, std::string val) {
        return {{KEY_COLUMN, std::nullopt}, {VAL_COLUMN, std::move(val)}};
    }

    /**
     * Get tuple for specified column values.
     *
     * @param id ID.
     * @return Ignite tuple instance.
     */
    static ignite_tuple get_tuple(int32_t id) { return {{KEY_COLUMN, id}}; }

    /**
     * Get tuple for specified column values.
     *
     * @param val Value.
     * @return Ignite tuple instance.
     */
    static ignite_tuple get_tuple(std::string val) { return {{VAL_COLUMN, std::move(val)}}; }

    /**
     * Get tuple for specified column values.
     *
     * @param id ID.
     * @param val Value.
     * @return Ignite tuple instance.
     */
    static ignite_tuple_pair get_tuple_pair(int32_t id, std::string val) {
        return std::make_pair<ignite_tuple, ignite_tuple>({{KEY_COLUMN, id}}, {{VAL_COLUMN, std::move(val)}});
    }

    /**
     * Get tuple for specified column values.
     *
     * @param id ID.
     * @param val Value.
     * @return Ignite tuple instance.
     */
    static cq_test_pair get_object_pair(int32_t id, std::string val) {
        return std::make_pair<cq_test_key_type, cq_test_value_type>(
            cq_test_key_type{id}, cq_test_value_type{std::move(val)});
    }

    /** Ignite logger. */
    std::shared_ptr<gtest_logger> m_logger;

    /** Ignite client. */
    ignite_client m_client;

    /** Binary Record view. */
    record_view<ignite_tuple> m_simple_table_binary_view;

    record_view<ignite_tuple> m_table_with_sec_storage_bin_view;
};

void check_tuples_equal(
    unsigned line, const std::optional<ignite_tuple> &actual, const std::optional<ignite_tuple> &expected) {
    std::string context = "Check line: " + std::to_string(line);
    ASSERT_EQ(expected.has_value(), actual.has_value()) << context;
    if (actual) {
        ASSERT_EQ(expected->column_count(), actual->column_count()) << context;
        if (expected->column_ordinal(KEY_COLUMN) >= 0) {
            EXPECT_EQ(expected->get(KEY_COLUMN), actual->get(KEY_COLUMN)) << context;
        }
        if (expected->column_ordinal(VAL_COLUMN) >= 0) {
            EXPECT_EQ(expected->get(VAL_COLUMN), actual->get(VAL_COLUMN)) << context;
        }
    }
}

void check_event(unsigned line, const table_row_event<ignite_tuple> &event, table_row_event_type typ,
    const std::optional<ignite_tuple> &old_val, const std::optional<ignite_tuple> &val) {
    std::string context = "Check line: " + std::to_string(line);
    EXPECT_EQ(typ, event.get_type()) << context;

    check_tuples_equal(line, event.get_old_entry(), old_val);
    check_tuples_equal(line, event.get_entry(), val);
}

void check_tuples_equal(
    unsigned line, const std::optional<cq_test_type> &actual, const std::optional<cq_test_type> &expected) {
    std::string context = "Check line: " + std::to_string(line);
    ASSERT_EQ(expected.has_value(), actual.has_value()) << context;
    if (actual) {
        EXPECT_EQ(expected->key, actual->key) << context;
        EXPECT_EQ(expected->val, actual->val) << context;
    }
}

void check_event(unsigned line, const table_row_event<cq_test_type> &event, table_row_event_type typ,
    const std::optional<cq_test_type> &old_val, const std::optional<cq_test_type> &val) {
    std::string context = "Check line: " + std::to_string(line);
    EXPECT_EQ(typ, event.get_type()) << context;

    check_tuples_equal(line, event.get_old_entry(), old_val);
    check_tuples_equal(line, event.get_entry(), val);
}

void check_tuples_equal(
    unsigned line, const std::optional<ignite_tuple_pair> &actual, const std::optional<ignite_tuple_pair> &expected) {
    std::string context = "Check line: " + std::to_string(line);
    ASSERT_EQ(expected.has_value(), actual.has_value()) << context;
    if (actual) {
        ASSERT_EQ(expected->first.column_count(), actual->first.column_count()) << context;
        ASSERT_EQ(expected->second.column_count(), actual->second.column_count()) << context;

        EXPECT_EQ(expected->first.get(KEY_COLUMN), actual->first.get(KEY_COLUMN)) << context;
        EXPECT_EQ(expected->second.get(VAL_COLUMN), actual->second.get(VAL_COLUMN)) << context;
    }
}

void check_event(unsigned line, const table_row_event<ignite_tuple_pair> &event, table_row_event_type typ,
    const std::optional<ignite_tuple_pair> &old_val, const std::optional<ignite_tuple_pair> &val) {
    std::string context = "Check line: " + std::to_string(line);
    EXPECT_EQ(typ, event.get_type()) << context;

    check_tuples_equal(line, event.get_old_entry(), old_val);
    check_tuples_equal(line, event.get_entry(), val);
}

void check_tuples_equal(
    unsigned line, const std::optional<cq_test_pair> &actual, const std::optional<cq_test_pair> &expected) {
    std::string context = "Check line: " + std::to_string(line);
    ASSERT_EQ(expected.has_value(), actual.has_value()) << context;
    if (actual) {
        ASSERT_EQ(expected->first.key, actual->first.key) << context;
        ASSERT_EQ(expected->second.val, actual->second.val) << context;
    }
}

void check_event(unsigned line, const table_row_event<cq_test_pair> &event, table_row_event_type typ,
    const std::optional<cq_test_pair> &old_val, const std::optional<cq_test_pair> &val) {
    std::string context = "Check line: " + std::to_string(line);
    EXPECT_EQ(typ, event.get_type()) << context;

    check_tuples_equal(line, event.get_old_entry(), old_val);
    check_tuples_equal(line, event.get_entry(), val);
}

#define EXPECT_EVENT(...) check_event(__LINE__, __VA_ARGS__)

#define EXPECT_NO_ERROR(store)                                                                                         \
 do {                                                                                                                  \
  auto err = store.get_error();                                                                                        \
  if (err.has_value())                                                                                                 \
   FAIL() << err->what_str();                                                                                          \
 } while (false)

TEST_F(continuous_query_test, record_binary_view_all_event_types) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);

    m_logger->set_debug_enabled(false);
    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(3, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(3, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, "Test1")});
    EXPECT_EVENT(store.get_event(1), table_row_event_type::UPDATED, {get_tuple(1, "Test1")}, {get_tuple(1, "Test2")});
    EXPECT_EVENT(store.get_event(2), table_row_event_type::REMOVED, {get_tuple(1, "Test2")}, std::nullopt);
}

TEST_F(continuous_query_test, record_view_all_event_types) {
    auto record_view = m_client.get_tables().get_table(TEST_TABLE_NAME)->get_record_view<cq_test_type>();

    continuous_query_options opts;
    opts.set_poll_interval_ms(100);

    auto cq = record_view.query_continuously(opts);
    auto store = make_store(cq);

    record_view.upsert(nullptr, cq_test_type(1, "Test1"));
    record_view.upsert(nullptr, cq_test_type(1, "Test2"));
    record_view.remove(nullptr, cq_test_type(1));

    auto wait_res = store.query_events(3, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(3, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {cq_test_type(1, "Test1")});
    EXPECT_EVENT(
        store.get_event(1), table_row_event_type::UPDATED, {cq_test_type(1, "Test1")}, {cq_test_type(1, "Test2")});
    EXPECT_EVENT(store.get_event(2), table_row_event_type::REMOVED, {cq_test_type(1, "Test2")}, std::nullopt);
}

TEST_F(continuous_query_test, key_value_binary_view_all_event_types) {
    auto kv_view = m_client.get_tables().get_table(TEST_TABLE_NAME)->get_key_value_binary_view();

    continuous_query_options opts;
    opts.set_poll_interval_ms(100);

    auto cq = kv_view.query_continuously(opts);
    auto store = make_store(cq);

    kv_view.put(nullptr, get_tuple(1), get_tuple("Test1"));
    kv_view.put(nullptr, get_tuple(1), get_tuple("Test2"));
    kv_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(3, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(3, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple_pair(1, "Test1")});
    EXPECT_EVENT(
        store.get_event(1), table_row_event_type::UPDATED, {get_tuple_pair(1, "Test1")}, {get_tuple_pair(1, "Test2")});
    EXPECT_EVENT(store.get_event(2), table_row_event_type::REMOVED, {get_tuple_pair(1, "Test2")}, std::nullopt);
}

TEST_F(continuous_query_test, key_value_view_all_event_types) {
    auto kv_view =
        m_client.get_tables().get_table(TEST_TABLE_NAME)->get_key_value_view<cq_test_key_type, cq_test_value_type>();

    continuous_query_options opts;
    opts.set_poll_interval_ms(100);

    auto cq = kv_view.query_continuously(opts);
    auto store = make_store(cq);

    kv_view.put(nullptr, cq_test_key_type(1), cq_test_value_type("Test1"));
    kv_view.put(nullptr, cq_test_key_type(1), cq_test_value_type("Test2"));
    kv_view.remove(nullptr, cq_test_key_type(1));

    auto wait_res = store.query_events(3, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(3, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_object_pair(1, "Test1")});
    EXPECT_EVENT(store.get_event(1), table_row_event_type::UPDATED, {get_object_pair(1, "Test1")},
        {get_object_pair(1, "Test2")});
    EXPECT_EVENT(store.get_event(2), table_row_event_type::REMOVED, {get_object_pair(1, "Test2")}, std::nullopt);
}

TEST_F(continuous_query_test, event_types_created) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_event_types({table_row_event_type::CREATED});

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(1, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, "Test1")});
}

TEST_F(continuous_query_test, event_types_updated) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_event_types({table_row_event_type::UPDATED});

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(1, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::UPDATED, {get_tuple(1, "Test1")}, {get_tuple(1, "Test2")});
}

TEST_F(continuous_query_test, event_types_removed) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_event_types({table_row_event_type::REMOVED});

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(1, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::REMOVED, {get_tuple(1, "Test2")}, std::nullopt);
}

TEST_F(continuous_query_test, event_types_created_updated) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_event_types({table_row_event_type::CREATED, table_row_event_type::UPDATED});

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(2, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(2, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, "Test1")});
    EXPECT_EVENT(store.get_event(1), table_row_event_type::UPDATED, {get_tuple(1, "Test1")}, {get_tuple(1, "Test2")});
}

TEST_F(continuous_query_test, event_types_created_removed) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_event_types({table_row_event_type::CREATED, table_row_event_type::REMOVED});

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(2, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(2, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, "Test1")});
    EXPECT_EVENT(store.get_event(1), table_row_event_type::REMOVED, {get_tuple(1, "Test2")}, std::nullopt);
}

TEST_F(continuous_query_test, event_types_updated_removed) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_event_types({table_row_event_type::UPDATED, table_row_event_type::REMOVED});

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(2, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::UPDATED, {get_tuple(1, "Test1")}, {get_tuple(1, "Test2")});
    EXPECT_EVENT(store.get_event(1), table_row_event_type::REMOVED, {get_tuple(1, "Test2")}, std::nullopt);
}

TEST_F(continuous_query_test, filtered_columns) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_column_names({"ID"});

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store.query_events(3, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(3, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, nullptr)});
    EXPECT_EVENT(store.get_event(1), table_row_event_type::UPDATED, {get_tuple(1, nullptr)}, {get_tuple(1, nullptr)});
    EXPECT_EVENT(store.get_event(2), table_row_event_type::REMOVED, {get_tuple(1, nullptr)}, std::nullopt);
}

TEST_F(continuous_query_test, two_events_different_partitions) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.insert(nullptr, get_tuple(1, "Test"));
    m_simple_table_binary_view.insert(nullptr, get_tuple(2, "Lorem ipsum"));

    auto wait_res = store.query_events(2, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(2, store.get_events_num());
}

TEST_F(continuous_query_test, cancel_works) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test"));

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(1, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, "Test")});

    cq.cancel();

    auto complete = wait_for_condition(5s, [&]() -> bool { return cq.is_complete(); });
    ASSERT_TRUE(complete);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));

    wait_res = store.query_events(2, 500ms);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    ASSERT_TRUE(store.get_error().has_value());
    auto err_str = store.get_error()->what_str();
    EXPECT_THAT(err_str, testing::HasSubstr("Continuous query canceled"));
}

TEST_F(continuous_query_test, many_items_one_partition_page_size_10) {
    constexpr int ITEMS_CNT = 321;

    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_page_size(10);

    m_logger->set_debug_enabled(false);
    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    for (int i = 0; i < ITEMS_CNT; ++i) {
        m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test" + std::to_string(i)));
        std::this_thread::sleep_for(1ms);
    }

    auto wait_res = store.query_events(ITEMS_CNT, 10s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);
    m_logger->set_debug_enabled(true);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(ITEMS_CNT, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, "Test0")});

    for (int i = 1; i < ITEMS_CNT; ++i) {
        auto old = get_tuple(1, "Test" + std::to_string(i - 1));
        auto val = get_tuple(1, "Test" + std::to_string(i));
        EXPECT_EVENT(store.get_event(i), table_row_event_type::UPDATED, old, val);
    }
}

TEST_F(continuous_query_test, many_items_many_partitions_page_size_1) {
    constexpr int ITEMS_CNT = 321;

    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_page_size(1);

    m_logger->set_debug_enabled(false);
    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    for (int i = 0; i < ITEMS_CNT; ++i) {
        m_simple_table_binary_view.upsert(nullptr, get_tuple(i, "Test" + std::to_string(i)));
        std::this_thread::sleep_for(1ms);
    }

    auto wait_res = store.query_events(ITEMS_CNT, 10s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);
    m_logger->set_debug_enabled(true);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(ITEMS_CNT, store.get_events_num());
}

template<typename T1, typename T2>
ignite_timestamp time_point_to_ts(std::chrono::time_point<T1, T2> time_point) {
    using namespace std::chrono;

    auto secs = time_point_cast<seconds>(time_point).time_since_epoch().count();
    auto ns_frac = std::int32_t(time_point_cast<nanoseconds>(time_point).time_since_epoch().count() % 1'000'000'000);

    return {secs, ns_frac};
}

TEST_F(continuous_query_test, poll_interval_delays_arrival) {
    auto start = time_point_to_ts(std::chrono::system_clock::now());

    continuous_query_options opts;
    opts.set_poll_interval_ms(10'000);
    opts.set_watermark(continuous_query_watermark::of_timestamp(start));

    m_simple_table_binary_view.upsert(nullptr, get_tuple(0, "Test"));
    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(2, "Test"));

    wait_res = store.query_events(3, 1s);
    ASSERT_EQ(std::cv_status::timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(1, store.get_events_num());
}

TEST_F(continuous_query_test, transaction_interaction) {
    continuous_query_options opts;
    opts.set_poll_interval_ms(100);

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    auto tx1 = m_client.get_transactions().begin();
    m_simple_table_binary_view.upsert(&tx1, get_tuple(3, "Test1"));
    tx1.rollback();

    auto tx2 = m_client.get_transactions().begin();
    m_simple_table_binary_view.upsert(&tx2, get_tuple(4, "Test2"));
    tx2.commit();

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(1, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(4, "Test2")});

    cq.cancel();

    auto complete = wait_for_condition(5s, [&]() -> bool { return cq.is_complete(); });
    ASSERT_TRUE(complete);
    EXPECT_TRUE(cq.is_complete());
    ASSERT_EQ(1, store.get_events_num());
}

TEST_F(continuous_query_test, schema_update_while_query_is_active) {
    m_client.get_sql().execute(nullptr, nullptr,
        {"create table schema_update_while_query_is_active(" KEY_COLUMN " int primary key, " VAL_COLUMN
            R"( varchar) zone "zone1")"},
        {});

    continuous_query_options opts;
    opts.set_poll_interval_ms(100);

    auto binary_view = m_client.get_tables().get_table("schema_update_while_query_is_active")->get_record_binary_view();
    auto cq = binary_view.query_continuously(opts);
    auto store = make_store(cq);

    binary_view.upsert(nullptr, get_tuple(1, "Test"));

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(1, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, "Test")});

    m_client.get_sql().execute(nullptr, nullptr, {"alter table schema_update_while_query_is_active add column age int"}, {});

    auto val = get_tuple(1, "Test2");
    val.set("age", 20);

    binary_view.upsert(nullptr, val);

    wait_res = store.query_events(2, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    EXPECT_NO_ERROR(store);
    EXPECT_FALSE(cq.is_complete());
    ASSERT_EQ(2, store.get_events_num());

    auto updated_old = get_tuple(1, "Test");
    updated_old.set("age", nullptr);

    EXPECT_EVENT(store.get_event(1), table_row_event_type::UPDATED, updated_old, val);
}

TEST_F(continuous_query_test, start_timestamp_returns_past_events) {
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));

    std::this_thread::sleep_for(2s);
    auto ts = time_point_to_ts(std::chrono::system_clock::now());

    std::this_thread::sleep_for(2s);
    m_simple_table_binary_view.upsert(nullptr, get_tuple(2, "Test2"));

    continuous_query_options opts;
    opts.set_poll_interval_ms(100);
    opts.set_watermark(continuous_query_watermark::of_timestamp(ts));

    auto cq = m_simple_table_binary_view.query_continuously(opts);
    auto store = make_store(cq);

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    cq.cancel();

    auto complete = wait_for_condition(5s, [&]() -> bool { return cq.is_complete(); });
    ASSERT_TRUE(complete);
    EXPECT_TRUE(cq.is_complete());

    EXPECT_NO_ERROR(store);
    ASSERT_EQ(1, store.get_events_num());

    EXPECT_EVENT(store.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(2, "Test2")});
}

TEST_F(continuous_query_test, drop_table_invokes_error) {
    m_client.get_sql().execute(nullptr, nullptr,
        {"create table drop_table_invokes_error(" KEY_COLUMN " int primary key, " VAL_COLUMN
            R"( varchar) zone "zone1")"},
        {});

    auto binary_view = m_client.get_tables().get_table("drop_table_invokes_error")->get_record_binary_view();

    auto cq = binary_view.query_continuously({});
    auto store = make_store(cq);

    std::this_thread::sleep_for(100ms);

    m_client.get_sql().execute(nullptr, nullptr,
        {"drop table drop_table_invokes_error"}, {});

    auto wait_res = store.query_events(1, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    ASSERT_TRUE(store.get_error().has_value());
    auto err_str = store.get_error()->what_str();

    if (err_str.find("The table does not exist") != std::string::npos) {
        EXPECT_THAT(err_str, testing::HasSubstr("The table does not exist"));
    } else {
        EXPECT_THAT(err_str, testing::HasSubstr("No such partition"));
    }
}

continuous_query_watermark copy_and_check_watermark(const continuous_query_watermark &watermark) {
    auto watermark_str = watermark.to_string();
    auto watermark_copy = continuous_query_watermark::from_string(watermark_str);
    auto watermark_copy_str = watermark_copy.to_string();

    EXPECT_EQ(watermark_str, watermark_copy_str);

    return watermark_copy;
}

TEST_F(continuous_query_test, resume_from_previous_watermark_record) {
    continuous_query_options opts1;
    opts1.set_poll_interval_ms(100);

    auto cq1 = m_simple_table_binary_view.query_continuously(opts1);
    auto store1 = make_store(cq1);

    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test1"));
    m_simple_table_binary_view.upsert(nullptr, get_tuple(1, "Test2"));
    m_simple_table_binary_view.remove(nullptr, get_tuple(1));

    auto wait_res = store1.query_events(3, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);

    cq1.cancel();

    auto complete = wait_for_condition(5s, [&]() -> bool { return cq1.is_complete(); });
    ASSERT_TRUE(complete);
    EXPECT_TRUE(cq1.is_complete());

    EXPECT_NO_ERROR(store1);
    ASSERT_EQ(3, store1.get_events_num());

    EXPECT_EVENT(store1.get_event(0), table_row_event_type::CREATED, std::nullopt, {get_tuple(1, "Test1")});
    EXPECT_EVENT(store1.get_event(1), table_row_event_type::UPDATED, {get_tuple(1, "Test1")}, {get_tuple(1, "Test2")});
    EXPECT_EVENT(store1.get_event(2), table_row_event_type::REMOVED, {get_tuple(1, "Test2")}, std::nullopt);

    continuous_query_options opts2;
    opts2.set_poll_interval_ms(100);
    auto copy = copy_and_check_watermark(store1.get_watermark(0));
    opts2.set_watermark(copy);

    auto cq2 = m_simple_table_binary_view.query_continuously(opts2);
    auto store2 = make_store(cq2);

    wait_res = store2.query_events(2, 5s);
    ASSERT_EQ(std::cv_status::no_timeout, wait_res);
    EXPECT_NO_ERROR(store2);
    ASSERT_EQ(2, store2.get_events_num());

    EXPECT_EVENT(store2.get_event(0), table_row_event_type::UPDATED, {get_tuple(1, "Test1")}, {get_tuple(1, "Test2")});
    EXPECT_EVENT(store2.get_event(1), table_row_event_type::REMOVED, {get_tuple(1, "Test2")}, std::nullopt);
}

TEST_F(continuous_query_test, batch_watermark_is_same_as_event_watermark) {
    auto cq = m_simple_table_binary_view.query_continuously({});

    m_simple_table_binary_view.insert(nullptr, get_tuple(1, "foo"));

    auto batch = cq.get_next();

    auto b_wm = batch.get_watermark();

    ASSERT_FALSE(batch.get_events().empty());

    auto last_event = *batch.get_events().rbegin();
    auto e_wm = last_event.get_watermark();

    ASSERT_EQ(b_wm.to_string(), e_wm.to_string());
}

TEST_F(continuous_query_test, empty_batch_produced) {
    continuous_query_options opts;
    opts.set_enable_empty_batches(true);

    auto cq = m_simple_table_binary_view.query_continuously(opts);

    auto batch = cq.get_next();

    ASSERT_TRUE(batch.get_events().empty());

    EXPECT_NO_THROW({ auto b_wm = batch.get_watermark(); });
}

TEST_F(continuous_query_test, archive_event_handled) {
    m_table_with_sec_storage_bin_view.insert(nullptr, {{"KEY", 42L}, {"VAL", "foo"}});

    auto cq = m_table_with_sec_storage_bin_view.query_continuously({});

    auto store = make_store(cq);

    auto job_target = job_target::any_node(m_client.get_cluster_nodes());
    auto job_desc =
        job_descriptor::builder("org.apache.ignite.internal.runner.app.PlatformTestNodeRunner$ArchiveRowJobCpp")
            .build();
    auto exec = m_client.get_compute().submit(job_target, job_desc, {42L});

    exec.get_result();

    ASSERT_EQ(job_status::COMPLETED, exec.get_state()->status);

    auto status = store.query_events(1, 5s);

    ASSERT_EQ(std::cv_status::no_timeout, status);

    EXPECT_EVENT(store.get_event(0), table_row_event_type::ARCHIVED, ignite_tuple{{"KEY", 42L}, {"VAL", "foo"}}, std::nullopt);
}