/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/detail/compute/job_execution_impl.h"
#include "ignite/client/detail/compute/compute_impl.h"

namespace ignite::detail {

void job_execution_impl::get_result_async(ignite_callback<std::optional<binary_object>> callback) {
    std::unique_lock<std::mutex> guard(m_mutex);

    if (m_result) {
        auto copy{*m_result};
        guard.unlock();

        callback({std::move(copy)});
    } else if (m_error) {
        auto copy{*m_error};
        guard.unlock();

        callback({std::move(copy)});
    } else {
        if (m_result_callback)
            throw ignite_error("A callback for this result was already submitted");

        m_result_callback = std::make_shared<ignite_callback<std::optional<binary_object>>>(std::move(callback));
    }
}

void job_execution_impl::set_result(std::optional<primitive> result) {
    std::optional<binary_object> obj;
    if (result) {
        obj = binary_object{std::move(*result)};
    }

    std::unique_lock<std::mutex> guard(m_mutex);

    m_result = obj;
    auto callback = std::move(m_result_callback);
    m_result_callback.reset();

    guard.unlock();

    if (callback) {
        (*callback)({std::move(obj)});
    }
}

void job_execution_impl::get_state_async(ignite_callback<std::optional<job_state>> callback) {
    std::unique_lock<std::mutex> guard(m_mutex);

    if (m_final_state) {
        auto copy{m_final_state};
        guard.unlock();

        callback({std::move(copy)});
    } else {
        m_compute->get_state_async(m_id, std::move(callback));
    }
}

void job_execution_impl::set_final_state(const job_state &status) {
    std::lock_guard<std::mutex> guard(m_mutex);

    m_final_state = status;
}

void job_execution_impl::set_error(ignite_error error) {
    std::unique_lock<std::mutex> guard(m_mutex);

    m_error = error;
    auto callback = std::move(m_result_callback);
    m_result_callback.reset();

    guard.unlock();

    if (callback) {
        (*callback)({std::move(error)});
    }
}

void job_execution_impl::cancel_async(ignite_callback<job_execution::operation_result> callback) {
    bool status_set;
    {
        std::lock_guard<std::mutex> guard(m_mutex);
        status_set = m_final_state.has_value();
    }

    if (status_set) {
        callback(job_execution::operation_result::INVALID_STATE);

        return;
    }

    m_compute->cancel_async(m_id, std::move(callback));
}

void job_execution_impl::change_priority_async(
    std::int32_t priority, ignite_callback<job_execution::operation_result> callback) {
    bool status_set;
    {
        std::lock_guard<std::mutex> guard(m_mutex);
        status_set = m_final_state.has_value();
    }

    if (status_set) {
        callback(job_execution::operation_result::INVALID_STATE);

        return;
    }

    m_compute->change_priority_async(m_id, priority, std::move(callback));
}

} // namespace ignite::detail
