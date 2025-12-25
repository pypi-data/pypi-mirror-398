/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/common/primitive.h"

#include <gtest/gtest.h>

#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>

using namespace ignite;

template<typename T>
void check_primitive_type(ignite_type expected) {
    primitive val(T{});
    EXPECT_EQ(val.get_type(), expected);
}

TEST(primitive, get_column_type) {
    check_primitive_type<std::nullptr_t>(ignite_type::NIL);
    check_primitive_type<bool>(ignite_type::BOOLEAN);
    check_primitive_type<std::int8_t>(ignite_type::INT8);
    check_primitive_type<std::int16_t>(ignite_type::INT16);
    check_primitive_type<std::int32_t>(ignite_type::INT32);
    check_primitive_type<std::int64_t>(ignite_type::INT64);
    check_primitive_type<float>(ignite_type::FLOAT);
    check_primitive_type<double>(ignite_type::DOUBLE);
    check_primitive_type<big_decimal>(ignite_type::DECIMAL);
    check_primitive_type<ignite_date>(ignite_type::DATE);
    check_primitive_type<ignite_time>(ignite_type::TIME);
    check_primitive_type<ignite_date_time>(ignite_type::DATETIME);
    check_primitive_type<ignite_timestamp>(ignite_type::TIMESTAMP);
    check_primitive_type<ignite_period>(ignite_type::PERIOD);
    check_primitive_type<ignite_duration>(ignite_type::DURATION);
    check_primitive_type<uuid>(ignite_type::UUID);
    check_primitive_type<std::string>(ignite_type::STRING);
    check_primitive_type<std::vector<std::byte>>(ignite_type::BYTE_ARRAY);
}

TEST(primitive, null_value_by_nullptr) {
    primitive val(nullptr);
    EXPECT_EQ(val.get_type(), ignite_type::NIL);
    EXPECT_TRUE(val.is_null());
}

TEST(primitive, null_value_by_nullopt) {
    primitive val(std::nullopt);
    EXPECT_EQ(val.get_type(), ignite_type::NIL);
    EXPECT_TRUE(val.is_null());
}
