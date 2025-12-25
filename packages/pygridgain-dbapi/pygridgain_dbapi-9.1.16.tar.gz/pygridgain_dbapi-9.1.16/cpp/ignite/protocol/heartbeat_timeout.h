/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/common/detail/duration_min_max.h>

#include <cassert>
#include <chrono>

namespace ignite {

inline std::chrono::milliseconds calculate_heartbeat_interval(std::chrono::milliseconds config_value,
    std::chrono::milliseconds idle_timeout) {
    static const std::chrono::milliseconds MIN_HEARTBEAT_INTERVAL = std::chrono::milliseconds(500);

    if (config_value.count()) {
        assert(config_value.count() > 0);

        config_value = min(idle_timeout / 3, config_value);
        config_value = max(MIN_HEARTBEAT_INTERVAL, config_value);
    }

    return config_value;
}

} // namespace ignite
