/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "string_utils.h"

#include <gtest/gtest.h>

using namespace ignite;

/**
 * Test suite.
 */
class string_utils_test : public ::testing::Test {};

TEST_F(string_utils_test, ltrim_basic) {
    auto test_ltrim = [](std::string_view expected, std::string_view in) { EXPECT_EQ(detail::ltrim(in), expected); };

    test_ltrim("", "");
    test_ltrim("", " ");
    test_ltrim("", "      ");
    test_ltrim("abc", "abc");
    test_ltrim("abc ", "abc ");
    test_ltrim("abc", " abc");
    test_ltrim("abc ", " abc ");
    test_ltrim("abc     ", "     abc     ");
    test_ltrim("a b  c ", " a b  c ");
}

TEST_F(string_utils_test, rtrim_basic) {
    auto test_rtrim = [](std::string_view expected, std::string_view in) { EXPECT_EQ(detail::rtrim(in), expected); };

    test_rtrim("", "");
    test_rtrim("", " ");
    test_rtrim("", "      ");
    test_rtrim("abc", "abc");
    test_rtrim("abc", "abc ");
    test_rtrim(" abc", " abc");
    test_rtrim(" abc", " abc ");
    test_rtrim("     abc", "     abc     ");
    test_rtrim(" a b  c", " a b  c ");
}

TEST_F(string_utils_test, trim_basic) {
    auto test_trim = [](std::string_view expected, std::string_view in) { EXPECT_EQ(detail::trim(in), expected); };

    test_trim("", "");
    test_trim("", " ");
    test_trim("", "      ");
    test_trim("abc", "abc");
    test_trim("abc", "abc ");
    test_trim("abc", " abc");
    test_trim("abc", " abc ");
    test_trim("abc", "     abc     ");
    test_trim("a b  c", " a b  c ");
}

TEST_F(string_utils_test, split_once_basic) {
    auto test_split_once = [](std::string_view p1, std::string_view p2, std::string_view in, char d) {
        auto res = detail::split_once(in, d);
        EXPECT_EQ(p1, res.first);
        EXPECT_EQ(p2, res.second);
    };

    test_split_once("a1", "a2,a3,a4,a5", "a1,a2,a3,a4,a5", ',');
    test_split_once("a2", "a3,a4,a5", "a2,a3,a4,a5", ',');
    test_split_once("a3", "a4,a5", "a3,a4,a5", ',');
    test_split_once("a4", "a5", "a4,a5", ',');
    test_split_once("a5", "", "a5", ',');
    test_split_once("", "", "", ',');

    test_split_once("", ",,", ",,,", ',');

    test_split_once("a1", "a2;a3;a4;a5", "a1;a2;a3;a4;a5", ';');
    test_split_once("a1;a2;a3;a4;a5", "", "a1;a2;a3;a4;a5", ',');
}

TEST_F(string_utils_test, split_basic) {
    auto test_split = [](std::vector<std::string_view> exp, std::string_view in, char d) {
        std::vector<std::string_view> res;
        detail::for_every_delimited(in, d, [&res](auto s) { res.push_back(s); });

        ASSERT_EQ(exp.size(), res.size());

        for (size_t i = 0; i < exp.size(); ++i) {
            EXPECT_EQ(exp[i], res[i]) << "Vectors differ at index " << i;
        }
    };

    test_split({"a", "b"}, "a,b", ',');
    test_split({"a", "b", "c", "d", "bar"}, "a,b,c,d,bar", ',');

    test_split({}, "", ',');
    test_split({"abc"}, "abc", ',');
    test_split({"abc"}, "abc,", ',');
    test_split({"", "abc"}, ",abc", ',');
    test_split({"a", "", "b"}, "a,,b", ',');
}

TEST_F(string_utils_test, to_lower_basic) {
    auto test_to_lower = [](std::string_view exp, std::string in) { EXPECT_EQ(detail::to_lower(std::move(in)), exp); };

    test_to_lower("lorem ipsum", "Lorem Ipsum");
    test_to_lower("lorem ipsum", "LOREM IPSUM");
    test_to_lower("lorem ipsum", "LoRem IpsUM");
    test_to_lower("lorem ipsum", "lorem ipsum");
}
