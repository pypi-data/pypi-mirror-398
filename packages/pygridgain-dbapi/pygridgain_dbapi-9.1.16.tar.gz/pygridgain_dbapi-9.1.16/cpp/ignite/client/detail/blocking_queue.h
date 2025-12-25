/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <condition_variable>
#include <deque>
#include <mutex>

namespace ignite::detail {

/**
 * A basic blocking queue implementation. Blocks when the queue is empty, until a new value is pushed into it.
 * @note Currently, only necessary methods were implemented. Feel free to add other id needed.
 */
template<typename T>
class blocking_queue {
public:
    /** Value type. */
    typedef T value_type;

    // Default
    blocking_queue() = default;

    /**
     * Push value to the back of the queue.
     *
     * @param value Value.
     */
    void push(const value_type &value) {
        std::lock_guard<std::mutex> guard(m_job_queue_mutex);
        m_impl.push_back(value);
        m_job_queue_cond.notify_one();
    }

    /**
     * Push value to the back of the queue.
     *
     * @param value Value.
     */
    void push(value_type &&value) {
        std::lock_guard<std::mutex> guard(m_job_queue_mutex);
        m_impl.push_back(std::move(value));
        m_job_queue_cond.notify_one();
    }

    /**
     * Pull a value out of a queue.
     * Blocks if there is no values in the queue.
     *
     * @return The value from the front of the queue.
     */
    value_type pop() {
        std::unique_lock<std::mutex> guard(m_job_queue_mutex);
        while (m_impl.empty())
            m_job_queue_cond.wait(guard);

        auto value = std::move(m_impl.front());
        m_impl.pop_front();
        return value;
    }

    /**
     * Clear the queue.
     */
    void clear() {
        std::unique_lock<std::mutex> guard(m_job_queue_mutex);
        m_impl.clear();
    }

private:
    /** Mutex. */
    std::mutex m_job_queue_mutex;

    /** Condition variable. */
    std::condition_variable m_job_queue_cond;

    /** Queue implementation. */
    std::deque<value_type> m_impl;
};

} // namespace ignite::detail
