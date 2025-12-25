/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite_error.h"

#include <string_view>

#include <cctype>
#include <locale>

namespace ignite::detail {

namespace name_utils_constant {
/** Separator character between schema and object names. */
constexpr char SEPARATOR_CHAR = '.';

/** Quote character for identifiers. */
constexpr char QUOTE_CHAR = '"';

} // name_utils_constant

/**
 * Quote string.
 *
 * @param str A string to quote.
 * @param quote_char Quote character.
 * @return Quoted string.
 */
[[nodiscard]] std::string quote(std::string_view &str, char quote_char);

/**
 * Wraps the given name with double quotes if it is not uppercased non-quoted name,
 * e.g. "myColumn" -> "\"myColumn\"", "MYCOLUMN" -> "MYCOLUMN".
 *
 * @param name Name.
 * @param quote_char Quote character.
 * @return Quoted name.
 */
[[nodiscard]] std::string quote_if_needed(std::string_view name, char quote_char);

/**
 * Gets a fully qualified name in canonical form, that is, enclosing each part of the identifier chain in double
 * quotes if necessary.
 *
 * @param schema_name Schema name.
 * @param object_name Object name.
 * @param quote_char Quote character.
 * @param separator_char Separator character.
 * @return A fully qualified name in canonical form.
 */
[[nodiscard]] std::string to_canonical_name(std::string_view schema_name, std::string_view object_name,
    char quote_char, char separator_char);

/**
 * Unquotes the specified identifier, or converts it to upper case if it is not quoted.
 *
 * @param identifier Identifier.
 * @param quote_char Quote character.
 * @return Unquoted or uppercased identifier
 */
[[nodiscard]] std::string unquote(std::string_view &identifier, char quote_char);

/**
 * Parses the specified identifier.
 *
 * @param identifier Identifier
 * @param quote_char Quote character.
 * @param separator_char Separator character.
 * @return Parsed identifier.
 */
[[nodiscard]] std::string parse_identifier(std::string_view identifier, char quote_char, char separator_char);

/**
 * Check whether the char is an identifier extend is U+00B7, or any character in the Unicode General Category classes
 * "Mn", "Mc", "Nd", "Pc", or "Cf".
 *
 * @param codepoint Char to check.
 * @return @c true if the char is an identifier extend.
 */
[[nodiscard]] bool is_identifier_extend(char32_t codepoint);

/**
 * Check if the character is the identifier start.
 *
 * @param codepoint First codepoint.
 * @return @c true, if the character can be the first char of the identifier.
 */
inline bool is_identifier_start(char32_t codepoint) {
    return codepoint < 256 && (std::isalpha(codepoint) || codepoint == '_');
}

/**
 * Check if the character is the identifier start.
 *
 * @param codepoint First codepoint.
 * @return @c true, if the character can be the first char of the identifier.
 */
inline bool is_normalized_identifier_start(char32_t codepoint) {
    return codepoint < 256 && (std::isupper(codepoint) || codepoint == '_');
}

/**
 * Find a separator in the sequence.
 * @tparam Iterator Iterator type.
 * @param name The name.
 * @param begin Beginning iterator.
 * @param end Ending iterator.
 * @param quote_char Quote character.
 * @param separator_char Separator character.
 * @return
 */
template<typename Iterator>
Iterator find_separator(std::string_view name, Iterator begin, Iterator end, char32_t quote_char, char32_t separator_char) {
    if (begin == end)
        return end;

    auto it = begin;

    bool quoted = false;
    if (*it == quote_char) {
        quoted = true;
        ++it;
    }

    if (!quoted && !is_identifier_start(*it)) {
        throw ignite_error(error::code::ILLEGAL_ARGUMENT,
            "Invalid identifier start '" + std::to_string(*it) + "' : " + std::string(name)
            + ". Unquoted identifiers must begin with a letter or an underscore.");
    }

    auto next = std::next(it);
    for (; it != end; it = next, ++next) {
        auto codepoint = *it;

        if (codepoint == quote_char) {
            if (!quoted) {
                throw ignite_error(error::code::ILLEGAL_ARGUMENT,
                    "Identifier is not quoted, but contains quote character: '" + std::string(name) + "'");
            }

            // The end of quoted identifier
            if (next == end)
                return end;

            // We've found a separator
            if (*next == separator_char)
                return next;

            if (*next == quote_char) {
                ++next;
                continue;
            }

            throw ignite_error(error::code::ILLEGAL_ARGUMENT, "Unexpected character '" + std::to_string(*next)
                + "' after quote: '" + std::string(name) + "'");
        }

        if (codepoint == separator_char) {
            if (quoted)
                continue;

            return it;
        }

        if (!quoted && !is_identifier_start(codepoint) && !is_identifier_extend(codepoint)) {
            throw ignite_error(error::code::ILLEGAL_ARGUMENT, "Unexpected character '" + std::to_string(codepoint)
                + "' in unquoted identefier : '" + std::string(name) + "'");
        }
    }

    if (quoted) {
        throw ignite_error(error::code::ILLEGAL_ARGUMENT, "Missing closing quote: '" + std::string(name) + "'");
    }

    return end;
}

} // namespace ignite
