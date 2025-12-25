/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/continuous_query/continuous_query_watermark.h"
#include "ignite/client/detail/continuous_query/watermark_provider_impl.h"
#include "ignite/common/uuid.h"

#include <sstream>

#include <gtest/gtest.h>

namespace ignite::detail {

class watermark_accessor {
public:
    watermark_accessor(continuous_query_watermark &wm) // NOLINT(*-explicit-constructor)
        : m_wm(wm) {}

    std::shared_ptr<continuous_query_watermark_impl> &impl() { return m_wm.m_impl; }

    std::int64_t &timestamp() { return m_wm.m_timestamp; }

    static continuous_query_watermark from_impl(std::shared_ptr<continuous_query_watermark_impl> impl) {
        return continuous_query_watermark{std::move(impl)};
    }

private:
    continuous_query_watermark &m_wm;
};

} // namespace ignite::detail

using namespace ignite;
using namespace detail;

void check_from_timestamp(ignite_timestamp ts, const std::string &exp, int line) {
    auto watermark_1 = continuous_query_watermark::of_timestamp(ts);
    auto watermark_1_str = watermark_1.to_string();
    EXPECT_EQ(watermark_1_str, exp) << "Line: " << line;

    auto watermark_2 = continuous_query_watermark::from_string(watermark_1_str);
    auto watermark_2_str = watermark_2.to_string();
    EXPECT_EQ(watermark_1_str, watermark_2_str) << "Line: " << line;

    watermark_accessor wma1(watermark_1);
    watermark_accessor wma2(watermark_2);
    EXPECT_EQ(wma1.timestamp(), wma2.timestamp()) << "Line: " << line;
    EXPECT_FALSE(wma1.impl()) << "Line: " << line;
    EXPECT_FALSE(wma2.impl()) << "Line: " << line;
}

void check_from_arrays(
    std::vector<uuid> &&row_ids, std::vector<std::int64_t> &&timestamps, const std::string &exp, int line) {
    auto impl1 = std::make_shared<continuous_query_watermark_impl>(std::move(row_ids), std::move(timestamps));
    auto watermark_1 = watermark_accessor::from_impl(impl1);
    auto watermark_1_str = watermark_1.to_string();
    EXPECT_EQ(watermark_1_str, exp) << "Line: " << line;

    auto watermark_2 = continuous_query_watermark::from_string(watermark_1_str);
    auto watermark_2_str = watermark_2.to_string();
    EXPECT_EQ(watermark_1_str, watermark_2_str) << "Line: " << line;

    watermark_accessor wma1(watermark_1);
    watermark_accessor wma2(watermark_2);
    EXPECT_EQ(wma1.timestamp(), 0) << "Line: " << line;
    EXPECT_EQ(wma2.timestamp(), 0) << "Line: " << line;
    EXPECT_TRUE(wma1.impl()) << "Line: " << line;
    EXPECT_TRUE(wma2.impl()) << "Line: " << line;
    EXPECT_EQ(wma1.impl()->get_timestamps(), wma2.impl()->get_timestamps()) << "Line: " << line;
    EXPECT_EQ(wma1.impl()->get_row_ids(), wma2.impl()->get_row_ids()) << "Line: " << line;
}

TEST(continuous_query_watermark, from_timestamp) {
    check_from_timestamp({}, R"({})", __LINE__);
    check_from_timestamp({0, 0}, R"({})", __LINE__);
    check_from_timestamp({0, 1}, R"({})", __LINE__);
    check_from_timestamp({0, 10}, R"({})", __LINE__);
    check_from_timestamp({0, 100}, R"({})", __LINE__);
    check_from_timestamp({1, 0}, R"({"ts":"1000"})", __LINE__);
    check_from_timestamp({0, 123456789}, R"({"ts":"123"})", __LINE__);
    check_from_timestamp({1, 123456789}, R"({"ts":"1123"})", __LINE__);
    check_from_timestamp({10, 0}, R"({"ts":"10000"})", __LINE__);
    check_from_timestamp({123456789, 123456789}, R"({"ts":"123456789123"})", __LINE__);
    check_from_timestamp({3456275, 25427572}, R"({"ts":"3456275025"})", __LINE__);
}

TEST(continuous_query_watermark, from_arrays) {
    check_from_arrays({}, {}, R"({"row_ids":[],"tss":[]})", __LINE__);
    check_from_arrays({{}}, {1}, R"({"row_ids":["00000000-0000-0000-0000-000000000000"],"tss":["1"]})", __LINE__);

    check_from_arrays({{}, {}}, {42, 4398472936},
        R"({"row_ids":)"
        R"(["00000000-0000-0000-0000-000000000000","00000000-0000-0000-0000-000000000000"],)"
        R"("tss":["42","4398472936"]})",
        __LINE__);

    check_from_arrays({{0x655f47c610bc432b, std::int64_t(0xa38bf1fb1ff2baba)},
                          {std::int64_t(0xf17125cacc7a422c), std::int64_t(0xa1b6276e621bb440)},
                          {std::int64_t(0xfe82860bdc66486e), 0x7f66601cd4a19dbc}},
        {1, 2, 3},
        R"({"row_ids":)"
        R"(["655f47c6-10bc-432b-a38b-f1fb1ff2baba",)"
        R"("f17125ca-cc7a-422c-a1b6-276e621bb440",)"
        R"("fe82860b-dc66-486e-7f66-601cd4a19dbc"],)"
        R"("tss":["1","2","3"]})",
        __LINE__);
}
