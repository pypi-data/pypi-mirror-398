/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "uuid.h"

#include <random>
#include <mutex>

namespace ignite {

uuid uuid::random() {
    static std::mutex random_mutex;
    static std::random_device rd;
    static std::mt19937 gen(rd());

    std::uniform_int_distribution<int64_t> distrib;

    std::lock_guard<std::mutex> lock(random_mutex);

    return {distrib(gen), distrib(gen)};
}

} // namespace ignite
