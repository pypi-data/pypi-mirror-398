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
#include "ignite/common/detail/string_utils.h"

#include <sstream>
#include <iomanip>

namespace ignite {

/**
 * Write a single entry.
 * @tparam T Entry type
 * @param stream Stream
 * @param val Value.
 */
template<typename T>
void write_single_entry(std::ostream &stream, T val) {
    stream << '"' << val << '"';
}

/**
 * Write a vector of values.
 * @tparam T Type of values.
 * @param stream Stream.
 * @param array Vector.
 */
template<typename T>
void write_vector(std::ostream &stream, const std::vector<T> &array) {
    stream << '[';
    if (!array.empty()) {
        for (std::size_t i = 0; i < array.size() - 1; ++i) {
            write_single_entry(stream, array[i]);
            stream << ',';
        }
        write_single_entry(stream, array.back());
    }
    stream << "]";
}

std::string ignite::continuous_query_watermark::to_string() const {
    std::stringstream buf;
    buf << '{';
    if (!m_impl) {
        if (m_timestamp) {
            buf << R"("ts":")" << m_timestamp << '"';
        }
    } else {
        buf << R"("row_ids":)";
        write_vector(buf, m_impl->get_row_ids());

        buf << R"(,"tss":)";
        write_vector(buf, m_impl->get_timestamps());
    }
    buf << '}';
    return buf.str();
}

void expect(bool cond, const std::string& err_msg) {
    if (!cond)
        throw ignite_error(err_msg);
}

bool starts_with(std::string_view &str, std::string_view exp) {
    if (str.size() < exp.size())
        return false;

    auto start = str.substr(0, exp.size());
    if (start == exp) {
        str.remove_prefix(exp.size());
        return true;
    }
    return false;
}

std::string_view expect_starts_with(std::string_view str, std::string_view exp, const std::string& err_msg) {
    expect(starts_with(str, exp), err_msg);
    return str;
}

std::string_view expect_ends_with(std::string_view str, std::string_view exp, const std::string& err_msg) {
    expect(str.size() >= exp.size(), err_msg);
    auto end = str.substr(str.size() - exp.size());
    expect(end == exp, err_msg);
    str.remove_suffix(exp.size());
    return str;
}

std::string_view expect_colon(std::string_view str) {
    str = detail::trim(str);
    str = expect_starts_with(str, ":", "Expected ':' between name field and value");
    str = detail::trim(str);
    return str;
}

std::string_view skip_coma(std::string_view str) {
    str = detail::trim(str);
    if (!str.empty()) {
        str = expect_starts_with(str, ",", "Expected ',' between fields");
        str = detail::trim(str);
    }
    return str;
}

std::pair<std::string_view, std::string_view> expect_starts_with_array(std::string_view str, const std::string& err_msg) {
    str = detail::ltrim(str);
    str = expect_starts_with(str, "[", err_msg);

    return detail::split_once(str, ']');
}

std::pair<std::string_view, std::string_view> expect_starts_with_string(std::string_view str, const std::string& err_msg) {
    str = detail::ltrim(str);
    str = expect_starts_with(str, "\"", err_msg);

    return detail::split_once(str, '"');
}

continuous_query_watermark continuous_query_watermark::from_string(std::string_view str) {
    continuous_query_watermark res;
    auto buf = detail::trim(str);

    buf = expect_starts_with(buf, "{", "Watermark object representation should start with '{'");
    buf = expect_ends_with(buf, "}", "Watermark object representation should end with '}'");
    buf = detail::trim(buf);

    std::optional<std::vector<uuid>> row_ids;
    std::optional<std::vector<std::int64_t>> timestamps;

    while (!buf.empty()) {
        if (starts_with(buf, "\"ts\"")) {
            buf = expect_colon(buf);
            auto parsed_pair = expect_starts_with_string(buf, "Timestamp value should be written as a string");
            auto elem = parsed_pair.first;
            buf = parsed_pair.second;

            auto ts = detail::parse_int64(elem);
            expect(ts.has_value(), "Unknown format of timestamp field");

            res.m_timestamp = *ts;
        } else if (starts_with(buf, "\"row_ids\"")) {
            buf = expect_colon(buf);
            auto parsed_pair = expect_starts_with_array(buf, "Row IDs should be written as an array");
            auto elem = parsed_pair.first;
            buf = parsed_pair.second;

            row_ids = std::vector<uuid>{};
            detail::for_every_delimited(elem, ',', [&](std::string_view value) {
                value = detail::trim(value);
                value = expect_starts_with(value, "\"", "Row ID should be written as a string");
                value = expect_ends_with(value, "\"", "Row ID should be written as a string");
                value = detail::trim(value);

                row_ids->push_back(detail::lexical_cast<uuid>(value));
            });
        } else if (starts_with(buf, "\"tss\"")) {
            buf = expect_colon(buf);
            auto parsed_pair = expect_starts_with_array(buf, "Timestamps should be written as an array");
            auto elem = parsed_pair.first;
            buf = parsed_pair.second;

            timestamps = std::vector<std::int64_t>{};
            detail::for_every_delimited(elem, ',', [&](std::string_view value) {
                value = detail::trim(value);
                value = expect_starts_with(value, "\"", "Timestamp should be written as a string");
                value = expect_ends_with(value, "\"", "Timestamp should be written as a string");
                value = detail::trim(value);

                auto ts = detail::parse_int64(value);
                expect(ts.has_value(), "Unknown format of timestamp value");

                timestamps->push_back(*ts);
            });
        } else {
            throw ignite_error("Unexpected field");
        }
        // Skipping a coma
        buf = skip_coma(buf);
    }

    if (row_ids || timestamps) {
        expect(row_ids && timestamps, "Row IDs array size should be the same as an Timestamps");
        expect(row_ids->size() == timestamps->size(), "Row IDs array size should be the same as an Timestamps");
        auto impl = std::make_shared<detail::continuous_query_watermark_impl>(std::move(*row_ids), std::move(*timestamps));
        res.m_impl = std::move(impl);
    }

    return res;
}

} // namespace ignite
