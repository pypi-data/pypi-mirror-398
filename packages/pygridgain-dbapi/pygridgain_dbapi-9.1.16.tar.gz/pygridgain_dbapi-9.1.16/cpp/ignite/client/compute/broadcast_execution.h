/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/compute/job_execution.h"
#include "ignite/common/ignite_result.h"

#include <vector>

namespace ignite {

/**
 * @brief Provides context related to broadcast compute.
 *
 * Broadcast execution control object, provides information about the broadcast execution process and result.
 */
class broadcast_execution {
public:
    // Default
    broadcast_execution() = default;

    /**
     * Constructor.
     *
     * @param executions Executions.
     */
    explicit broadcast_execution(std::vector<ignite_result<job_execution>> &&executions)
        : m_executions(std::move(executions)) {}

    /**
     * Gets the job executions.
     *
     * @return Job executions.
     */
    [[nodiscard]] const std::vector<ignite_result<job_execution>> &get_job_executions() const {
        return m_executions;
    }

private:
    /** Executions. */
    std::vector<ignite_result<job_execution>> m_executions;
};

} // namespace ignite
