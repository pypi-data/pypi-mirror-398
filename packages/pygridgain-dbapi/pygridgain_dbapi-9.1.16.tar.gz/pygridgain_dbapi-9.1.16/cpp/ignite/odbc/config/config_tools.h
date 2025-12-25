/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/end_point.h"

#include <map>
#include <string>
#include <vector>

namespace ignite {

/**
 * Convert the address list to string.
 *
 * @param addresses Addresses.
 * @return Resulting string.
 */
[[nodiscard]] std::string addresses_to_string(const std::vector<end_point> &addresses);

/**
 * Parse address.
 *
 * @throw odbc_error on error.
 * @param value String value to parse.
 * @return End points list.
 */
[[nodiscard]] std::vector<end_point> parse_address(std::string_view value);

/** Configuration options map */
typedef std::map<std::string, std::string> config_map;

/**
 * Parse connection string into a map containing configuration attributes.
 *
 * @param str Connection string.
 * @return A map containing configuration attributes.
 */
[[nodiscard]] config_map parse_connection_string(std::string_view str);

/**
 * Parse DSN configuration string into a map containing configuration attributes.
 *
 * @param str DSN string. Must be terminated with two subsequent '\0'.
 * @return A map containing configuration attributes.
 */
[[nodiscard]] config_map parse_config_attributes(const char *str);

/**
 * Normalize argument string, i.e. strip leading and trailing whitespaces and convert to lowercase.
 *
 * @param value Value.
 * @return Normalized string.
 */
[[nodiscard]] std::string normalize_argument_string(std::string_view value);

} // namespace ignite
