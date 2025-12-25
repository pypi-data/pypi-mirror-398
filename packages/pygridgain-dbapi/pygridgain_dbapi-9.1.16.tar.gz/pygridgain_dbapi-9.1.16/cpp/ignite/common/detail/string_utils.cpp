/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "string_utils.h"

#include <algorithm>

namespace ignite::detail {

end_point parse_single_address(std::string_view value, std::uint16_t default_port) {
    auto colon_num = std::count(value.begin(), value.end(), ':');

    if (colon_num == 0)
        return {std::string(value), default_port};

    if (colon_num != 1) {
        throw ignite_error("Unexpected number of ':' characters in the following address: '" + std::string(value));
    }

    auto colon_pos = value.find(':');
    auto host = value.substr(0, colon_pos);

    if (colon_pos == value.size() - 1) {
        throw ignite_error("Port is missing in the following address: '" + std::string(value));
    }

    auto port_str = value.substr(colon_pos + 1);
    auto port = parse_port(port_str);

    return {std::string(host), port};
}

std::optional<std::int64_t> parse_int64(std::string_view value) {
    auto value_str = trim(value);
    if (!std::all_of(value_str.begin(), value_str.end(), [](char c) { return std::isdigit(c) || c == '-'; }))
        return std::nullopt;
    return lexical_cast<std::int64_t>(value_str);
}

std::uint16_t parse_port(std::string_view value) {
    auto port_opt = parse_int<std::uint16_t>(value);
    if (!port_opt || *port_opt == 0) {
        throw ignite_error("Invalid port value: " + std::string(value));
    }
    return *port_opt;
}

} // namespace ignite
