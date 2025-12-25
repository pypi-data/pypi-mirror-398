/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/compute/job_status.h"
#include "ignite/common/ignite_timestamp.h"
#include "ignite/common/uuid.h"

#include <optional>

namespace ignite {

/**
 * @brief Compute job state.
 */
struct job_state {
    /// Job ID.
    uuid id{};

    /// Status.
    job_status status{job_status::QUEUED};

    /// Create time.
    ignite_timestamp create_time{};

    /// Start time (@c std::nullopt when not yet started).
    std::optional<ignite_timestamp> start_time{};

    /// Finish time (@c std::nullopt when not yet finished).
    std::optional<ignite_timestamp> finish_time{};
};

} // namespace ignite
