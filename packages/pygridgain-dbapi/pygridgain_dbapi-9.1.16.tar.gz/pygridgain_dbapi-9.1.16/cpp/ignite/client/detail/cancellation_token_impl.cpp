/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/detail/cancellation_token_impl.h"

#include <sstream>

namespace ignite
{

void cancellation_token_impl::set_cancellation_result(ignite_result<void> &&res) {
    std::lock_guard guard(m_mutex);
    m_result = std::move(res);
    for (auto &cb : m_callbacks) {
        cb(ignite_result<void>{*m_result});
    }
}

void cancellation_token_impl::cancel_async(ignite_callback<void> callback) {
    std::lock_guard guard(m_mutex);

    if (is_cancelled()) {
        if (m_result) {
            callback(ignite_result<void>{*m_result});
        } else {
            m_callbacks.push_back(std::move(callback));
        }
        return;
    }

    m_cancelled.store(true);
    m_callbacks.push_back(std::move(callback));

    if (m_actions.empty()) {
        m_result = ignite_result<void>{};
        for (auto &cb : m_callbacks) {
            cb(ignite_result<void>{*m_result});
        }
        return;
    }

    auto results = std::make_shared<std::vector<ignite_result<void>>>();
    auto results_mutex = std::make_shared<std::mutex>();
    auto action_callback =
        [self = shared_from_this(), results, results_mutex, expected_results = m_actions.size()]
        (ignite_result<void> res) {
            std::lock_guard guard(*results_mutex);
            results->push_back(std::move(res));

            if (results->size() == expected_results) {
                // We've received all results and need to report it now to all the callbacks.
                bool error_found{false};
                error::code err_code{error::code::INTERNAL};
                std::stringstream msg_builder;
                for (auto &result : *results) {
                    if (!result.has_error()) {
                        continue;
                    }

                    if (!error_found) {
                        err_code = result.error().get_status_code();
                        msg_builder << "One or more cancel actions failed: " << result.error().what_str();
                        error_found = true;
                        continue;
                    }

                    msg_builder << ", " << result.error().what_str();
                }

                // It's actually OK to hold lock on results_mutex mutex here even if we don't need it anymore as the
                // last callback is this one, and no one is going to access results or wait on mutex anyway.

                if (error_found) {
                    self->set_cancellation_result(ignite_error{err_code, msg_builder.str()});
                } else {
                    self->set_cancellation_result({});
                }
            }
        };

    for (auto &action : m_actions) {
        action(action_callback);
    }
}

void cancellation_token_impl::add_action(std::shared_ptr<ignite_logger> logger,
    std::function<void(ignite_callback<void>)> action) {
    auto callback = [logger](ignite_result<void> res) {
        if (res.has_error()) {
            logger->log_warning(
                "Cancellation action that was added after the token was already canceled: " + res.error().what_str());
        }
    };

    if (is_cancelled()) {
        action(callback);
        return;
    }

    std::unique_lock lock(m_mutex);
    if (is_cancelled()) {
        lock.unlock();
        action(callback);
        return;
    }

    m_actions.push_back(std::move(action));
}

} // namespace ignite
