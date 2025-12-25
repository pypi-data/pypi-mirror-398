/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <cstdint>

namespace ignite::protocol {

/**
 * Extension types.
 */
enum class extension_type : std::int8_t {
    NUMBER = 1,

    DECIMAL = 2,

    UUID = 3,

    DATE = 4,

    TIME = 5,

    DATE_TIME = 6,

    TIMESTAMP = 7,

    BITMASK = 8,

    NO_VALUE = 10
};

} // namespace ignite::protocol
