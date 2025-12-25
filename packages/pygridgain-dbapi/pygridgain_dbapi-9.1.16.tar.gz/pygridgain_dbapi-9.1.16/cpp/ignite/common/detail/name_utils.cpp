/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "name_utils.h"
#include "string_utils.h"

#include "uni_algo/case.h"
#include "uni_algo/prop.h"
#include "uni_algo/ranges_conv.h"

namespace ignite::detail {

std::string quote(std::string_view &str, char quote_char) {
    auto quote_num = std::count(str.begin(), str.end(), quote_char);

    std::string res;
    res.reserve(str.size() + quote_num + 2);

    res.push_back(quote_char);

    if (quote_num) {
        for (auto c : str) {
            if (c == quote_char) {
                res.push_back(quote_char);
            }
            res.push_back(c);
        }
    } else {
        res.append(str);
    }

    res.push_back(quote_char);
    return res;
}

std::string quote_if_needed(std::string_view name, char quote_char) {
    if (name.empty()) {
        return std::string{name};
    }

    if (!is_normalized_identifier_start(name[0])) {
        return quote(name, quote_char);
    }

    auto other_chars = name;
    other_chars.remove_prefix(1);

    auto utf8_view = una::ranges::utf8_view(other_chars);
    for (char32_t cur : utf8_view) {
        if (!is_normalized_identifier_start(cur) && !is_identifier_extend(cur)) {
            return quote(name, quote_char);
        }
    }

    return std::string{name};
}

std::string to_canonical_name(std::string_view schema_name, std::string_view object_name,
    char quote_char, char separator_char) {
    return quote_if_needed(schema_name, quote_char)
        + separator_char
        + quote_if_needed(object_name, quote_char);
}

std::string unquote(std::string_view &identifier, char quote_char)
{
    if (identifier.empty())
        return {};

    if (identifier.front() == quote_char) {
        identifier.remove_prefix(1);
        identifier.remove_suffix(1);

        auto quote_num = std::count(identifier.begin(), identifier.end(), quote_char);
        if (quote_num == 0)
            return std::string{identifier};

        std::string res;
        res.reserve(identifier.size() - quote_num);

        auto ignore_quote = false;
        for (auto c : identifier) {
            // There are no checks as the checks should be conducted before calling this functions.
            if (c == quote_char) {
                if (ignore_quote) {
                    ignore_quote = false;
                    continue;
                }
                ignore_quote = true;
            }
            res.push_back(c);
        }

        return res;
    }

    return una::cases::to_uppercase_utf8(identifier);
}

std::string parse_identifier(std::string_view identifier, char quote_char, char separator_char)
{
    auto utf8_view = una::ranges::utf8_view(identifier);
    auto separator_pos = find_separator(identifier, utf8_view.begin(), utf8_view.end(), quote_char, separator_char);

    if (separator_pos != utf8_view.end()) {
        throw ignite_error(error::code::ILLEGAL_ARGUMENT,
            "Unexpected separator in identifier: " + std::string{identifier});
    }

    return unquote(identifier, quote_char);
}

bool is_identifier_extend(char32_t codepoint) {
    constexpr std::int32_t UNICODE_MIDDLE_DOT = 0xB7;

    auto cat = una::codepoint::get_general_category(codepoint);

    return codepoint == UNICODE_MIDDLE_DOT
        || cat == una::codepoint::general_category::Mn
        || cat == una::codepoint::general_category::Mc
        || cat == una::codepoint::general_category::Nd
        || cat == una::codepoint::general_category::Pc
        || cat == una::codepoint::general_category::Cf;
}

} // namespace ignite::detail


