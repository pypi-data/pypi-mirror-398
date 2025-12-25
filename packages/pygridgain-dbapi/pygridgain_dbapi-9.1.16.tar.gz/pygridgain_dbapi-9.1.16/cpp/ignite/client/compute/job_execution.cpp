/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/compute/job_execution.h"
#include "ignite/client/detail/compute/job_execution_impl.h"

namespace ignite {

uuid job_execution::get_id() const {
    return m_impl->get_id();
}

const cluster_node &job_execution::get_node() const {
    return m_impl->get_node();
}

void job_execution::get_state_async(ignite_callback<std::optional<job_state>> callback) {
    m_impl->get_state_async(std::move(callback));
}

void job_execution::get_result_async(ignite_callback<std::optional<binary_object>> callback) {
    m_impl->get_result_async(std::move(callback));
}

void job_execution::cancel_async(ignite_callback<job_execution::operation_result> callback) {
    m_impl->cancel_async(std::move(callback));
}

void job_execution::change_priority_async(
    std::int32_t priority, ignite_callback<job_execution::operation_result> callback) {
    m_impl->change_priority_async(priority, std::move(callback));
}

} // namespace ignite
