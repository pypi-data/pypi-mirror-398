/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite_result.h"

#include <condition_variable>
#include <functional>
#include <memory>
#include <mutex>
#include <queue>
#include <thread>

namespace ignite::detail {

/**
 * Thread-based timer.
 */
class thread_timer final {
    /**
     * Timed event.
     */
    struct timed_event {
        /** Trigger time. */
        std::chrono::steady_clock::time_point timestamp;

        /** Callback to call. */
        std::function<void()> callback;

        /**
         * Constructor.
         */
        timed_event() = default;

        /**
         * Constructor.
         */
        timed_event(std::chrono::steady_clock::time_point ts, std::function<void()> &&cb)
            : timestamp(ts)
            , callback(std::move(cb)) {}

        /**
         * Comparison operator for priority_queue.
         */
        bool operator>(const timed_event& other) const { return timestamp > other.timestamp; }
    };

public:
    /**
     * Destructor.
     */
    ~thread_timer();

    /**
     * Start.
     *
     * @param error_handler Error handler for the errors that can occur during the events handling.
     * @return A thread timer instance.
     */
    static std::shared_ptr<thread_timer> start(std::function<void(ignite_error&&)> error_handler);

    /**
     * Stop the thread.
     */
    void stop();

    /**
     * Add a new event.
     *
     * @param timeout Timeout.
     * @param callback Callback to call.
     */
    void add(std::chrono::milliseconds timeout, std::function<void()> callback);

private:
    /**
     * Constructor.
     */
    thread_timer() = default;

    /** The stop flag. */
    bool m_stopping{false};

    /** Thread. */
    std::thread m_thread;

    /** Mutex. */
    std::mutex m_mutex;

    /** Conditional variable. */
    std::condition_variable m_condition;

    /** Timed event. */
    std::priority_queue<timed_event, std::vector<timed_event>, std::greater<>> m_events;
};

} // namespace ignite::detail
