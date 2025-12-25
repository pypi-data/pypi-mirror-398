/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/odbc/ssl_mode.h"
#include "ignite/odbc/config/config_tools.h"

/** A string token for ssl_mode::DISABLE. */
const std::string DISABLE_TOKEN{"disable"};

/** A string token for ssl_mode::REQUIRE. */
const std::string REQUIRE_TOKEN{"require"};

/** A string token for ssl_mode::UNKNOWN. */
const std::string UNKNOWN_TOKEN{"unknown"};

namespace ignite {

ssl_mode_t ssl_mode_from_string(const std::string &val, ssl_mode_t dflt) {
    std::string lower_val = normalize_argument_string(val);

    if (lower_val == DISABLE_TOKEN)
        return ssl_mode_t::DISABLE;

    if (lower_val == REQUIRE_TOKEN)
        return ssl_mode_t::REQUIRE;

    return dflt;
}

std::string to_string(ssl_mode_t val) {
    switch (val) {
        case ssl_mode_t::DISABLE:
            return DISABLE_TOKEN;

        case ssl_mode_t::REQUIRE:
            return REQUIRE_TOKEN;

        case ssl_mode_t::UNKNOWN:
        default:
            return UNKNOWN_TOKEN;
    }
}

} // namespace ignite
