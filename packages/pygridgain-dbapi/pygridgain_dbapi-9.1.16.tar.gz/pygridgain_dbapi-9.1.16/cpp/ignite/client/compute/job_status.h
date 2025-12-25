/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

namespace ignite {

/**
 * Compute job status.
 */
enum class job_status {
    /// The job is submitted and waiting for an execution start.
    QUEUED,

    /// The job is being executed.
    EXECUTING,

    /// The job was unexpectedly terminated during execution.
    FAILED,

    /// The job was executed successfully and the execution result was returned.
    COMPLETED,

    /// The job has received the cancel command, but is still running.
    CANCELING,

    /// The job was successfully cancelled.
    CANCELED
};

} // namespace ignite
