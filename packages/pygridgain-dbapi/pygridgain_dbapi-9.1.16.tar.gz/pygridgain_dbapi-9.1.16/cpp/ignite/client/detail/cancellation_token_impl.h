/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/ignite_result.h"
#include "ignite/client/cancellation_token.h"

#include <optional>
#include <mutex>
#include <vector>
#include <functional>
#include <ignite/client/ignite_logger.h>

namespace ignite
{

/**
 * @brief Implementation for cancellation token.
 *
 * Implementation of @ref ignite::cancellation_token.
 */
class cancellation_token_impl : public cancellation_token, public std::enable_shared_from_this<cancellation_token_impl>
{
public:
    /**
     * Destructor.
     */
    ~cancellation_token_impl() override = default;

    /**
     * Abruptly terminates an execution of an associated process.
     *
     * @param callback A callback that will be called after the process has been terminated and the resources associated
     *                 with that process have been freed.
     */
    void cancel_async(ignite_callback<void> callback);

    /**
     * Adds an action to perform on cancellation.
     *
     * @param logger Logger to use if the operation was already canceled.
     * @param action An action to perform on cancellation.
     */
    void add_action(std::shared_ptr<ignite_logger> logger, std::function<void(ignite_callback<void>)> action);

    /**
     * Flag indicating whether cancellation was requested or not.
     *
     * This method will return true even if cancellation has not been completed yet.
     *
     * @return @c true if the cancellation was requested.
     */
    bool is_cancelled() const { return m_cancelled.load(); }

private:
    /**
     * Set cancellation result.
     * @param res Result to set.
     */
    void set_cancellation_result(ignite_result<void> &&res);

    /** Mutex. */
    std::mutex m_mutex{};

    /** Cancel flag. */
    std::atomic<bool> m_cancelled{false};

    /** Result. */
    std::optional<ignite_result<void>> m_result{std::nullopt};

    /** Callbacks. */
    std::vector<ignite_callback<void>> m_callbacks{};

    /** Actions to take on cancel. */
    std::vector<std::function<void(ignite_callback<void>)>> m_actions{};
};

} // namespace ignite
