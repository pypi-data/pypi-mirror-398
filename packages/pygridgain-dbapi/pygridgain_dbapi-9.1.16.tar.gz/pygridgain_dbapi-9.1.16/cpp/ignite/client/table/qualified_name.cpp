/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/common/detail/name_utils.h"
#include "ignite/client/table/qualified_name.h"
#include "ignite/client/detail/argument_check_utils.h"
#include "ignite/common/detail/string_utils.h"

#include "uni_algo/ranges_conv.h"

namespace {
using namespace ignite;

std::pair<std::string_view, std::string_view> split_at(std::string_view input, size_t pos) {
    return {input.substr(0,pos), input.substr(pos + 1)};
}

} // anonymous namespace


namespace ignite {

qualified_name qualified_name::create(std::string_view schema_name, std::string_view object_name) {
    detail::arg_check::container_non_empty(object_name, "Object name");

    if (schema_name.empty()) {
        schema_name = DEFAULT_SCHEMA_NAME;
    }

    return {detail::parse_identifier(schema_name, QUOTE_CHAR, SEPARATOR_CHAR),
        detail::parse_identifier(object_name, QUOTE_CHAR, SEPARATOR_CHAR)};
}

qualified_name qualified_name::parse(std::string_view simple_or_canonical_name) {
    detail::arg_check::container_non_empty(simple_or_canonical_name, "Object name");

    auto utf8_view = una::ranges::utf8_view(simple_or_canonical_name);
    auto separator_pos = detail::find_separator(
        simple_or_canonical_name, utf8_view.begin(), utf8_view.end(), char32_t(QUOTE_CHAR), char32_t(SEPARATOR_CHAR));

    if (separator_pos == utf8_view.end()) {
        return create({}, simple_or_canonical_name);
    }

    auto next_separator = detail::find_separator(simple_or_canonical_name, std::next(separator_pos),
     utf8_view.end(), char32_t(QUOTE_CHAR), char32_t(SEPARATOR_CHAR));

    detail::arg_check::is_true(next_separator == utf8_view.end(),
        "Canonical name should have at most two parts: '" + std::string{simple_or_canonical_name} + "'");

    auto offset = separator_pos.begin() - utf8_view.begin().begin();
    auto [schema_name, object_name] = split_at(simple_or_canonical_name, offset);
    detail::arg_check::container_non_empty(schema_name, "Schema part of the canonical name");
    detail::arg_check::container_non_empty(object_name, "Object part of the canonical name");

    return create(schema_name, object_name);
}

const std::string & qualified_name::get_canonical_name() const {
    if (m_canonical_name.empty()) {
        m_canonical_name = detail::to_canonical_name(m_schema_name, m_object_name, QUOTE_CHAR, SEPARATOR_CHAR);
    }
    return m_canonical_name;
}

} // namespace ignite
