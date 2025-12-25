/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/common/detail/hash_utils.h"

#include <gtest/gtest.h>

using namespace ignite;
using namespace detail;

/**
 * Test suite.
 */
class hash_utils_test : public ::testing::Test {};

template<typename T>
std::vector<std::byte> to_bytes(T elems) {
    std::vector<std::byte> data;
    data.reserve(elems.size());
    for (auto i : elems) {
        data.push_back(std::byte(i));
    }
    return data;
}

std::int32_t hash32bytes(std::initializer_list<int> il) {
    return hash32(to_bytes(std::move(il)));
}

std::int32_t hash32bytes(std::string data) {
    return hash32(to_bytes(std::move(data)));
}

TEST_F(hash_utils_test, hash32_bytes) {
    // The constant values were calculated using Java code (see HashUtils class)

    EXPECT_EQ(hash32bytes({42}), std::int32_t(0x76A6ACD8));
    EXPECT_EQ(hash32bytes({1, 1}), std::int32_t(0xC0DC46D7L));
    EXPECT_EQ(hash32bytes({1, 2, 3, 4}), std::int32_t(0xD0049F4A));
    EXPECT_EQ(hash32bytes({128, 0, -1, 255, 127, -127, -128}), std::int32_t(0xC0457772));

    std::vector<std::byte> long_data;
    for (int i = 0; i < 10000; i++) {
        long_data.push_back(std::byte(i * 759028375));
    }

    EXPECT_EQ(hash32(long_data), std::int32_t(0xAA935B82));

    EXPECT_EQ(hash32bytes({'a', 'b', 'c'}), std::int32_t(0x8B3B4758));
    EXPECT_EQ(hash32bytes("Lorem ipsum dolor sit amet"), std::int32_t(0x73B3A579));
}
