/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "thread_timer.h"

#include "ignite_result.h"

namespace ignite::detail {

thread_timer::~thread_timer() {
    stop();
}

std::shared_ptr<thread_timer> thread_timer::start(std::function<void(ignite_error&&)> error_handler) {
    std::shared_ptr<thread_timer> res{new thread_timer()};
    res->m_thread = std::thread([&self = *res, error_handler = std::move(error_handler)]() {
        std::unique_lock<std::mutex> lock(self.m_mutex);
        while (true) {
            if (self.m_stopping) {
                self.m_condition.notify_one();
                return;
            }

            if (self.m_events.empty()) {
                self.m_condition.wait(lock);
                continue;
            }

            auto nearest_event_ts = self.m_events.top().timestamp;
            auto now = std::chrono::steady_clock::now();
            if (nearest_event_ts < now) {
                auto func = self.m_events.top().callback;
                self.m_events.pop();

                lock.unlock();

                auto res = result_of_operation(func);
                if (res.has_error()) {
                    error_handler(res.error());
                }

                lock.lock();
            } else {
                self.m_condition.wait_until(lock, nearest_event_ts);
            }
        }
    });
    return res;
}

void thread_timer::stop() {
    {
        std::unique_lock<std::mutex> lock(m_mutex);
        if (m_stopping)
            return;

        m_stopping = true;
        m_condition.notify_one();
    }
    m_thread.join();
}

void thread_timer::add(std::chrono::milliseconds timeout, std::function<void()> callback) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_events.emplace(std::chrono::steady_clock::now() + timeout, std::move(callback));
    m_condition.notify_one();
}

} // namespace ignite::detail
