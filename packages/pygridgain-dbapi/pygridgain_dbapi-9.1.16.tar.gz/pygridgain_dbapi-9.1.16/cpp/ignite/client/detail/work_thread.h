/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/detail/blocking_queue.h"
#include "ignite/common/ignite_error.h"

#include <functional>
#include <memory>
#include <thread>

namespace ignite::detail {

/**
 * A basic work thread concept that executes jobs it's given in a sequential order.
 *
 * @warning The class is not a thread safe. The methods of this class should not be called concurrently from multiple
 *      threads.
 */
class work_thread {
public:
    /** Job type. */
    typedef std::function<void()> job_type;

    // Default
    work_thread() = default;

    /**
     * Constructor.
     *
     * @param logger Logger.
     */
    explicit work_thread(std::shared_ptr<ignite_logger> logger)
        : m_logger(std::move(logger)) {}

    /**
     * Add a new job to the queue.
     *
     * @param job Job.
     */
    void add_job(job_type &&job) {
        if (m_stopped.load())
            throw ignite_error("Thread is already stopped");

        m_job_queue.push(std::move(job));
    }

    /**
     * Stop the thread.
     *
     * No new jobs should be added to the thread after the job was stopped.
     */
    void stop() {
        if (!m_stopped.load()) {
            m_stopped.store(true);
            m_job_queue.push([]() {});
        }
    }

    /**
     * Join the thread.
     *
     * Should not be called concurrently.
     */
    void join() {
        if (m_thread.joinable())
            m_thread.join();
    }

private:
    /** Logger. */
    std::shared_ptr<ignite_logger> m_logger;

    /** Stop flag. */
    std::atomic_bool m_stopped{false};

    /** Blocking queue. */
    blocking_queue<job_type> m_job_queue;

    /** Thread. */
    std::thread m_thread{[this]() {
        while (!m_stopped.load()) {
            auto job = m_job_queue.pop();
            try {
                job();
            } catch (const std::exception &err) {
                if (m_logger)
                    m_logger->log_warning(std::string("Exception caught while executing a job: ") + err.what());
            } catch (...) {
                if (m_logger)
                    m_logger->log_warning(std::string("Unknown exception caught while executing a job"));
            }
        }
        // Clear the job queue to prevent memory leaks.
        m_job_queue.clear();
    }};
};

} // namespace ignite::detail
