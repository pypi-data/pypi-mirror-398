/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/common/detail/name_utils.h"
#include "ignite/common/ignite_error.h"
#include "tests/test-common/hidden_param.h"

#include <gtest/gtest.h>

using namespace ignite;
using namespace detail;
using namespace name_utils_constant;

class quote_if_needed_fixture : public ::testing::TestWithParam<std::tuple<hidden, hidden>> {};

TEST_P(quote_if_needed_fixture, quote_if_needed) {
    auto [name, expected] = unhide(GetParam());

    EXPECT_EQ(expected, quote_if_needed(name, QUOTE_CHAR));
    EXPECT_EQ(name, parse_identifier(quote_if_needed(name, QUOTE_CHAR), QUOTE_CHAR, SEPARATOR_CHAR));
}


INSTANTIATE_TEST_SUITE_P(
    client_name_utils, quote_if_needed_fixture,
    ::testing::Values(
        std::make_tuple("foo", "\"foo\""),
        std::make_tuple("fOo", "\"fOo\""),
        std::make_tuple("FOO", "FOO"),
        std::make_tuple("_FOO", "_FOO"),
        std::make_tuple("_", "_"),
        std::make_tuple("__", "__"),
        std::make_tuple("_\xC2\xB7", "_\xC2\xB7"),
        std::make_tuple("A\xCC\x80", "A\xCC\x80"),
        std::make_tuple("1o0", "\"1o0\""),
        std::make_tuple("@#$", "\"@#$\""),
        std::make_tuple("f16", "\"f16\""),
        std::make_tuple("F16", "F16"),
        std::make_tuple("Ff16", "\"Ff16\""),
        std::make_tuple("FF16", "FF16"),
        std::make_tuple(" ", "\" \""),
        std::make_tuple(" F", "\" F\""),
        std::make_tuple(" ,", "\" ,\""),
        std::make_tuple("\xF0\x9F\x98\x85", "\"\xF0\x9F\x98\x85\""),
        std::make_tuple("\"foo\"", "\"\"\"foo\"\"\""),
        std::make_tuple("\"fOo\"", "\"\"\"fOo\"\"\""),
        std::make_tuple("\"f.f\"", "\"\"\"f.f\"\"\""),
        std::make_tuple("foo\"bar\"", "\"foo\"\"bar\"\"\""),
        std::make_tuple("foo\"bar", "\"foo\"\"bar\"")
    ),
    print_test_index<quote_if_needed_fixture>
);


class malformed_identifiers_fixture : public ::testing::TestWithParam<hidden> {};

TEST_P(malformed_identifiers_fixture, parse_identifier_malformed) {
    auto malformed = unhide(GetParam());

    EXPECT_THROW(
        {
            try {
                (void) parse_identifier(malformed, QUOTE_CHAR, SEPARATOR_CHAR);
            } catch (const ignite_error &e) {
                EXPECT_EQ(e.get_status_code(), error::code::ILLEGAL_ARGUMENT);
                throw;
            }
        },
        ignite_error);
}

INSTANTIATE_TEST_SUITE_P(
    client_name_utils, malformed_identifiers_fixture,
    ::testing::Values(
        " ",
        "foo-1",
        "f.f",
        "f f",
        "f\"f",
        "f\"\"f",
        "\"foo",
        "\"fo\"o\"",
        "1o0",
        "@#$",
        "\xF0\x9F\x98\x85",
        "f\xF0\x9F\x98\x85",
        "A\xF0",
        "$foo",
        "foo$"
    ),
    print_test_index<malformed_identifiers_fixture>
);


class valid_identifiers_fixture : public ::testing::TestWithParam<std::tuple<hidden, hidden>> {};

TEST_P(valid_identifiers_fixture, parse_identifier_valid) {
    auto [name, expected] = unhide(GetParam());

    EXPECT_EQ(name, parse_identifier(quote_if_needed(name, QUOTE_CHAR), QUOTE_CHAR, SEPARATOR_CHAR));
}

INSTANTIATE_TEST_SUITE_P(
    client_name_utils, valid_identifiers_fixture,
    ::testing::Values(
        std::make_tuple("foo", "FOO"),
        std::make_tuple("fOo", "FOO"),
        std::make_tuple("FOO", "FOO"),
        std::make_tuple("fo_o", "FO_O"),
        std::make_tuple("_foo", "_FOO"),
        std::make_tuple("_\xC2\xB7", "_\xC2\xB7"),
        std::make_tuple("A\xCC\x80", "A\xCC\x80"),
        std::make_tuple("\"FOO\"", "FOO"),
        std::make_tuple("\"foo\"", "foo"),
        std::make_tuple("\"fOo\"", "fOo"),
        std::make_tuple("\"$fOo\"", "$fOo"),
        std::make_tuple("\"f.f\"", "f.f"),
        std::make_tuple("\"f\"\"f\"", "f\"f"),
        std::make_tuple("\" \"", " "),
        std::make_tuple("\"   \"", "   "),
        std::make_tuple("\",\"", ","),
        std::make_tuple("\"\xF0\x9F\x98\x85\"", "\xF0\x9F\x98\x85"),
        std::make_tuple("\"f\xF0\x9F\x98\x85\"", "f\xF0\x9F\x98\x85")
    ),
    print_test_index<valid_identifiers_fixture>
);

