/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/detail/table/schema.h"
#include "ignite/client/detail/utils.h"

#include "ignite/protocol/buffer_adapter.h"
#include "ignite/protocol/reader.h"
#include "ignite/protocol/writer.h"

#include <gtest/gtest.h>

using namespace ignite;
using namespace detail;

inline column make_column(std::string name, ignite_type type, std::int32_t key_index = -1) {
    column val;
    val.name = std::move(name);
    val.type = type;
    val.key_index = key_index;

    return val;
}

std::shared_ptr<schema> make_test_schema() {
    std::vector<column> columns;
    columns.push_back(make_column("VAL_COL1", ignite_type::INT32));
    columns.push_back(make_column("KEY_COL1", ignite_type::STRING, 0));
    columns.push_back(make_column("VAL_COL2", ignite_type::STRING));
    columns.push_back(make_column("KEY_COL2", ignite_type::INT32, 1));

    return schema::create_instance(0, std::move(columns));
}

ignite_tuple write_read_tuple(const ignite_tuple &tuple, const std::shared_ptr<schema> &sch, bool key_only) {
    std::vector<std::byte> message;
    protocol::buffer_adapter buffer(message);

    protocol::writer writer(buffer);

    write_tuple(writer, *sch, tuple, key_only);

    protocol::reader reader(message);
    reader.skip(); // Skip bitset

    return read_tuple(reader, sch.get(), key_only);
}

TEST(client_utils, tuple_write_read_random_order_all_columns) {
    auto sch = make_test_schema();

    ignite_tuple tuple{{"VAL_COL1", std::int32_t(42)}, {"VAL_COL2", std::string("Lorem ipsum")},
        {"KEY_COL2", std::int32_t(1337)}, {"KEY_COL1", std::string("Test value")}};

    auto res_tuple = write_read_tuple(tuple, sch, false);

    ASSERT_EQ(4, res_tuple.column_count());
    EXPECT_EQ("VAL_COL1", res_tuple.column_name(0));
    EXPECT_EQ("KEY_COL1", res_tuple.column_name(1));
    EXPECT_EQ("VAL_COL2", res_tuple.column_name(2));
    EXPECT_EQ("KEY_COL2", res_tuple.column_name(3));

    EXPECT_EQ(std::int32_t(42), res_tuple.get(0));
    EXPECT_EQ(std::string("Test value"), res_tuple.get(1));
    EXPECT_EQ(std::string("Lorem ipsum"), res_tuple.get(2));
    EXPECT_EQ(std::int32_t(1337), res_tuple.get(3));
}

TEST(client_utils, tuple_write_read_random_order_key_only) {
    auto sch = make_test_schema();

    ignite_tuple tuple{{"VAL_COL1", std::int32_t(42)}, {"VAL_COL2", std::string("Lorem ipsum")},
        {"KEY_COL2", std::int32_t(1337)}, {"KEY_COL1", std::string("Test value")}};

    auto res_tuple = write_read_tuple(tuple, sch, true);

    ASSERT_EQ(2, res_tuple.column_count());
    EXPECT_EQ("KEY_COL1", res_tuple.column_name(0));
    EXPECT_EQ("KEY_COL2", res_tuple.column_name(1));

    EXPECT_EQ(std::string("Test value"), res_tuple.get(0));
    EXPECT_EQ(std::int32_t(1337), res_tuple.get(1));
}