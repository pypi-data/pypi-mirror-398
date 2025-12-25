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
#include "ignite/client/compute/job_state.h"
#include "ignite/client/detail/cluster_connection.h"
#include "ignite/common/ignite_result.h"
#include "ignite/common/primitive.h"
#include "ignite/common/uuid.h"

namespace ignite::detail {

class compute_impl;

/**
 * Job control object, provides information about the job execution process and result, allows cancelling the job.
 */
class job_execution_impl {
public:
    // Default
    job_execution_impl() = default;

    /**
     * Constructor
     *
     * @param id Job ID.
     * @param node Cluster node.
     * @param compute Compute.
     */
    explicit job_execution_impl(uuid id, cluster_node node, std::shared_ptr<compute_impl> &&compute)
        : m_id(id)
        , m_node(std::move(node))
        , m_compute(compute) {}

    /**
     * Gets the job ID.
     *
     * @return Job ID.
     */
    [[nodiscard]] uuid get_id() const { return m_id; }

    /**
     * Gets the cluster node.
     *
     * @return Cluster node.
     */
    [[nodiscard]] const cluster_node &get_node() const { return m_node; }

    /**
     * Gets the job execution result asynchronously.
     *
     * Only one callback can be submitted for this operation at a time, which means you cannot call this method in
     * parallel.
     * @param callback Callback to be called when the operation is complete. Called with the job execution result.
     */
    void get_result_async(ignite_callback<std::optional<binary_object>> callback);

    /**
     * Set result.
     *
     * @param result Result.
     */
    void set_result(std::optional<primitive> result);

    /**
     * Gets the job execution state. Can be @c nullopt if the job state no longer exists due to exceeding the
     * retention time limit.
     *
     * @param callback Callback to be called when the operation is complete. Contains the job state. It Can be
     *  @c nullopt if the job state no longer exists due to exceeding the retention time limit.
     */
    void get_state_async(ignite_callback<std::optional<job_state>> callback);

    /**
     * Set final state.
     *
     * @param state Execution state.
     */
    void set_final_state(const job_state &state);

    /**
     * Set error.
     *
     * @param error Error.
     */
    void set_error(ignite_error error);

    /**
     * Cancels the job execution.
     *
     * @param callback Callback to be called when the operation is complete. Contains a cancel result.
     */
    void cancel_async(ignite_callback<job_execution::operation_result> callback);

    /**
     * Changes the job priority. After priority change, the job will be the last in the queue of jobs with the same
     * priority.
     *
     * @param priority New priority.
     * @param callback Callback to be called when the operation is complete. Contains an operation result.
     */
    void change_priority_async(std::int32_t priority, ignite_callback<job_execution::operation_result> callback);

private:
    /** Job ID. */
    const uuid m_id;

    /** Cluster node. */
    const cluster_node m_node;

    /** Compute. */
    std::shared_ptr<compute_impl> m_compute;

    /** Mutex. Should be held to change any data. */
    std::mutex m_mutex;

    /** Final state. */
    std::optional<job_state> m_final_state;

    /** Execution result. First optional to understand if the result is available. */
    std::optional<std::optional<binary_object>> m_result;

    /** Error. */
    std::optional<ignite_error> m_error;

    /** Result callback. */
    std::shared_ptr<ignite_callback<std::optional<binary_object>>> m_result_callback;
};

} // namespace ignite::detail
